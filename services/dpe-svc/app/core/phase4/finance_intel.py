"""A11 Finance Intelligence — MO margin, decision P&L, cash flow sketch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MOMargin:
    mo_id: str
    revenue: float
    material_cost: float
    labour_cost: float
    overhead: float
    total_cost: float
    gross_margin: float
    gross_margin_pct: float
    target_margin_pct: float
    variance_unfavourable: float
    alert: str | None


def compute_mo_margin(
    *,
    mo_id: str,
    revenue: float,
    material_cost: float,
    labour_cost: float,
    overhead: float = 0.0,
    standard_material: float | None = None,
    standard_labour: float | None = None,
    target_margin_pct: float = 25.0,
) -> MOMargin:
    total = material_cost + labour_cost + overhead
    gross = revenue - total
    pct = round((gross / revenue) * 100, 2) if revenue else 0.0
    mat_var = max(0.0, material_cost - (standard_material or material_cost))
    lab_var = max(0.0, labour_cost - (standard_labour or labour_cost))
    variance = round(mat_var + lab_var, 2)
    alert = None
    if pct < target_margin_pct:
        alert = (
            f"{mo_id} margin eroded to {pct}% (target {target_margin_pct}%). "
            f"Primary variance ${variance:,.0f}."
        )
    return MOMargin(
        mo_id=mo_id,
        revenue=revenue,
        material_cost=material_cost,
        labour_cost=labour_cost,
        overhead=overhead,
        total_cost=round(total, 2),
        gross_margin=round(gross, 2),
        gross_margin_pct=pct,
        target_margin_pct=target_margin_pct,
        variance_unfavourable=variance,
        alert=alert,
    )


def evaluate_decision_pnl(
    *,
    decision: str,
    direct_cost: float,
    revenue_protected: float = 0.0,
    penalty_avoided: float = 0.0,
    mtd_revenue: float = 0.0,
    mtd_direct_costs: float = 0.0,
) -> dict[str, Any]:
    net = revenue_protected + penalty_avoided - direct_cost
    roi = round(net / direct_cost, 1) if direct_cost > 0 else None
    mtd_costs = mtd_direct_costs + direct_cost
    mtd_gp = mtd_revenue - mtd_costs
    return {
        "decision": decision,
        "direct_cost": direct_cost,
        "revenue_protected": revenue_protected,
        "penalty_avoided": penalty_avoided,
        "net_impact": round(net, 2),
        "roi": roi,
        "mtd": {
            "revenue": mtd_revenue,
            "direct_costs": round(mtd_costs, 2),
            "gross_profit": round(mtd_gp, 2),
            "net_pnl_effect": round(penalty_avoided - direct_cost, 2),
        },
        "recommendation": "approve" if net > 0 else "reject",
    }


def cash_flow_forecast(
    weeks: list[dict[str, Any]],
    *,
    opening_balance: float,
    threshold: float = 250_000.0,
) -> dict[str, Any]:
    """Build multi-week cash sketch with threshold alerts."""
    balance = opening_balance
    out_weeks = []
    alerts = []
    for w in weeks:
        inflow = float(w.get("inflows", 0))
        outflow = float(w.get("outflows", 0))
        net = inflow - outflow
        balance = round(balance + net, 2)
        row = {
            "week": w.get("week"),
            "inflows": inflow,
            "outflows": outflow,
            "net": round(net, 2),
            "closing_balance": balance,
            "below_threshold": balance < threshold,
        }
        out_weeks.append(row)
        if balance < threshold:
            alerts.append(
                f"Cash balance {balance:,.0f} below {threshold:,.0f} in {w.get('week')}."
            )
    return {"opening_balance": opening_balance, "threshold": threshold, "weeks": out_weeks, "alerts": alerts}


class FinanceIntelligence:
    """A11 facade."""

    def mo_margin(self, **kwargs: Any) -> dict[str, Any]:
        m = compute_mo_margin(**kwargs)
        return {
            "agent_id": "A11",
            "mo_id": m.mo_id,
            "revenue": m.revenue,
            "material_cost": m.material_cost,
            "labour_cost": m.labour_cost,
            "overhead": m.overhead,
            "total_cost": m.total_cost,
            "gross_margin": m.gross_margin,
            "gross_margin_pct": m.gross_margin_pct,
            "target_margin_pct": m.target_margin_pct,
            "variance_unfavourable": m.variance_unfavourable,
            "alert": m.alert,
        }

    def decision_pnl(self, **kwargs: Any) -> dict[str, Any]:
        return {"agent_id": "A11", **evaluate_decision_pnl(**kwargs)}

    def cash_flow(self, weeks: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        return {"agent_id": "A11", **cash_flow_forecast(weeks, **kwargs)}
