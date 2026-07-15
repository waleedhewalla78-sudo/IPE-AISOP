"""A1.1 Planning Cockpit — plan health + attention queue."""

from __future__ import annotations

from typing import Any


def _pct(num: float, den: float) -> float:
    if den <= 0:
        return 0.0
    return round(100.0 * num / den, 1)


def build_planning_cockpit(
    *,
    tenant_id: str,
    demand_orders: int = 50,
    confirmed_mos: int = 47,
    planned_production: float = 245,
    inventory: float = 45,
    total_demand: float = 300,
    weeks_with_plan: int = 9,
    horizon_weeks: int = 12,
    unchanged_mos: int = 43,
    total_mos: int = 47,
    frozen_weeks: int = 2,
    mos_at_risk: int = 5,
    materials_below_ss: int = 3,
    over_capacity_wcs: list[dict[str, Any]] | None = None,
    atp_pending: int = 2,
    mrp_needed: bool = True,
) -> dict[str, Any]:
    over_capacity_wcs = over_capacity_wcs or [
        {"work_centre": "Winding", "utilisation_pct": 102, "week": "W30"}
    ]
    plan_coverage = _pct(confirmed_mos, demand_orders)
    balance = _pct(planned_production + inventory, total_demand)
    horizon = _pct(weeks_with_plan, horizon_weeks)
    stability = _pct(unchanged_mos, total_mos)

    attention: list[dict[str, Any]] = []
    if mos_at_risk:
        attention.append(
            {
                "severity": "red",
                "code": "MOS_AT_RISK",
                "message": f"{mos_at_risk} MOs at risk (next 7 days)",
                "action": "resolve",
            }
        )
    if materials_below_ss:
        attention.append(
            {
                "severity": "amber",
                "code": "MATERIAL_SS",
                "message": f"{materials_below_ss} materials below safety stock",
                "action": "review_supply",
            }
        )
    for wc in over_capacity_wcs:
        attention.append(
            {
                "severity": "amber",
                "code": "CAPACITY_OVERLOAD",
                "message": (
                    f"{wc.get('work_centre')} at {wc.get('utilisation_pct')}% "
                    f"in {wc.get('week')}"
                ),
                "action": "rebalance",
            }
        )
    if mrp_needed:
        attention.append(
            {
                "severity": "blue",
                "code": "MRP_NEEDED",
                "message": "MRP run needed (new orders)",
                "action": "run_mrp",
            }
        )
    if atp_pending:
        attention.append(
            {
                "severity": "blue",
                "code": "ATP_PENDING",
                "message": f"{atp_pending} ATP requests pending",
                "action": "promise",
            }
        )

    timeline = []
    for i, (cov, mos, risk, mat, cap) in enumerate(
        [
            (94, 47, 5, "OK", "WND warn"),
            (86, 38, 2, "OK", "OK"),
            (72, 28, 0, "Cu wire", "OK"),
            (45, 15, 0, "Need MRP", "Unknown"),
        ],
        start=29,
    ):
        timeline.append(
            {
                "week": f"W{i}",
                "coverage_pct": cov,
                "mos": mos,
                "at_risk": risk,
                "materials": mat,
                "capacity": cap,
            }
        )

    return {
        "tenant_id": tenant_id,
        "plan_health": {
            "plan_coverage_pct": plan_coverage,
            "demand_supply_balance_pct": balance,
            "horizon_coverage_pct": horizon,
            "plan_stability_pct": stability,
            "schedule_frozen_weeks": frozen_weeks,
        },
        "attention": attention,
        "timeline": timeline,
        "actions": ["run_mrp", "update_mps", "check_atp", "open_scenarios"],
    }
