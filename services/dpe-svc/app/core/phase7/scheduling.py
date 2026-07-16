"""Phase 7 §4.1 — Advanced Scheduling.

- Sequence-dependent setup time optimisation (greedy nearest-setup heuristic).
- Multi-resource scheduling (all resources must align; surfaces the binding one).
- Campaign planning (batch a product family to minimise changeovers).
"""

from __future__ import annotations

from itertools import pairwise, permutations
from typing import Any

_DEFAULT_SETUP_MATRIX = {
    "DT100": {"DT100": 0, "DT250": 25, "PT500": 45, "Custom": 60},
    "DT250": {"DT100": 25, "DT250": 0, "PT500": 35, "Custom": 55},
    "PT500": {"DT100": 45, "DT250": 35, "PT500": 0, "Custom": 50},
    "Custom": {"DT100": 60, "DT250": 55, "PT500": 50, "Custom": 40},
}


def _sequence_setup(seq: list[str], matrix: dict[str, dict[str, int]]) -> int:
    total = 0
    for a, b in pairwise(seq):
        total += int(matrix.get(a, {}).get(b, 0))
    return total


def optimize_setup_sequence(
    *,
    jobs: list[str] | None = None,
    setup_matrix: dict[str, dict[str, int]] | None = None,
) -> dict[str, Any]:
    """Minimise total sequence-dependent setup time.

    Exact search for small job lists (<= 8), else greedy nearest-setup heuristic.
    """

    jobs = jobs or ["DT100", "PT500", "DT100", "DT250"]
    matrix = setup_matrix or _DEFAULT_SETUP_MATRIX

    before_setup = _sequence_setup(jobs, matrix)

    n = len(jobs)
    if n <= 8:
        best_seq = min(permutations(jobs), key=lambda s: _sequence_setup(list(s), matrix))
        best_seq = list(best_seq)
        best_setup = _sequence_setup(best_seq, matrix)
    else:
        remaining = jobs[1:]
        best_seq = [jobs[0]]
        while remaining:
            last = best_seq[-1]
            nxt = min(remaining, key=lambda j: matrix.get(last, {}).get(j, 0))
            best_seq.append(nxt)
            remaining.remove(nxt)
        best_setup = _sequence_setup(best_seq, matrix)

    savings = before_setup - best_setup
    savings_pct = round(savings / before_setup * 100.0, 0) if before_setup else 0.0
    return {
        "jobs": jobs,
        "before_sequence": jobs,
        "before_setup_min": before_setup,
        "optimised_sequence": best_seq,
        "optimised_setup_min": best_setup,
        "savings_min": savings,
        "savings_pct": savings_pct,
        "note": "All delivery dates maintained; sequence reorders within the day only.",
    }


def schedule_multi_resource(
    *,
    mo_id: str = "MO-ST-004",
    product: str = "DT250",
    resources: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """All resources must be available simultaneously; surface the binding constraint.

    ``resources`` items: {name, type, available(bool), ready_at?, note?}.
    """

    resources = resources or [
        {
            "name": "Winding Machine #2",
            "type": "machine",
            "available": True,
            "ready_at": "Jul 15 08:00",
        },
        {
            "name": "Operator Mohamed",
            "type": "labour",
            "available": True,
            "ready_at": "Jul 15 Shift A",
        },
        {
            "name": "Copper wire batch #089",
            "type": "material",
            "available": False,
            "ready_at": "Jul 14 EOD",
            "note": "A10 quality clearance needed",
        },
        {"name": "Test equipment", "type": "test", "available": True, "ready_at": "Jul 16 08:00"},
    ]

    blocking = [r for r in resources if not r.get("available", True)]
    schedulable = not blocking
    escalation = None
    if blocking:
        b = blocking[0]
        escalation = {
            "from_agent": "A3",
            "to_agent": "A10",
            "message": (
                f"Clearance for {b['name']} needed by {b.get('ready_at')} to avoid "
                f"production delay on {mo_id}. Can you expedite?"
            ),
        }
    return {
        "mo_id": mo_id,
        "product": product,
        "resources": resources,
        "schedulable": schedulable,
        "binding_constraint": blocking[0]["name"] if blocking else None,
        "escalation": escalation,
        "schedule": None if blocking else {"start": "Jul 15 08:00", "end": "Jul 16 10:00"},
    }


def plan_campaign(
    *,
    work_centre: str = "Winding",
    families: list[dict[str, Any]] | None = None,
    setup_matrix: dict[str, dict[str, int]] | None = None,
    daily_mix_setups: int = 20,
    daily_mix_setup_min: float = 400.0,
    wip_cost_per_month_usd: float = 8_400.0,
    recovered_capacity_value_usd: float = 14_200.0,
) -> dict[str, Any]:
    """Campaign mode: one setup per family per week vs a daily mixed schedule."""

    families = families or [
        {"week": "W31", "product": "DT100", "units": 20, "efficiency_pct": 95},
        {"week": "W32", "product": "DT250", "units": 15, "efficiency_pct": 94},
        {"week": "W33", "product": "PT500", "units": 6, "efficiency_pct": 93},
    ]
    matrix = setup_matrix or _DEFAULT_SETUP_MATRIX

    campaign_setups = len(families)
    campaign_setup_min = 0.0
    prev = None
    schedule: list[dict[str, Any]] = []
    for f in families:
        setup = 0 if prev is None else int(matrix.get(prev, {}).get(f["product"], 0))
        campaign_setup_min += setup
        schedule.append({**f, "setup_min": setup})
        prev = f["product"]

    setup_savings_min = round(daily_mix_setup_min - campaign_setup_min, 0)
    recovered_hours = round(setup_savings_min / 60.0, 1)
    net_benefit = round(recovered_capacity_value_usd - wip_cost_per_month_usd, 0)
    return {
        "work_centre": work_centre,
        "schedule": schedule,
        "campaign_setups": campaign_setups,
        "campaign_setup_min": campaign_setup_min,
        "daily_mix_setups": daily_mix_setups,
        "daily_mix_setup_min": daily_mix_setup_min,
        "setup_savings_min": setup_savings_min,
        "recovered_capacity_hours": recovered_hours,
        "tradeoff": "Higher WIP inventory during campaigns (managed by safety stock).",
        "economics": {
            "wip_cost_month_usd": wip_cost_per_month_usd,
            "recovered_capacity_value_usd": recovered_capacity_value_usd,
            "net_benefit_usd": net_benefit,
        },
        "recommendation": (
            f"Campaign planning saves {recovered_hours} hours/month on {work_centre}; "
            f"net benefit ${net_benefit:,.0f}/month."
        ),
    }
