"""Sprint 7 T718 — activity emit on schedule created."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.activity.emit import record_from_kafka_topic
from ipe_shared.events.producer import kafka_producer

logger = logging.getLogger(__name__)


async def emit_schedule_created_activity(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    mo_count: int,
    schedule: dict,
) -> None:
    envelope = kafka_producer.build_envelope(
        event_type="ipe.schedule.created",
        tenant_id=str(tenant_id),
        payload={
            "summary": (
                f"Schedule created for {mo_count} MO(s) "
                f"({schedule.get('solver_status', 'UNKNOWN')})"
            ),
            "mo_count": mo_count,
            "solver_status": schedule.get("solver_status", "UNKNOWN"),
            "operation_count": len(schedule.get("assignments", [])),
        },
    )
    try:
        await record_from_kafka_topic(
            session,
            "ipe.schedule.created",
            envelope,
            tenant_id=str(tenant_id),
        )
    except Exception:
        logger.exception("Failed to record schedule activity for tenant %s", tenant_id)
