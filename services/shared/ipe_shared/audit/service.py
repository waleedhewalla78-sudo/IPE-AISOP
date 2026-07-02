"""Async audit logging service.

Writes to the append-only cdm_audit_log table using background tasks
to avoid blocking API responses.

Immutability enforcement (P9-006):
- RLS policy ``audit_tenant_isolation`` restricts rows to the current tenant.
- Role ``ipe_audit_writer`` holds INSERT + SELECT only (no UPDATE, no DELETE).
- ``REVOKE UPDATE, DELETE ON cdm_audit_log FROM PUBLIC`` (and all non-superuser
  roles) prevents accidental modification.
- Trigger ``trg_prevent_audit_modification`` raises an exception on any UPDATE or
  DELETE attempt, providing a last-resort guard at the database level.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from ipe_shared.config import settings
from ipe_shared.database.connection import get_engine

logger = logging.getLogger(__name__)


async def log_audit_event(
    tenant_id: UUID | str,
    actor_type: str,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: UUID | str,
    before_state: dict | None = None,
    after_state: dict | None = None,
    rationale: str | None = None,
) -> None:
    """Write an audit log entry (non-blocking, fire-and-forget).

    Args:
        tenant_id: Tenant UUID.
        actor_type: "user" or "system".
        actor_id: User ID or system identifier.
        action: Action code (e.g., APPROVE_SCHEDULE, RUN_SCENARIO, COST_OPTIMIZE).
        entity_type: Entity type (e.g., "manufacturing_order", "scenario", "copilot_query").
        entity_id: Entity UUID.
        before_state: State before the action (JSON-serializable dict).
        after_state: State after the action (JSON-serializable dict).
        rationale: Human-readable rationale for the action.
    """
    try:
        engine = get_engine()
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            await session.execute(
                text("""
                    INSERT INTO cdm_audit_log
                        (tenant_id, actor_type, actor_id, action, entity_type, entity_id,
                         before_state, after_state, rationale, timestamp)
                    VALUES
                        (:tenant_id, :actor_type, :actor_id, :action, :entity_type, :entity_id,
                         :before_state, :after_state, :rationale, :timestamp)
                """),
                {
                    "tenant_id": UUID(str(tenant_id)) if isinstance(tenant_id, str) else tenant_id,
                    "actor_type": actor_type,
                    "actor_id": str(actor_id),
                    "action": action,
                    "entity_type": entity_type,
                    "entity_id": UUID(str(entity_id)) if isinstance(entity_id, str) else entity_id,
                    "before_state": before_state,
                    "after_state": after_state,
                    "rationale": rationale,
                    "timestamp": datetime.now(timezone.utc),
                },
            )
            await session.commit()
    except Exception as e:
        logger.error("Failed to write audit log: action=%s entity=%s error=%s", action, entity_id, e)

    if settings.AUDIT_KAFKA_ENABLED:
        try:
            from ipe_shared.audit.kafka_publisher import publish_audit_event

            await publish_audit_event(
                tenant_id=str(tenant_id),
                actor_type=actor_type,
                actor_id=str(actor_id),
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id),
                before_state=before_state,
                after_state=after_state,
                rationale=rationale,
            )
        except Exception as exc:
            logger.debug("Kafka audit fan-out skipped: %s", exc)


def create_audit_writer(
    tenant_id: UUID | str,
    actor_type: str,
    actor_id: str,
):
    """Create a context helper for audit logging.

    Returns a callable that can be used to log events:
        writer = create_audit_writer(tenant_id, "user", str(user_id))
        await writer("APPROVE_SCHEDULE", "mo", mo_id, before=..., after=..., rationale=...)
    """
    async def _write(
        action: str,
        entity_type: str,
        entity_id: UUID | str,
        before_state: dict | None = None,
        after_state: dict | None = None,
        rationale: str | None = None,
    ) -> None:
        await log_audit_event(
            tenant_id=tenant_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_state=before_state,
            after_state=after_state,
            rationale=rationale,
        )

    return _write


async def validate_audit_immutability() -> dict[str, Any]:
    """Verify that the audit log immutability trigger exists.

    Queries ``pg_trigger`` to confirm ``trg_prevent_audit_modification`` is
    installed on ``cdm_audit_log`` and returns a validation result dict.
    """
    try:
        engine = get_engine()
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            result = await session.execute(
                text(
                    "SELECT tgname FROM pg_trigger "
                    "WHERE tgrelid = 'cdm_audit_log'::regclass "
                    "AND tgname = 'trg_prevent_audit_modification'"
                ),
            )
            row = result.scalar_one_or_none()
            if row:
                logger.info("Audit immutability trigger verified: %s", row)
                return {"valid": True, "trigger": row}
            logger.warning("Audit immutability trigger NOT found on cdm_audit_log")
            return {"valid": False, "trigger": None}
    except Exception as e:
        logger.error("Failed to validate audit immutability: %s", e)
        return {"valid": False, "trigger": None, "error": str(e)}
