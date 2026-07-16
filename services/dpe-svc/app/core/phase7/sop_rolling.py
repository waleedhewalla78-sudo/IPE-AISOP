"""Phase 7 §2.2 — Rolling S&OP (event-driven recalc + monthly governance)."""

from __future__ import annotations

from typing import Any

# Event types that trigger a continuous (automatic) rolling recalculation.
_EVENT_RULES = {
    "large_order": {
        "threshold_usd": 100_000,
        "agent": "A6",
        "recalc": "consensus impact",
    },
    "supplier_failure": {"agent": "A6", "recalc": "constrained supply"},
    "forecast_update": {"agent": "A6", "recalc": "rolling consensus"},
    "capacity_change": {"agent": "A6", "recalc": "supply"},
}

_GOVERNANCE_STAGES = [
    {
        "stage": 1,
        "week": 1,
        "name": "demand_review",
        "owner": "A1+A6",
        "purpose": "Formalize accumulated rolling demand adjustments",
    },
    {
        "stage": 2,
        "week": 2,
        "name": "supply_review",
        "owner": "A3+A6",
        "purpose": "Capacity and material formal commitment",
    },
    {
        "stage": 3,
        "week": 3,
        "name": "reconciliation",
        "owner": "A6+A11",
        "purpose": "Financial P&L formal sign-off",
    },
    {
        "stage": 4,
        "week": 4,
        "name": "management_review",
        "owner": "A6+A7+A17",
        "purpose": "Strategic decisions only",
    },
]


def recalc_rolling_sop(
    *,
    events: list[dict[str, Any]] | None = None,
    baseline_consensus: float = 24.0,
) -> dict[str, Any]:
    """Apply event-driven adjustments to a rolling consensus and log the trail.

    Small adjustments require no meeting; the trend stays visible. Events carry an
    optional ``delta_units`` and ``value_usd``.
    """

    events = events or [
        {"type": "large_order", "ref": "SO-2026-0455", "value_usd": 140_000, "delta_units": 2},
        {"type": "forecast_update", "ref": "wk-29", "delta_units": -1},
    ]

    consensus = baseline_consensus
    log: list[dict[str, Any]] = []
    material_events = 0
    for ev in events:
        etype = ev.get("type", "forecast_update")
        rule = _EVENT_RULES.get(etype, _EVENT_RULES["forecast_update"])
        delta = float(ev.get("delta_units", 0.0))
        significant = etype == "large_order" and float(ev.get("value_usd", 0)) >= rule.get(
            "threshold_usd", 0
        )
        # A "significant" event flags for review; small ones auto-apply silently.
        requires_review = significant or etype in ("supplier_failure", "capacity_change")
        consensus += delta
        if requires_review:
            material_events += 1
        log.append(
            {
                "type": etype,
                "ref": ev.get("ref"),
                "agent": rule["agent"],
                "recalculated": rule["recalc"],
                "delta_units": delta,
                "new_consensus": round(consensus, 1),
                "requires_meeting": requires_review,
                "auto_applied": not requires_review,
            }
        )

    return {
        "mode": "rolling",
        "baseline_consensus": baseline_consensus,
        "current_consensus": round(consensus, 1),
        "event_log": log,
        "events_processed": len(log),
        "material_events_for_review": material_events,
        "governance_cycle": _GOVERNANCE_STAGES,
        "difference_vs_traditional": (
            "Adjustments detected and applied continuously; the monthly meeting confirms "
            "them and addresses strategic implications only."
        ),
    }
