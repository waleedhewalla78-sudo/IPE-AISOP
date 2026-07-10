"""Production intelligence analytics (Sprint S9)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.bottleneck import detect_bottlenecks
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.models.work_order import WorkOrder
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/analytics", tags=["production-analytics"])

HORIZON_MINUTES = 10080  # 7 days


def _work_orders_to_assignments(work_orders: list[WorkOrder]) -> list[dict]:
    assignments = []
    for wo in work_orders:
        duration_min = float(wo.duration_planned_mins or 60)
        assignments.append(
            {
                "work_center_id": str(wo.work_center_id),
                "duration": duration_min,
                "mo_id": str(wo.mo_id),
                "operation_seq": wo.sequence,
            }
        )
    return assignments


async def _load_schedule_context(session: AsyncSession, tenant_id: UUID) -> tuple[list[dict], list[dict]]:
    wc_rows = (
        await session.execute(
            select(WorkCenter).where(WorkCenter.tenant_id == tenant_id)
        )
    ).scalars().all()
    work_centers = [
        {
            "id": str(wc.id),
            "name": wc.name,
            "capacity_hours_per_day": float(wc.capacity_hours_per_day or 8),
        }
        for wc in wc_rows
    ]

    wo_rows = (
        await session.execute(
            select(WorkOrder).where(
                WorkOrder.tenant_id == tenant_id,
                WorkOrder.status.in_(["pending", "in_progress", "released"]),
            )
        )
    ).scalars().all()

    assignments = _work_orders_to_assignments(wo_rows)
    return assignments, work_centers


@router.get("/bottlenecks")
async def production_bottlenecks(
    threshold_pct: float = Query(85.0, ge=50, le=100),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "manager", "supervisor"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    assignments, work_centers = await _load_schedule_context(session, UUID(tenant_id))
    bottlenecks = detect_bottlenecks(assignments, work_centers, HORIZON_MINUTES)
    flagged = [b for b in bottlenecks if b["utilization_pct"] >= threshold_pct]

    return APIResponse(
        success=True,
        data={
            "threshold_pct": threshold_pct,
            "bottleneck_count": len(flagged),
            "work_centers": bottlenecks,
            "top_bottlenecks": flagged[:5],
        },
        error=None,
    )


@router.get("/changeover")
async def changeover_analysis(
    lookback_days: int = Query(30, ge=7, le=90),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "manager", "supervisor"])),
):
    """Estimate changeover load from sequential operations on shared work centers."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)

    stmt = (
        select(
            WorkOrder.work_center_id,
            WorkCenter.name,
            func.count().label("operation_count"),
            func.sum(WorkOrder.duration_planned_mins).label("total_minutes"),
        )
        .join(WorkCenter, WorkCenter.id == WorkOrder.work_center_id)
        .where(
            WorkOrder.tenant_id == tid,
            WorkOrder.planned_start >= cutoff,
        )
        .group_by(WorkOrder.work_center_id, WorkCenter.name)
        .order_by(func.count().desc())
    )
    rows = (await session.execute(stmt)).all()

    changeovers = []
    for row in rows:
        ops = int(row.operation_count or 0)
        estimated_changeovers = max(0, ops - 1)
        avg_setup_min = 15.0
        changeovers.append(
            {
                "work_center_id": str(row.work_center_id),
                "work_center_name": row.name,
                "operation_count": ops,
                "estimated_changeovers": estimated_changeovers,
                "estimated_changeover_hours": round(estimated_changeovers * avg_setup_min / 60, 2),
                "total_scheduled_hours": round(float(row.total_minutes or 0) / 60, 2),
            }
        )

    total_hours = sum(c["estimated_changeover_hours"] for c in changeovers)
    return APIResponse(
        success=True,
        data={
            "lookback_days": lookback_days,
            "total_changeover_hours": round(total_hours, 2),
            "work_centers": changeovers,
        },
        error=None,
    )


@router.get("/utilisation")
async def utilisation_summary(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "manager", "supervisor"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    assignments, work_centers = await _load_schedule_context(session, UUID(tenant_id))
    utilisation = detect_bottlenecks(assignments, work_centers, HORIZON_MINUTES)

    avg_util = (
        round(sum(u["utilization_pct"] for u in utilisation) / len(utilisation), 1)
        if utilisation
        else 0.0
    )
    overloaded = [u for u in utilisation if u["is_bottleneck"]]

    return APIResponse(
        success=True,
        data={
            "horizon_days": 7,
            "average_utilization_pct": avg_util,
            "overloaded_count": len(overloaded),
            "work_centers": utilisation,
        },
        error=None,
    )
