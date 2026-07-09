"""Activity event persistence (Sprint 7 activity store)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.activity_event import ActivityEvent


async def record_activity_event(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    source_tool: str,
    event_type: str,
    summary: str,
    actor_id: str | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    metadata: dict | None = None,
    severity: str = "info",
    occurred_at: datetime | None = None,
    idempotency_key: str | None = None,
) -> ActivityEvent:
    """Insert activity event; skip duplicate idempotency keys."""
    values = {
        "tenant_id": tenant_id,
        "source_tool": source_tool,
        "event_type": event_type,
        "actor_id": actor_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "summary": summary,
        "metadata_": metadata or {},
        "severity": severity,
        "occurred_at": occurred_at or datetime.now(UTC),
        "idempotency_key": idempotency_key,
    }
    if idempotency_key:
        existing = await session.execute(
            select(ActivityEvent).where(
                ActivityEvent.tenant_id == tenant_id,
                ActivityEvent.idempotency_key == idempotency_key,
            )
        )
        found = existing.scalar_one_or_none()
        if found:
            return found

    event = ActivityEvent(**values)
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def list_activity_feed(
    session: AsyncSession,
    tenant_id: UUID,
    *,
    source_tool: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ActivityEvent]:
    stmt = (
        select(ActivityEvent)
        .where(ActivityEvent.tenant_id == tenant_id)
        .order_by(ActivityEvent.occurred_at.desc())
        .limit(min(limit, 200))
        .offset(offset)
    )
    if source_tool:
        stmt = stmt.where(ActivityEvent.source_tool == source_tool)
    result = await session.execute(stmt)
    return list(result.scalars().all())
