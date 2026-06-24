from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.chaos_cost import aggregate_chaos_cost
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models import (
    DelayEvent,
    ManufacturingOrder,
    WorkCenter,
    WorkOrder,
)
from ipe_shared.models.demand import DemandLine
from ipe_shared.models.inventory import InventoryPosition
from ipe_shared.models.product import Product
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/executive-summary")
async def executive_summary(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    ai_stmt = select(
        func.count().filter(
            ManufacturingOrder.actual_end <= ManufacturingOrder.planned_end,
        ).label("on_time"),
        func.count().label("total"),
    ).where(
        ManufacturingOrder.tenant_id == tid,
        ManufacturingOrder.autonomy_action == "auto_confirmed",
        ManufacturingOrder.actual_end.isnot(None),
    )
    ai_row = (await session.execute(ai_stmt)).one()
    ai_otd_pct = round((ai_row.on_time / ai_row.total) * 100, 1) if ai_row.total else None

    manual_stmt = select(
        func.count().filter(
            ManufacturingOrder.actual_end <= ManufacturingOrder.planned_end,
        ).label("on_time"),
        func.count().label("total"),
    ).where(
        ManufacturingOrder.tenant_id == tid,
        ManufacturingOrder.autonomy_action.is_(None),
        ManufacturingOrder.actual_end.isnot(None),
    )
    manual_row = (await session.execute(manual_stmt)).one()
    manual_otd_pct = round((manual_row.on_time / manual_row.total) * 100, 1) if manual_row.total else None

    cycle_time_expr = extract("epoch", ManufacturingOrder.planned_start - DemandLine.created_at) / 86400.0
    ct_stmt = select(
        func.avg(cycle_time_expr).label("avg_days"),
    ).select_from(
        ManufacturingOrder,
    ).join(
        DemandLine, DemandLine.mo_id == ManufacturingOrder.id,
    ).where(
        ManufacturingOrder.tenant_id == tid,
        ManufacturingOrder.planned_start.isnot(None),
        DemandLine.created_at.isnot(None),
    )
    ct_row = (await session.execute(ct_stmt)).one()
    avg_planning_cycle_days = round(float(ct_row.avg_days), 1) if ct_row.avg_days else None

    inv_stmt = select(
        func.coalesce(
            func.sum(InventoryPosition.qty_on_hand * func.coalesce(Product.standard_cost, 0)),
            0,
        ).label("total_value"),
    ).select_from(
        InventoryPosition,
    ).join(
        Product, Product.id == InventoryPosition.product_id,
    ).where(
        InventoryPosition.tenant_id == tid,
    )
    inv_row = (await session.execute(inv_stmt)).one()
    inventory_value = round(float(inv_row.total_value), 2) if inv_row.total_value else 0.0

    delay_stmt = select(
        func.count().filter(
            DelayEvent.cause_category.isnot(None),
        ).label("classified"),
        func.count().label("total"),
    ).where(
        DelayEvent.tenant_id == tid,
    )
    delay_row = (await session.execute(delay_stmt)).one()
    delay_coverage_pct = round((delay_row.classified / delay_row.total) * 100, 1) if delay_row.total else 0.0

    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    day_col = func.date_trunc("day", ManufacturingOrder.actual_end)
    is_ai_col = case(
        (ManufacturingOrder.autonomy_action.isnot(None), True),
        else_=False,
    )
    otd_stmt = select(
        day_col.label("day"),
        is_ai_col.label("is_ai"),
        func.count().label("total"),
        func.count().filter(
            ManufacturingOrder.actual_end <= ManufacturingOrder.planned_end,
        ).label("on_time"),
    ).where(
        ManufacturingOrder.tenant_id == tid,
        ManufacturingOrder.actual_end.isnot(None),
        ManufacturingOrder.actual_end >= cutoff,
    ).group_by(
        day_col, is_ai_col,
    ).order_by(
        day_col,
    )
    otd_result = await session.execute(otd_stmt)
    otd_trend = [
        {
            "day": str(row.day),
            "is_ai": row.is_ai,
            "otd_pct": round(float(row.on_time) / float(row.total) * 100, 1) if row.total else 0.0,
        }
        for row in otd_result.fetchall()
    ]

    return APIResponse(
        success=True,
        data={
            "ai_otd_pct": ai_otd_pct,
            "manual_otd_pct": manual_otd_pct,
            "avg_planning_cycle_days": avg_planning_cycle_days,
            "inventory_value": inventory_value,
            "delay_coverage_pct": delay_coverage_pct,
            "otd_trend": otd_trend,
        },
        error=None,
    )


@router.get("/otd-by-work-center")
async def otd_by_work_center(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    try:
        stmt = (
            select(
                WorkCenter.name.label("work_center"),
                func.count().label("total_mos"),
                func.count().filter(
                    WorkOrder.actual_end <= WorkOrder.planned_end,
                ).label("on_time_mos"),
            )
            .select_from(WorkOrder)
            .join(WorkCenter, WorkCenter.id == WorkOrder.work_center_id)
            .where(
                WorkOrder.tenant_id == tid,
                WorkOrder.actual_end.isnot(None),
            )
            .group_by(WorkCenter.id, WorkCenter.name)
        )
        result = await session.execute(stmt)
        rows = result.fetchall()

        data = sorted(
            [
                {
                    "work_center": row.work_center,
                    "total_mos": row.total_mos,
                    "on_time_mos": row.on_time_mos,
                    "otd_pct": round(float(row.on_time_mos) / float(row.total_mos) * 100, 1) if row.total_mos else 0.0,
                }
                for row in rows
            ],
            key=lambda x: x["otd_pct"],
        )
    except Exception:
        data = []

    return APIResponse(success=True, data=data, error=None)


@router.get("/delay-breakdown")
async def delay_breakdown(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    try:
        total_stmt = select(func.count()).select_from(DelayEvent).where(DelayEvent.tenant_id == tid)
        total_count = (await session.execute(total_stmt)).scalar() or 0
        if total_count == 0:
            return APIResponse(success=True, data=[], error=None)

        stmt = (
            select(
                DelayEvent.cause_category,
                func.count().label("cnt"),
            )
            .where(DelayEvent.tenant_id == tid)
            .group_by(DelayEvent.cause_category)
            .order_by(func.count().desc())
        )
        result = await session.execute(stmt)

        data = [
            {
                "cause_category": row.cause_category,
                "count": row.cnt,
                "pct": round(row.cnt * 100.0 / total_count, 1),
            }
            for row in result.fetchall()
        ]
    except Exception:
        data = []

    return APIResponse(success=True, data=data, error=None)


@router.get("/planning-accuracy")
async def planning_accuracy(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    empty_result = {
        "avg_planned_vs_actual_days": None,
        "median_planned_vs_actual_days": None,
        "pct_within_1_day": None,
        "pct_within_3_days": None,
        "pct_within_7_days": None,
        "max_overrun_days": None,
        "total_mos_analyzed": 0,
    }

    try:
        overrun_expr = extract("epoch", ManufacturingOrder.actual_end - ManufacturingOrder.planned_end) / 86400.0

        stmt = select(overrun_expr.label("overrun_days")).where(
            ManufacturingOrder.tenant_id == tid,
            ManufacturingOrder.actual_end.isnot(None),
            ManufacturingOrder.planned_end.isnot(None),
        )
        result = await session.execute(stmt)
        overruns = [float(row.overrun_days) for row in result.fetchall() if row.overrun_days is not None]

        if not overruns:
            return APIResponse(success=True, data=empty_result, error=None)

        n = len(overruns)
        avg_overrun = sum(overruns) / n
        sorted_overruns = sorted(overruns)
        median_overrun = sorted_overruns[n // 2]
        within_1 = sum(1 for o in overruns if abs(o) <= 1) / n * 100
        within_3 = sum(1 for o in overruns if abs(o) <= 3) / n * 100
        within_7 = sum(1 for o in overruns if abs(o) <= 7) / n * 100
        max_overrun = max(overruns)

        data = {
            "avg_planned_vs_actual_days": round(avg_overrun, 1),
            "median_planned_vs_actual_days": round(median_overrun, 1),
            "pct_within_1_day": round(within_1, 1),
            "pct_within_3_days": round(within_3, 1),
            "pct_within_7_days": round(within_7, 1),
            "max_overrun_days": round(max_overrun, 1),
            "total_mos_analyzed": n,
        }
    except Exception:
        data = empty_result

    return APIResponse(success=True, data=data, error=None)


@router.get("/cost-of-chaos")
async def cost_of_chaos(
    period: str = Query(default="7d", pattern="^(7d|30d)$"),
    category: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "executive", "cfo"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    period_days = 7 if period == "7d" else 30
    data = await aggregate_chaos_cost(
        session,
        UUID(tenant_id),
        period_days=period_days,
        category_filter=category,
    )
    data["period"] = period
    return APIResponse(success=True, data=data, error=None)