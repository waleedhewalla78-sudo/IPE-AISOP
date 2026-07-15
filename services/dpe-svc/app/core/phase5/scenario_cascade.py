"""A1.7 Enhanced scenario — demand/capacity/material/finance/customer cascade."""

from __future__ import annotations

from typing import Any


def run_scenario_cascade(
    *,
    name: str = "Q4 demand +20%",
    demand_uplift_pct: float = 20.0,
    baseline_revenue: float = 2_400_000.0,
    winding_util_pct: float = 84.0,
    copper_weeks_cover: float = 4.0,
    otd_pct: float = 89.0,
) -> dict[str, Any]:
    """Simulate cascade impact of a planning what-if (pure functions, no ERP write)."""
    uplift = demand_uplift_pct / 100.0
    new_revenue = round(baseline_revenue * (1 + uplift), 0)
    delta_rev = new_revenue - baseline_revenue
    new_winding = round(winding_util_pct * (1 + uplift), 1)
    new_copper_weeks = round(copper_weeks_cover / (1 + uplift), 1)
    new_otd = round(max(50.0, otd_pct - uplift * 65), 1)

    overtime = round(28_800 * (uplift / 0.2), 0)
    expedite = round(12_000 * (uplift / 0.2), 0)
    spot_mat = round(8_400 * (uplift / 0.2), 0)
    additional_cost = overtime + expedite + spot_mat
    additional_margin = max(0.0, delta_rev - additional_cost)
    investment = round(232_800 * (uplift / 0.2), 0)
    roi = round(additional_margin / investment, 2) if investment else 0.0

    overloaded_weeks = 6 if new_winding > 100 else 0
    recommend = "proceed" if roi >= 1.2 and new_winding < 115 else "mitigate_first"

    return {
        "scenario": name,
        "assumptions": {
            "demand_uplift_pct": demand_uplift_pct,
            "baseline_revenue": baseline_revenue,
        },
        "demand_impact": {
            "consensus_revenue": new_revenue,
            "delta_revenue": delta_rev,
            "mix_notes": "DT100 +25%, DT250 +15%, PT500 +20% (illustrative)",
        },
        "capacity_impact": {
            "winding_util_pct": new_winding,
            "assembly_util_pct": round(65 * (1 + uplift * 0.5), 1),
            "constraint": "Winding" if new_winding > 100 else None,
            "overloaded_weeks": overloaded_weeks,
        },
        "material_impact": {
            "copper_weeks_cover": new_copper_weeks,
            "materials_below_ss": 4 if new_copper_weeks < 3.5 else 1,
            "additional_po_value": round(186_000 * (uplift / 0.2), 0),
        },
        "financial_impact": {
            "additional_revenue": delta_rev,
            "additional_costs": additional_cost,
            "cost_breakdown": {
                "overtime": overtime,
                "expediting": expedite,
                "spot_materials": spot_mat,
            },
            "additional_margin": additional_margin,
            "investment_to_capture": investment,
            "roi": roi,
        },
        "customer_impact": {
            "otd_pct_without_action": new_otd,
            "at_risk_customers": ["Saudi Electricity", "Dubai Water"] if new_otd < 85 else [],
        },
        "recommended_actions": [
            "Add Saturday shift at Winding for constrained weeks",
            "Order copper 30% above current plan (normal terms)",
            "Hire temporary Winding capacity if overload persists",
        ],
        "recommendation": recommend,
        "agents": ["A1", "A2", "A3", "A8", "A11"],
    }
