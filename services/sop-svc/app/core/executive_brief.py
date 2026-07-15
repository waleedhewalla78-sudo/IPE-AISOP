"""Auto-generated S&OP executive brief."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class SopExecutiveBrief:
    def generate(self, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        inputs = inputs or {}
        demand = inputs.get("demand") or {
            "consensus": 2_400_000,
            "mape": 14.2,
            "top_growth": ["DT100 +22%", "PT500 +8%"],
            "top_decline": ["DT250 -15%"],
        }
        supply = inputs.get("supply") or {
            "constrained_capacity": "Winding WC at 108%",
            "lost_sales": 300_000,
            "material_risk": "Copper wire lead time 12 days",
            "supplier_alert": "Cairo Copper reliability 68%",
        }
        finance = inputs.get("finance") or {
            "revenue_actual": 2_100_000,
            "revenue_plan": 2_300_000,
            "profit_actual": 680_000,
            "profit_plan": 750_000,
        }
        decisions = inputs.get("decisions") or [
            {
                "title": "Authorise Winding overtime",
                "cost": 7200,
                "benefit": 180000,
                "recommendation": "approve",
            },
            {
                "title": "Approve second copper supplier qualification",
                "cost": 3000,
                "benefit": 45000,
                "recommendation": "approve",
            },
            {
                "title": "Accept reduced DT250 forecast or launch Gulf marketing",
                "cost": 0,
                "benefit": 0,
                "recommendation": "discuss",
            },
        ]

        gap_rev = finance["revenue_actual"] - finance["revenue_plan"]
        gap_pct = gap_rev / finance["revenue_plan"] * 100 if finance["revenue_plan"] else 0

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "headline": "Revenue at risk — consensus demand exceeds capacity",
            "demand_review": demand,
            "supply_review": supply,
            "reconciliation": {
                "revenue_vs_aop": {
                    "actual": finance["revenue_actual"],
                    "plan": finance["revenue_plan"],
                    "gap": gap_rev,
                    "gap_pct": round(gap_pct, 1),
                },
                "profit_gap": finance["profit_actual"] - finance["profit_plan"],
            },
            "decisions_required": decisions,
            "management_recommendation": (
                "Approve overtime and second copper supplier. "
                "ROI on overtime exceeds 20:1; diversification reduces quarterly risk."
            ),
        }
