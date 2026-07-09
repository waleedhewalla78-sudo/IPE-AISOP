"""Emit activity events from Kafka envelopes (Kafka-off / in-process path)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.activity.store import record_activity_event
from ipe_shared.events.eib import normalize_kafka_message


async def record_from_kafka_topic(
    session: AsyncSession,
    topic: str,
    envelope: dict,
    *,
    tenant_id: str | UUID | None = None,
) -> bool:
    """Normalize a Kafka envelope and persist to cdm_activity_event. Returns False if skipped."""
    normalized = normalize_kafka_message(topic, envelope, tenant_id=tenant_id)
    tid = normalized.get("tenant_id")
    if not tid:
        return False

    entity_uuid = None
    if normalized.get("entity_id"):
        try:
            entity_uuid = UUID(str(normalized["entity_id"]))
        except ValueError:
            entity_uuid = None

    await record_activity_event(
        session,
        tenant_id=UUID(str(tid)),
        source_tool=normalized["source_tool"],
        event_type=normalized["event_type"],
        summary=normalized["summary"],
        actor_id=normalized.get("actor_id"),
        entity_type=normalized.get("entity_type"),
        entity_id=entity_uuid,
        metadata=normalized.get("metadata"),
        severity=normalized.get("severity", "info"),
        occurred_at=normalized.get("occurred_at"),
        idempotency_key=normalized.get("idempotency_key"),
    )
    return True
