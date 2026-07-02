"""Persist copilot sessions in PostgreSQL (v8 Phase 1)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.v8_planning import CopilotSession


async def create_session(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: UUID,
    role: str,
    context: dict | None = None,
) -> CopilotSession:
    row = CopilotSession(
        tenant_id=tenant_id,
        user_id=user_id,
        role=role,
        context_jsonb=context or {},
    )
    session.add(row)
    await session.flush()
    return row


async def get_session_row(
    session: AsyncSession,
    *,
    tenant_id: str,
    session_id: UUID,
) -> CopilotSession | None:
    row = await session.get(CopilotSession, session_id)
    if not row or str(row.tenant_id) != tenant_id:
        return None
    return row


async def append_turn(
    session: AsyncSession,
    *,
    tenant_id: str,
    session_id: UUID,
    user_message: str,
    assistant_message: str,
    intent: str | None = None,
) -> CopilotSession | None:
    row = await get_session_row(session, tenant_id=tenant_id, session_id=session_id)
    if not row:
        return None
    history = list(row.context_jsonb.get("turns", []))
    history.append(
        {
            "at": datetime.now(UTC).isoformat(),
            "user": user_message[:2000],
            "assistant": assistant_message[:4000],
            "intent": intent,
        }
    )
    row.context_jsonb = {**row.context_jsonb, "turns": history[-20:]}
    row.updated_at = datetime.now(UTC)
    await session.flush()
    return row


async def latest_session_for_user(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: UUID,
) -> CopilotSession | None:
    result = await session.execute(
        select(CopilotSession)
        .where(CopilotSession.tenant_id == tenant_id, CopilotSession.user_id == user_id)
        .order_by(CopilotSession.updated_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
