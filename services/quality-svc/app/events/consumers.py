from __future__ import annotations

import logging

from ipe_shared.events.consumer import KafkaConsumer
from ipe_shared.middleware.tenant_context import tenant_ctx

logger = logging.getLogger(__name__)


async def handle_feasibility_scored(event: dict) -> None:
    tenant_id = event.get("tenant_id")
    if tenant_id:
        tenant_ctx.set(tenant_id)
    payload = event.get("payload", {})
    mo_id = payload.get("mo_id", "unknown")
    feasibility_score = payload.get("feasibility_score", 0.0)
    gate_scores = payload.get("gate_scores", {})
    logger.info(
        "Processing ipe.mo.feasibility_scored event: mo_id=%s score=%.2f gates=%s",
        mo_id,
        feasibility_score,
        list(gate_scores.keys()),
    )


async def handle_quality_event_created(event: dict) -> None:
    tenant_id = event.get("tenant_id")
    if tenant_id:
        tenant_ctx.set(tenant_id)
    payload = event.get("payload", {})
    event_type = payload.get("type", "unknown")
    severity = payload.get("severity", "medium")
    product_id = payload.get("product_id", "unknown")
    logger.info(
        "Processing ipe.quality.event_created event: type=%s severity=%s product=%s",
        event_type,
        severity,
        product_id,
    )


def create_consumers() -> list[KafkaConsumer]:
    from ipe_shared.config import settings

    feasibility_consumer = KafkaConsumer(
        topic="ipe.mo.feasibility_scored",
        group_id="quality-svc",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        handler=handle_feasibility_scored,
    )

    quality_event_consumer = KafkaConsumer(
        topic="ipe.quality.event_created",
        group_id="quality-svc",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        handler=handle_quality_event_created,
    )

    return [feasibility_consumer, quality_event_consumer]


async def start_consumers() -> None:
    consumers = create_consumers()
    for consumer in consumers:
        try:
            await consumer.start()
            logger.info("Started consumer on topic: %s", consumer.topic)
        except Exception as e:
            logger.error("Failed to start consumer on topic %s: %s", consumer.topic, e)


async def stop_consumers() -> None:
    consumers = create_consumers()
    for consumer in consumers:
        try:
            await consumer.stop()
            logger.info("Stopped consumer on topic: %s", consumer.topic)
        except Exception as e:
            logger.error("Error stopping consumer on topic %s: %s", consumer.topic, e)