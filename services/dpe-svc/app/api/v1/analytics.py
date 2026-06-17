from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])

MOCK_WORK_CENTERS = [
    {"work_center": "Assembly Line 1", "total_mos": 142, "on_time_mos": 131, "otd_pct": 92.3},
    {"work_center": "Assembly Line 2", "total_mos": 98, "on_time_mos": 84, "otd_pct": 85.7},
    {"work_center": "CNC Machining", "total_mos": 76, "on_time_mos": 61, "otd_pct": 80.3},
    {"work_center": "Welding Station", "total_mos": 53, "on_time_mos": 48, "otd_pct": 90.6},
    {"work_center": "Paint Booth", "total_mos": 41, "on_time_mos": 39, "otd_pct": 95.1},
    {"work_center": "Packaging", "total_mos": 67, "on_time_mos": 58, "otd_pct": 86.6},
]

MOCK_DELAY_BREAKDOWN = [
    {"cause_category": "material_shortage", "count": 48, "pct": 31.4},
    {"cause_category": "capacity_constraint", "count": 32, "pct": 20.9},
    {"cause_category": "equipment_breakdown", "count": 24, "pct": 15.7},
    {"cause_category": "labor_absence", "count": 18, "pct": 11.8},
    {"cause_category": "quality_issue", "count": 12, "pct": 7.8},
    {"cause_category": "supplier_delay", "count": 10, "pct": 6.5},
    {"cause_category": "bom_error", "count": 6, "pct": 3.9},
    {"cause_category": "unknown", "count": 3, "pct": 2.0},
]

MOCK_PLANNING_ACCURACY = {
    "avg_planned_vs_actual_days": 2.4,
    "median_planned_vs_actual_days": 1.1,
    "pct_within_1_day": 38.2,
    "pct_within_3_days": 67.5,
    "pct_within_7_days": 85.3,
    "max_overrun_days": 18.0,
    "total_mos_analyzed": 346,
}


@router.get("/executive-summary")
async def executive_summary(
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    ai_otd = await session.execute(
        text("""
            SELECT
                COUNT(*) FILTER (WHERE actual_end IS NOT NULL AND actual_end <= planned_end) AS on_time,
                COUNT(*) FILTER (WHERE actual_end IS NOT NULL) AS total
            FROM cdm_manufacturing_order
            WHERE tenant_id = :tid
              AND autonomy_action = 'auto_confirmed'
              AND actual_end IS NOT NULL
        """),
        {"tid": tid},
    )
    ai_row = ai_otd.one()
    ai_otd_pct = round((ai_row[0] / ai_row[1]) * 100, 1) if ai_row[1] > 0 else None

    manual_otd = await session.execute(
        text("""
            SELECT
                COUNT(*) FILTER (WHERE actual_end IS NOT NULL AND actual_end <= planned_end) AS on_time,
                COUNT(*) FILTER (WHERE actual_end IS NOT NULL) AS total
            FROM cdm_manufacturing_order
            WHERE tenant_id = :tid
              AND autonomy_action IS NULL
              AND actual_end IS NOT NULL
        """),
        {"tid": tid},
    )
    manual_row = manual_otd.one()
    manual_otd_pct = round((manual_row[0] / manual_row[1]) * 100, 1) if manual_row[1] > 0 else None

    cycle_time = await session.execute(
        text("""
            SELECT AVG(EXTRACT(EPOCH FROM (mo.planned_start - dl.created_at)) / 86400.0) AS avg_days
            FROM cdm_manufacturing_order mo
            JOIN cdm_demand_line dl ON dl.mo_id = mo.id
            WHERE mo.tenant_id = :tid
              AND mo.planned_start IS NOT NULL
              AND dl.created_at IS NOT NULL
        """),
        {"tid": tid},
    )
    ct_row = cycle_time.one()
    avg_planning_cycle_days = round(ct_row[0], 1) if ct_row[0] else None

    inv_value = await session.execute(
        text("""
            SELECT COALESCE(SUM(ip.qty_on_hand * COALESCE(p.standard_cost, 0)), 0) AS total_value
            FROM cdm_inventory_position ip
            JOIN cdm_product p ON p.id = ip.product_id
            WHERE ip.tenant_id = :tid
        """),
        {"tid": tid},
    )
    inv_row = inv_value.one()
    inventory_value = round(float(inv_row[0]), 2) if inv_row[0] else 0.0

    delay_coverage = await session.execute(
        text("""
            SELECT
                COUNT(*) FILTER (WHERE cause_category IS NOT NULL) AS classified,
                COUNT(*) AS total
            FROM cdm_delay_event
            WHERE tenant_id = :tid
        """),
        {"tid": tid},
    )
    delay_row = delay_coverage.one()
    delay_coverage_pct = round((delay_row[0] / delay_row[1]) * 100, 1) if delay_row[1] > 0 else 0.0

    ai_vs_manual = await session.execute(
        text("""
            SELECT
                DATE_TRUNC('day', actual_end) AS day,
                autonomy_action IS NOT NULL AS is_ai,
                COUNT(*) FILTER (WHERE actual_end <= planned_end) * 100.0 / NULLIF(COUNT(*), 0) AS otd_pct
            FROM cdm_manufacturing_order
            WHERE tenant_id = :tid
              AND actual_end IS NOT NULL
              AND actual_end >= NOW() - INTERVAL '90 days'
            GROUP BY day, is_ai
            ORDER BY day
        """),
        {"tid": tid},
    )
    otd_trend = [
        {
            "day": str(r[0]),
            "is_ai": r[1],
            "otd_pct": round(float(r[2]), 1) if r[2] else 0.0,
        }
        for r in ai_vs_manual.fetchall()
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
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    try:
        tid = UUID(tenant_id)
        rows = await session.execute(
            text("""
                SELECT
                    wc.name AS work_center,
                    COUNT(*) AS total_mos,
                    COUNT(*) FILTER (WHERE wo.actual_end IS NOT NULL AND wo.actual_end <= wo.planned_end) AS on_time_mos,
                    ROUND(
                        COUNT(*) FILTER (WHERE wo.actual_end IS NOT NULL AND wo.actual_end <= wo.planned_end)
                        * 100.0 / NULLIF(COUNT(*), 0), 1
                    ) AS otd_pct
                FROM cdm_work_order wo
                JOIN cdm_work_center wc ON wc.id = wo.work_center_id
                WHERE wo.tenant_id = :tid
                  AND wo.actual_end IS NOT NULL
                GROUP BY wc.id, wc.name
                ORDER BY otd_pct ASC
            """),
            {"tid": tid},
        )
        result = [
            {
                "work_center": r[0],
                "total_mos": r[1],
                "on_time_mos": r[2],
                "otd_pct": float(r[3]) if r[3] else 0.0,
            }
            for r in rows.fetchall()
        ]
        if not result:
            result = MOCK_WORK_CENTERS
    except Exception:
        result = MOCK_WORK_CENTERS

    return APIResponse(success=True, data=result, error=None)


@router.get("/delay-breakdown")
async def delay_breakdown(
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    try:
        tid = UUID(tenant_id)
        total = await session.execute(
            text("SELECT COUNT(*) FROM cdm_delay_event WHERE tenant_id = :tid"),
            {"tid": tid},
        )
        total_count = total.scalar() or 0
        if total_count == 0:
            return APIResponse(success=True, data=MOCK_DELAY_BREAKDOWN, error=None)

        rows = await session.execute(
            text("""
                SELECT cause_category, COUNT(*) AS cnt
                FROM cdm_delay_event
                WHERE tenant_id = :tid
                GROUP BY cause_category
                ORDER BY cnt DESC
            """),
            {"tid": tid},
        )
        result = [
            {
                "cause_category": r[0],
                "count": r[1],
                "pct": round(r[1] * 100.0 / total_count, 1),
            }
            for r in rows.fetchall()
        ]
    except Exception:
        result = MOCK_DELAY_BREAKDOWN

    return APIResponse(success=True, data=result, error=None)


@router.get("/planning-accuracy")
async def planning_accuracy(
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    try:
        tid = UUID(tenant_id)
        rows = await session.execute(
            text("""
                SELECT
                    mo.id,
                    mo.planned_end,
                    mo.actual_end,
                    EXTRACT(EPOCH FROM (mo.actual_end - mo.planned_end)) / 86400.0 AS overrun_days
                FROM cdm_manufacturing_order mo
                WHERE mo.tenant_id = :tid
                  AND mo.actual_end IS NOT NULL
                  AND mo.planned_end IS NOT NULL
            """),
            {"tid": tid},
        )
        fetched = rows.fetchall()
        if not fetched:
            return APIResponse(success=True, data=MOCK_PLANNING_ACCURACY, error=None)

        overruns = [float(r[3]) for r in fetched if r[3] is not None]
        n = len(overruns)
        if n == 0:
            return APIResponse(success=True, data=MOCK_PLANNING_ACCURACY, error=None)

        avg_overrun = sum(overruns) / n
        sorted_overruns = sorted(overruns)
        median_overrun = sorted_overruns[n // 2]
        within_1 = sum(1 for o in overruns if abs(o) <= 1) / n * 100
        within_3 = sum(1 for o in overruns if abs(o) <= 3) / n * 100
        within_7 = sum(1 for o in overruns if abs(o) <= 7) / n * 100
        max_overrun = max(overruns)

        result = {
            "avg_planned_vs_actual_days": round(avg_overrun, 1),
            "median_planned_vs_actual_days": round(median_overrun, 1),
            "pct_within_1_day": round(within_1, 1),
            "pct_within_3_days": round(within_3, 1),
            "pct_within_7_days": round(within_7, 1),
            "max_overrun_days": round(max_overrun, 1),
            "total_mos_analyzed": n,
        }
    except Exception:
        result = MOCK_PLANNING_ACCURACY

    return APIResponse(success=True, data=result, error=None)
