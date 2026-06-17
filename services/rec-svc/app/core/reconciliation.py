from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.work_order import WorkOrder


def analyze_mo_completion(
    mo: ManufacturingOrder,
    work_orders: list[WorkOrder],
) -> dict:
    planned_start = mo.planned_start
    planned_end = mo.planned_end
    actual_start = mo.actual_start
    actual_end = mo.actual_end

    if planned_start and planned_end:
        planned_duration = (planned_end - planned_start).total_seconds() / 86400.0
    elif work_orders:
        planned_duration = sum(
            (wo.duration_planned_mins or 0) for wo in work_orders
        ) / (24 * 60.0)
    else:
        planned_duration = 1.0

    if actual_start and actual_end:
        actual_duration = (actual_end - actual_start).total_seconds() / 86400.0
    elif work_orders:
        actual_duration = sum(
            (wo.duration_actual_mins or 0) for wo in work_orders
        ) / (24 * 60.0)
    else:
        actual_duration = planned_duration

    time_variance_pct = round(
        ((actual_duration - planned_duration) / planned_duration) * 100, 2
    ) if planned_duration else 0.0

    yield_planned = float(mo.yield_planned) if mo.yield_planned else 0.0
    yield_actual = float(mo.yield_actual) if mo.yield_actual else 0.0

    yield_variance_pct = round(
        ((yield_actual - yield_planned) / yield_planned) * 100, 2
    ) if yield_planned else 0.0

    scrap_delta = float(mo.scrap_actual) if mo.scrap_actual else 0.0

    completed_wo = sum(1 for wo in work_orders if wo.status == "completed")
    total_wo = len(work_orders)

    return {
        "mo_id": str(mo.id),
        "time_variance_pct": time_variance_pct,
        "yield_variance_pct": yield_variance_pct,
        "scrap_delta": scrap_delta,
        "planned_duration_days": round(planned_duration, 2),
        "actual_duration_days": round(actual_duration, 2),
        "completed_work_orders": completed_wo,
        "total_work_orders": total_wo,
    }
