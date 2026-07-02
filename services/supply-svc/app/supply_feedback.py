"""Publish supply network adjustment events for demand-svc feedback loop."""

from __future__ import annotations

import logging
from uuid import uuid4

from ipe_shared.events.producer import kafka_producer

logger = logging.getLogger(__name__)

SUPPLY_ADJUSTED_TOPIC = "ipe.supply.adjusted"


async def publish_supply_adjustment(
    *,
    tenant_id: str,
    product_id: str,
    base_value: float,
    capacity_utilization_pct: float,
    lead_time_days: float,
    facilities_count: int = 0,
) -> None:
    """Emit forecast adjustment hint after supply network read/update."""
    envelope = kafka_producer.build_envelope(
        event_type="ipe.supply.adjusted",
        tenant_id=tenant_id,
        payload={
            "tenant_id": tenant_id,
            "product_id": product_id,
            "base_value": base_value,
            "value": base_value,
            "capacity_utilization_pct": capacity_utilization_pct,
            "lead_time_days": lead_time_days,
            "facilities_count": facilities_count,
            "horizon_type": "short",
        },
    )
    try:
        await kafka_producer.send(
            SUPPLY_ADJUSTED_TOPIC,
            key=str(product_id),
            value=envelope,
        )
    except Exception as exc:
        logger.warning("Failed to publish %s: %s", SUPPLY_ADJUSTED_TOPIC, exc)
