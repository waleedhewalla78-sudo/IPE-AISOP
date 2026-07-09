"""EIB consumer — normalize Kafka events into activity store."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from ipe_shared.activity.store import record_activity_event
from ipe_shared.database.connection import get_engine
from ipe_shared.events.eib import normalize_kafka_message
from ipe_shared.middleware.tenant_context import tenant_ctx

logger = logging.getLogger(__name__)


async def handle_eib_activity(topic: str, message: dict) -> None:
    envelope = message if "payload" in message else {"payload": message, "tenant_id": tenant_ctx.get()}
    normalized = normalize_kafka_message(topic, envelope, tenant_id=tenant_ctx.get())
    tid = normalized.get("tenant_id")
    if not tid:
        logger.debug("EIB skip — no tenant_id for topic %s", topic)
        return

    entity_uuid = None
    if normalized.get("entity_id"):
        try:
            entity_uuid = UUID(str(normalized["entity_id"]))
        except ValueError:
            entity_uuid = None

    engine = get_engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, false)"),
            {"tid": str(tid)},
        )
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
