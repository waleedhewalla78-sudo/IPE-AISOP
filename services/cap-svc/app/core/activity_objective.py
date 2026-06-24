"""Activity-based scheduling objective — extends cost solver with setup/expedite terms."""

from __future__ import annotations

from typing import Any

from app.core.scheduler_cost import solve_cost_optimized


def estimate_activity_costs(
    operations: list[dict],
    work_centers: list[dict],
    *,
    setup_cost_per_change: float = 120.0,
    expedite_cost_per_unit: float = 0.0,
) -> dict[str, float]:
    """Estimate activity-based costs from a schedule proposal."""
    wc_setup_counts: dict[str, int] = {}
    for op in operations:
        wc_id = str(op.get("work_center_id", ""))
        wc_setup_counts[wc_id] = wc_setup_counts.get(wc_id, 0) + 1

    setup_usd = sum(max(0, count - 1) * setup_cost_per_change for count in wc_setup_counts.values())
    overtime_usd = 0.0
    for wc in work_centers:
        wc_id = str(wc.get("id", ""))
        cost_per_hour = float(wc.get("cost_per_hour") or 0)
        ot_mult = float(wc.get("overtime_cost_multiplier") or 1.5)
        wc_ops = [o for o in operations if str(o.get("work_center_id")) == wc_id]
        total_mins = sum(int(o.get("duration") or 0) for o in wc_ops)
        if total_mins > 8 * 60:
            overtime_mins = total_mins - 8 * 60
            overtime_usd += (overtime_mins / 60.0) * cost_per_hour * (ot_mult - 1.0)

    mo_ids = {str(o.get("mo_id")) for o in operations if o.get("mo_id")}
    expedite_usd = expedite_cost_per_unit * max(1, len(mo_ids))
    total = setup_usd + overtime_usd + expedite_usd
    return {
        "overtime_usd": round(overtime_usd, 2),
        "setup_usd": round(setup_usd, 2),
        "expedite_usd": round(expedite_usd, 2),
        "total_usd": round(total, 2),
    }


def solve_activity_optimized(
    work_centers: list[dict],
    operations: list[dict],
    *,
    horizon: int = 168 * 60,
    alpha: float = 0.5,
    tariffs: list[dict] | None = None,
    frozen_ops: list[dict] | None = None,
    setup_cost_per_change: float = 120.0,
    expedite_cost_per_unit: float = 0.0,
) -> dict[str, Any]:
    """Run cost-optimized solve and attach activity-based cost breakdown."""
    cost_alpha = max(0.1, min(0.9, 1.0 - alpha))
    result = solve_cost_optimized(
        work_centers=work_centers,
        operations=operations,
        horizon=horizon,
        alpha=cost_alpha,
        tariffs=tariffs,
        frozen_ops=frozen_ops,
    )
    if not result.get("assignments"):
        result["activity_cost_breakdown"] = {
            "overtime_usd": 0.0,
            "setup_usd": 0.0,
            "expedite_usd": 0.0,
            "total_usd": 0.0,
        }
        result["optimality_gap_pct"] = None
        return result

    activity = estimate_activity_costs(
        result["assignments"],
        work_centers,
        setup_cost_per_change=setup_cost_per_change,
        expedite_cost_per_unit=expedite_cost_per_unit,
    )
    cost_summary = result.get("cost_summary") or {}
    activity["energy_labor_usd"] = round(float(cost_summary.get("total_cost", 0)), 2)
    activity["total_usd"] = round(
        activity["total_usd"] + float(cost_summary.get("total_cost", 0)), 2
    )
    result["activity_cost_breakdown"] = activity
    result["optimality_gap_pct"] = round(float(cost_summary.get("optimality_gap", 0) or 0), 2)
    return result
