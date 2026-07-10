"""Multi-tenant operations dashboard API (Sprint S8)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.mdr_score import MdrScore
from ipe_shared.models.sync_run import SyncRun
from ipe_shared.models.tenant import Tenant
from ipe_shared.models.tenant_health import TenantHealth
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/ops", tags=["ops"])


def _derive_health_status(
    is_active: bool,
    sync_status: str,
    failed_sync_24h: int,
    mdr_passed: bool | None,
) -> str:
    if not is_active:
        return "inactive"
    if failed_sync_24h >= 3 or sync_status == "failed":
        return "critical"
    if sync_status in ("partial", "running") or (mdr_passed is False):
        return "degraded"
    return "healthy"


async def _build_tenant_health_row(session: AsyncSession, tenant: Tenant) -> dict:
    tid = tenant.id
    cutoff_24h = datetime.now(UTC) - timedelta(hours=24)

    sync_stmt = (
        select(SyncRun)
        .where(SyncRun.tenant_id == tid)
        .order_by(SyncRun.started_at.desc())
        .limit(1)
    )
    last_sync = (await session.execute(sync_stmt)).scalar_one_or_none()

    failed_count_stmt = select(func.count()).where(
        SyncRun.tenant_id == tid,
        SyncRun.status == "failed",
        SyncRun.started_at >= cutoff_24h,
    )
    failed_sync_24h = int((await session.execute(failed_count_stmt)).scalar() or 0)

    mdr_stmt = (
        select(MdrScore)
        .where(MdrScore.tenant_id == tid)
        .order_by(MdrScore.evaluated_at.desc())
        .limit(1)
    )
    mdr = (await session.execute(mdr_stmt)).scalar_one_or_none()
    mdr_passed = mdr.passed if mdr else None
    mdr_score = None
    if mdr:
        mdr_score = round(
            float(mdr.bom_completeness_pct + mdr.lead_time_accuracy_pct) / 2,
            1,
        )

    active_mo_stmt = select(func.count()).where(
        ManufacturingOrder.tenant_id == tid,
        ManufacturingOrder.status.in_(["planned", "in_progress", "released"]),
    )
    active_mos = int((await session.execute(active_mo_stmt)).scalar() or 0)

    sync_status = last_sync.status if last_sync else "unknown"
    health_status = _derive_health_status(
        bool(tenant.is_active),
        sync_status,
        failed_sync_24h,
        mdr_passed,
    )

    return {
        "tenant_id": str(tid),
        "tenant_name": tenant.name,
        "tier": tenant.tier,
        "erp_type": tenant.erp_type,
        "is_active": bool(tenant.is_active),
        "health_status": health_status,
        "sync_status": sync_status,
        "last_sync_at": last_sync.finished_at.isoformat() if last_sync and last_sync.finished_at else None,
        "failed_sync_count_24h": failed_sync_24h,
        "mdr_passed": mdr_passed,
        "mdr_score_pct": mdr_score,
        "active_mo_count": active_mos,
        "open_alert_count": failed_sync_24h,
    }


@router.get("/tenants/health")
async def list_tenant_health(
    refresh: bool = Query(False, description="Persist snapshot rows to cdm_tenant_health"),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin"])),
):
    """Platform admin view of all tenant health metrics."""
    tenants = (await session.execute(select(Tenant).order_by(Tenant.name))).scalars().all()
    rows = []
    for tenant in tenants:
        row = await _build_tenant_health_row(session, tenant)
        rows.append(row)
        if refresh:
            snapshot = TenantHealth(
                tenant_id=tenant.id,
                health_status=row["health_status"],
                sync_status=row["sync_status"],
                last_sync_at=datetime.fromisoformat(row["last_sync_at"]) if row["last_sync_at"] else None,
                failed_sync_count_24h=row["failed_sync_count_24h"],
                mdr_passed=row["mdr_passed"],
                mdr_score_pct=row["mdr_score_pct"],
                active_mo_count=row["active_mo_count"],
                open_alert_count=row["open_alert_count"],
            )
            session.add(snapshot)

    if refresh and rows:
        await session.commit()

    summary = {
        "total": len(rows),
        "healthy": sum(1 for r in rows if r["health_status"] == "healthy"),
        "degraded": sum(1 for r in rows if r["health_status"] == "degraded"),
        "critical": sum(1 for r in rows if r["health_status"] == "critical"),
        "inactive": sum(1 for r in rows if r["health_status"] == "inactive"),
    }

    return APIResponse(success=True, data={"summary": summary, "tenants": rows}, error=None)


@router.get("/tenants/alerts")
async def list_tenant_alerts(
    severity: str | None = Query(None, description="critical | warning | info"),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin"])),
):
    """Sync failures and degraded tenants for the ops dashboard."""
    cutoff_7d = datetime.now(UTC) - timedelta(days=7)
    failed_syncs = (
        await session.execute(
            select(SyncRun, Tenant.name)
            .join(Tenant, Tenant.id == SyncRun.tenant_id)
            .where(SyncRun.status == "failed", SyncRun.started_at >= cutoff_7d)
            .order_by(SyncRun.started_at.desc())
            .limit(limit)
        )
    ).all()

    alerts: list[dict] = []
    for sync_run, tenant_name in failed_syncs:
        sev = "critical" if sync_run.status == "failed" else "warning"
        if severity and sev != severity:
            continue
        alerts.append(
            {
                "alert_id": str(sync_run.id),
                "tenant_id": str(sync_run.tenant_id),
                "tenant_name": tenant_name,
                "severity": sev,
                "category": "sync_failure",
                "message": sync_run.error_summary or f"Sync {sync_run.source} failed",
                "occurred_at": sync_run.started_at.isoformat() if sync_run.started_at else None,
                "source": sync_run.source,
            }
        )

    tenants = (await session.execute(select(Tenant).where(Tenant.is_active.is_(True)))).scalars().all()
    for tenant in tenants:
        row = await _build_tenant_health_row(session, tenant)
        if row["health_status"] == "critical":
            sev = "critical"
        elif row["health_status"] == "degraded":
            sev = "warning"
        else:
            continue
        if severity and sev != severity:
            continue
        alerts.append(
            {
                "alert_id": f"health-{row['tenant_id']}",
                "tenant_id": row["tenant_id"],
                "tenant_name": row["tenant_name"],
                "severity": sev,
                "category": "tenant_health",
                "message": f"Tenant health {row['health_status']} (sync={row['sync_status']})",
                "occurred_at": row["last_sync_at"],
                "source": "ops_monitor",
            }
        )

    alerts.sort(key=lambda a: a.get("occurred_at") or "", reverse=True)
    return APIResponse(
        success=True,
        data={"alerts": alerts[:limit], "total": len(alerts)},
        error=None,
    )
