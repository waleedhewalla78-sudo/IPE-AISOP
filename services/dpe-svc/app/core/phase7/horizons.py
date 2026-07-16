"""Phase 7 §1 — Multi-Horizon Planning Framework.

Three simultaneous planning horizons (strategic / tactical / operational) with a
cascade engine: decisions flow DOWN, constraints flow UP. Deterministic compute
over supplied inputs (falls back to Star-Trans defaults) — no live ERP dependency.
"""

from __future__ import annotations

from typing import Any

HORIZONS = ("strategic", "tactical", "operational")

_HORIZON_META = {
    "strategic": {
        "label": "Strategic",
        "window_months": "12-24",
        "granularity": "monthly/quarterly",
        "decisions": ["capacity investment", "new product introduction", "market entry"],
        "stakeholders": ["CEO", "board", "VP operations"],
        "updated": "quarterly",
        "agent_lead": ["A6", "A14"],
    },
    "tactical": {
        "label": "Tactical",
        "window_months": "1-6",
        "granularity": "weekly",
        "decisions": ["S&OP consensus", "workforce planning", "supplier commitments"],
        "stakeholders": ["Ops Director", "department heads"],
        "updated": "monthly (S&OP cycle)",
        "agent_lead": ["A6", "A1", "A3"],
    },
    "operational": {
        "label": "Operational",
        "window_months": "0-1",
        "granularity": "daily/shift",
        "decisions": ["MO scheduling", "material expediting", "capacity allocation"],
        "stakeholders": ["Planner", "production supervisor"],
        "updated": "daily / real-time on events",
        "agent_lead": ["A4", "A3", "A5"],
    },
}


def _health_bar(pct: float, width: int = 12) -> str:
    filled = round(pct / 100.0 * width)
    return "█" * filled + "░" * (width - filled)


def build_horizons(
    *,
    strategic: dict[str, Any] | None = None,
    tactical: dict[str, Any] | None = None,
    operational: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Three-Horizons view with per-horizon coverage health."""

    strategic = strategic or {
        "revenue_target_usd": 28_000_000,
        "growth_pct": 15.0,
        "capex_decision_quarter": "Q4",
        "npi_products": 2,
        "coverage_pct": 85.0,
        "pending_decisions": 2,
    }
    tactical = tactical or {
        "sop_cycle": "Aug",
        "consensus_pct": 94.0,
        "capacity_gap_month": "Oct",
        "supplier_risk_count": 1,
        "coverage_pct": 94.0,
        "pending_decisions": 0,
    }
    operational = operational or {
        "mos_active": 47,
        "mos_at_risk": 5,
        "capacity_pct": 88.0,
        "material_flags": 3,
        "coverage_pct": 89.0,
        "mrp_run_needed": True,
    }

    def _card(key: str, payload: dict[str, Any]) -> dict[str, Any]:
        cov = float(payload.get("coverage_pct", 0.0))
        pending = int(payload.get("pending_decisions", 0)) or (
            1 if payload.get("mrp_run_needed") else 0
        )
        status = "healthy" if cov >= 90 else "attention" if cov >= 80 else "critical"
        return {
            "horizon": key,
            **_HORIZON_META[key],
            "metrics": payload,
            "coverage_pct": round(cov, 1),
            "health_bar": _health_bar(cov),
            "status": status,
            "pending_decisions": pending,
        }

    cards = {
        "strategic": _card("strategic", strategic),
        "tactical": _card("tactical", tactical),
        "operational": _card("operational", operational),
    }
    overall = round(sum(c["coverage_pct"] for c in cards.values()) / 3.0, 1)
    return {
        "as_of": "2026-07-16",
        "horizons": cards,
        "overall_coverage_pct": overall,
        "attention": [
            {
                "horizon": k,
                "coverage_pct": c["coverage_pct"],
                "pending_decisions": c["pending_decisions"],
            }
            for k, c in cards.items()
            if c["status"] != "healthy"
        ],
    }


def cascade_plan(
    *,
    direction: str = "down",
    driver: str = "We will grow DT250 revenue by 20% in 2027",
    growth_pct: float = 20.0,
    product: str = "DT250",
    constraint_work_centre: str = "Winding",
    capacity_gap_hours: float = 800.0,
    capex_usd: float = 180_000.0,
    roi_months: float = 14.0,
) -> dict[str, Any]:
    """Cascade a strategic decision DOWN to tactical/operational, or escalate an
    operational constraint UP to tactical/strategic."""

    direction = direction.lower()
    if direction not in ("down", "up"):
        direction = "down"

    if direction == "down":
        tactical = [
            {
                "agent": "A6",
                "action": f"2027 S&OP must plan for {growth_pct:.0f}% more {product} production",
            },
            {
                "agent": "A3",
                "action": (
                    f"{constraint_work_centre} WC needs capacity increase — "
                    "2nd shift or new machine"
                ),
            },
            {
                "agent": "A2",
                "action": f"Copper wire annual commitment needs +{growth_pct:.0f}% with supplier",
            },
            {"agent": "A1", "action": f"Demand model should bias {product} forecast upward"},
        ]
        operational = [
            {"agent": "A3", "action": f"Q1 2027 MPS includes {growth_pct:.0f}% more {product}"},
            {
                "agent": "A9",
                "action": "Q4 2026 PO for additional copper wire to build safety stock",
            },
            {"agent": "A3", "action": "December training plan for WC-WND 2nd shift operators"},
        ]
        return {
            "direction": "down",
            "driver": driver,
            "cascades_to_tactical": tactical,
            "cascades_to_operational": operational,
            "traceable": True,
        }

    # direction == "up": constraint escalation
    return {
        "direction": "up",
        "operational_constraint": (
            f"{constraint_work_centre} WC physically cannot handle +{growth_pct:.0f}% "
            "without 2nd machine"
        ),
        "escalates_to_tactical": [
            {
                "agent": "A6",
                "action": (
                    f"S&OP supply review: capacity gap of {capacity_gap_hours:.0f} hours/year "
                    f"for {product} growth"
                ),
            },
            {
                "agent": "A11",
                "action": (
                    f"Capital investment: new {constraint_work_centre.lower()} machine "
                    f"${capex_usd:,.0f}, ROI {roi_months:.0f} months"
                ),
            },
        ],
        "escalates_to_strategic": [
            {
                "agent": "A17",
                "action": (
                    f"Board decision needed: approve ${capex_usd:,.0f} capex for {product} growth "
                    f"or revise growth target to {max(growth_pct - 8, 0):.0f}% "
                    "(achievable with current capacity)"
                ),
                "governance_level": 4,
            }
        ],
        "board_decision_required": True,
    }
