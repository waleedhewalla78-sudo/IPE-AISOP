"""Andon dual-write helpers — persist in-memory alerts to cdm_andon_alert."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.andon_alert import AndonAlert


def _parse_tenant(tenant_id: str) -> UUID | None:
    try:
        return UUID(str(tenant_id))
    except Exception:
        return None


def _parse_triggered(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(UTC)


async def persist_andon_alert(
    session: AsyncSession,
    *,
    tenant_id: str,
    alert: dict[str, Any],
) -> bool:
    """Best-effort insert of an Andon alert. Returns True if queued on session."""
    tid = _parse_tenant(tenant_id)
    if tid is None:
        return False
    row = AndonAlert(
        tenant_id=tid,
        alert_ref=str(alert.get("id") or "")[:40],
        color=str(alert.get("color") or "white"),
        work_centre=alert.get("work_centre"),
        reported_by=alert.get("reported_by"),
        message=alert.get("message"),
        impact=alert.get("impact"),
        status=str(alert.get("status") or "active"),
        response_minutes=alert.get("response_minutes"),
        escalate_after_minutes=alert.get("escalate_after_minutes"),
        resolution=alert.get("resolution"),
        triggered_at=_parse_triggered(alert.get("triggered_at")),
        resolved_at=_parse_triggered(alert.get("resolved_at")),
    )
    session.add(row)
    try:
        await session.commit()
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass
        return False
    return True


async def persist_andon_resolve(
    session: AsyncSession,
    *,
    tenant_id: str,
    alert_ref: str,
    resolution: str,
) -> bool:
    tid = _parse_tenant(tenant_id)
    if tid is None:
        return False
    now = datetime.now(UTC)
    try:
        await session.execute(
            update(AndonAlert)
            .where(AndonAlert.tenant_id == tid, AndonAlert.alert_ref == alert_ref)
            .values(status="resolved", resolution=resolution, resolved_at=now)
        )
        await session.commit()
    except Exception:
        try:
            await session.rollback()
        except Exception:
            pass
        return False
    return True


async def load_andon_alerts(
    session: AsyncSession,
    *,
    tenant_id: str,
    status: str | None = None,
) -> list[dict[str, Any]]:
    tid = _parse_tenant(tenant_id)
    if tid is None:
        return []
    try:
        stmt = select(AndonAlert).where(AndonAlert.tenant_id == tid)
        if status:
            stmt = stmt.where(AndonAlert.status == status)
        result = await session.execute(stmt)
        rows = result.scalars().all()
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "id": r.alert_ref or str(r.id),
                "color": r.color,
                "work_centre": r.work_centre,
                "reported_by": r.reported_by,
                "message": r.message,
                "impact": r.impact,
                "status": r.status,
                "response_minutes": r.response_minutes,
                "escalate_after_minutes": r.escalate_after_minutes,
                "resolution": r.resolution,
                "triggered_at": r.triggered_at.isoformat() if r.triggered_at else None,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
                "persisted": True,
            }
        )
    return out
