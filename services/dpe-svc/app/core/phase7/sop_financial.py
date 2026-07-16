"""Phase 7 §2.1 — Financial S&OP (volume + P&L per consensus)."""

from __future__ import annotations

from typing import Any


def build_financial_sop(
    *,
    product: str = "DT250",
    unit_price: float = 85_000.0,
    material_cost_per_unit: float = 58_000.0,
    labour_cost_per_unit: float = 5_040.0,
    overhead_per_unit: float = 3_360.0,
    periods: list[dict[str, Any]] | None = None,
    margin_floor_pct: float = 20.0,
) -> dict[str, Any]:
    """Every S&OP row is simultaneously a volume decision and a financial decision.

    Each period supplies consensus_demand and constrained_supply (units); the engine
    derives revenue, cost stack, gross profit, margin, and flags margin erosion.
    """

    periods = periods or [
        {
            "period": "Sep",
            "consensus_demand": 25,
            "constrained_supply": 25,
            "material_infl_pct": 0.0,
        },
        {
            "period": "Oct",
            "consensus_demand": 30,
            "constrained_supply": 28,
            "material_infl_pct": 3.0,
        },
        {
            "period": "Nov",
            "consensus_demand": 28,
            "constrained_supply": 28,
            "material_infl_pct": 3.0,
        },
    ]

    rows: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []
    for p in periods:
        demand = float(p["consensus_demand"])
        supply = float(p.get("constrained_supply", demand))
        lost = max(demand - supply, 0.0)
        infl = float(p.get("material_infl_pct", 0.0)) / 100.0
        mat = material_cost_per_unit * (1 + infl)
        revenue = supply * unit_price
        material_cost = supply * mat
        labour_cost = supply * labour_cost_per_unit
        overhead = supply * overhead_per_unit
        gross_profit = revenue - material_cost - labour_cost - overhead
        margin_pct = round(gross_profit / revenue * 100.0, 1) if revenue else 0.0
        lost_revenue = lost * unit_price
        row = {
            "period": p["period"],
            "consensus_demand": demand,
            "constrained_supply": supply,
            "lost_sales_units": lost,
            "revenue_usd": round(revenue, 2),
            "lost_revenue_usd": round(lost_revenue, 2),
            "material_cost_usd": round(material_cost, 2),
            "labour_cost_usd": round(labour_cost, 2),
            "overhead_usd": round(overhead, 2),
            "gross_profit_usd": round(gross_profit, 2),
            "margin_pct": margin_pct,
            "margin_below_floor": margin_pct < margin_floor_pct,
        }
        rows.append(row)
        if margin_pct < margin_floor_pct:
            alerts.append(
                {
                    "agent": "A11",
                    "period": p["period"],
                    "severity": "warning",
                    "message": (
                        f"{p['period']} margin drops to {margin_pct:.1f}% due to capacity "
                        f"constraint (lost {lost:.0f} units) and material cost increase."
                    ),
                    "actions": [
                        {
                            "id": "overtime",
                            "desc": (
                                f"Add {product} overtime — "
                                f"recovers ~${lost_revenue:,.0f} revenue"
                            ),
                            "net_usd": round(lost_revenue - 3_600, 2),
                        },
                        {
                            "id": "price_lock",
                            "desc": "Negotiate copper wire price lock for the quarter",
                            "net_usd": 42_000,
                        },
                    ],
                }
            )

    return {
        "product": product,
        "unit_price_usd": unit_price,
        "margin_floor_pct": margin_floor_pct,
        "periods": rows,
        "finance_alerts": alerts,
        "recommendation": (
            "Approve overtime for constrained periods and initiate supplier price-lock "
            "negotiation; combined impact restores margin above floor."
            if alerts
            else "All periods above margin floor — no financial intervention required."
        ),
    }
