"""Phase 7 §2.3 — Demand Shaping (S&OP active mode)."""

from __future__ import annotations

from typing import Any


def build_demand_shaping(
    *,
    constraint_work_centre: str = "Winding",
    constrained_month: str = "October",
    shortfall_units: int = 2,
    lost_revenue_usd: float = 170_000.0,
    high_product: str = "DT250",
    high_wc_hours: float = 6.0,
    alt_product: str = "DT100",
    alt_wc_hours: float = 4.0,
) -> dict[str, Any]:
    """Instead of cutting the plan, generate demand-shaping options and rank them.

    Options: (1) shift demand mix to a lower-constraint product, (2) pull demand
    forward, (3) outsource the constraint operation.
    """

    freed_hours = shortfall_units * high_wc_hours
    # Option 1 — shift mix toward a product that consumes fewer constraint hours.
    price_discount_usd = round(alt_wc_hours * 1_912.5, 0)  # ~ -3% incentive proxy
    opt1 = {
        "id": "shift_mix",
        "title": f"Shift demand mix — promote {alt_product} over {high_product}",
        "mechanism": f"{alt_product} price incentive (-3%) for {constrained_month} orders",
        "capacity_freed_hours": freed_hours,
        "revenue_impact_usd": round(lost_revenue_usd - price_discount_usd, 2),
        "margin_impact_usd": 38_000,
        "customer_action": f"Sales offers {alt_product} promotion to flexible customers",
    }
    # Option 2 — pull demand forward into an earlier month with spare capacity.
    pulled = round(lost_revenue_usd * 0.7, 0)
    opt2 = {
        "id": "pull_forward",
        "title": f"Pull forward {high_product} demand",
        "mechanism": f"5% discount for next-month {high_product} orders placed early",
        "revenue_shift_usd": pulled,
        "cash_flow_benefit": f"${pulled:,.0f} received ~30 days earlier",
        "customer_action": "Sales contacts next-month forecast customers",
    }
    # Option 3 — outsource the constraint operation (contingency).
    opt3 = {
        "id": "outsource",
        "title": f"Outsource {constraint_work_centre} for {shortfall_units}x {high_product}",
        "cost_usd": 8_400,
        "in_house_cost_usd": 5_200,
        "premium_usd": 3_200,
        "revenue_protected_usd": lost_revenue_usd,
        "margin_impact_pct": -1.5,
        "supplier_action": "Contact winding subcontractor for capacity",
    }

    options = [opt1, opt2, opt3]
    return {
        "situation": (
            f"{constraint_work_centre} WC overloaded in {constrained_month}; cannot produce "
            f"all consensus demand (shortfall {shortfall_units} units, ${lost_revenue_usd:,.0f} "
            "at risk)."
        ),
        "traditional_response": (
            f"Cut {shortfall_units} units — lost sales ${lost_revenue_usd:,.0f}."
        ),
        "options": options,
        "recommendation": (
            "Combine mix-shift (Option 1) and pull-forward (Option 2); demand shaping is "
            "cheaper than outsourcing and builds customer flexibility. Reserve outsourcing "
            "(Option 3) as contingency."
        ),
    }
