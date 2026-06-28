"""Kafka consumer: supply network adjustments → demand forecast rows."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.supply_feedback import (
    SUPPLY_ADJUSTED_TOPIC,
    adjust_forecast_for_supply,
    parse_supply_network_event,
)
from ipe_shared.events.consumer import KafkaConsumer
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.v8_planning import DemandForecast

logger = logging.getLogger(__name__)

_consumer_tasks: list[tuple[KafkaConsumer, asyncio.Task]] = []


async def handle_supply_adjustment(session: AsyncSession, payload: dict) -> None:
    """Persist supply-adjusted forecast row from Kafka message."""
    event = parse_supply_network_event(payload)
    tenant_id = event.get("tenant_id") or tenant_ctx.get()
    if not tenant_id:
        logger.warning("supply adjustment missing tenant_id — skipped")
        return

    product_id = payload.get("product_id")
    if not product_id:
        logger.warning("supply adjustment missing product_id — skipped")
        return

    base_value = float(payload.get("base_value", payload.get("value", 10.0)))
    adjusted, confidence = adjust_forecast_for_supply(
        base_value,
        capacity_utilization_pct=event["capacity_utilization_pct"],
        lead_time_days=event["lead_time_days"],
    )
    spread = max(base_value * 0.1, 1.0) * (1.0 - confidence)

    row = DemandForecast(
        tenant_id=UUID(str(tenant_id)),
        product_id=UUID(str(product_id)),
        horizon_type=str(payload.get("horizon_type", "short")),
        forecast_date=datetime.now(UTC),
        value=adjusted,
        lower_bound=max(0.0, adjusted - spread),
        upper_bound=adjusted + spread,
        model_version="supply_adjusted",
    )
    session.add(row)
    logger.info(
        "supply_adjusted forecast tenant=%s product=%s value=%.4f confidence=%.4f",
        tenant_id,
        product_id,
        adjusted,
        confidence,
    )


async def start_consumers() -> None:
    consumer = KafkaConsumer(
        topics=[SUPPLY_ADJUSTED_TOPIC],
        group_id="demand-feedback-group",
        handler=handle_supply_adjustment,
        service_name="demand-svc",
        use_session=True,
    )
    task = asyncio.create_task(consumer.start())
    _consumer_tasks.append((consumer, task))
    logger.info("Started supply feedback consumer on %s", SUPPLY_ADJUSTED_TOPIC)


async def stop_consumers() -> None:
    for consumer, task in _consumer_tasks:
        await consumer.stop()
        task.cancel()
    _consumer_tasks.clear()
