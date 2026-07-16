"""Phase 7 §5.5 — Standard Work Management (A16 step tracking).

Digital work instructions with per-step standard times, quality checkpoints, and
over-standard flagging (> 120%). Also surfaces continuous-improvement signals.
"""

from __future__ import annotations

from typing import Any

_DEFAULT_STEPS = [
    {
        "step": 1,
        "std_min": 5,
        "activity": "Setup wire spool",
        "checkpoint": "Correct gauge (4.0mm)",
        "sop_ref": "SOP-WND-001",
    },
    {
        "step": 2,
        "std_min": 5,
        "activity": "Thread wire through tensioner",
        "checkpoint": "Tension 15-18 N",
        "sop_ref": "SOP-WND-002",
    },
    {
        "step": 3,
        "std_min": 3,
        "activity": "Load core assembly",
        "checkpoint": "Core type verified",
        "sop_ref": "SOP-WND-003",
    },
    {
        "step": 4,
        "std_min": 180,
        "activity": "HV winding (360 turns)",
        "checkpoint": "Turn counter at 90/180/270",
        "sop_ref": "SOP-WND-004",
    },
    {
        "step": 5,
        "std_min": 10,
        "activity": "Insulation layer",
        "checkpoint": "No wrinkles, full coverage",
        "sop_ref": "SOP-WND-005",
    },
    {
        "step": 6,
        "std_min": 120,
        "activity": "LV winding (180 turns)",
        "checkpoint": "Turn counter at 60/120",
        "sop_ref": "SOP-WND-006",
    },
    {
        "step": 7,
        "std_min": 10,
        "activity": "Final insulation + tape",
        "checkpoint": "Tape overlap >= 50%",
        "sop_ref": "SOP-WND-007",
    },
    {
        "step": 8,
        "std_min": 5,
        "activity": "Visual inspection",
        "checkpoint": "No visible defects",
        "sop_ref": "SOP-WND-008",
    },
    {
        "step": 9,
        "std_min": 5,
        "activity": "Resistance measurement",
        "checkpoint": "Within +/-5% of spec",
        "sop_ref": "SOP-WND-009",
    },
    {
        "step": 10,
        "std_min": 2,
        "activity": "Log completion in IPE",
        "checkpoint": "MO status updated",
        "sop_ref": "—",
    },
]


def build_standard_work(
    *,
    operation: str = "DT250 Winding Operation",
    steps: list[dict[str, Any]] | None = None,
    actuals: dict[int, float] | None = None,
    over_standard_pct: float = 120.0,
) -> dict[str, Any]:
    """Return the standard-work sheet with A16 tracking against actuals."""

    steps = steps or _DEFAULT_STEPS
    actuals = actuals or {}

    tracked: list[dict[str, Any]] = []
    total_std = 0.0
    total_actual = 0.0
    over_flags: list[dict[str, Any]] = []
    for s in steps:
        std = float(s["std_min"])
        actual = float(actuals.get(s["step"], std))
        total_std += std
        total_actual += actual
        pct = round(actual / std * 100.0, 0) if std else 100.0
        over = pct > over_standard_pct
        node = {**s, "actual_min": actual, "pct_of_standard": pct, "over_standard": over}
        tracked.append(node)
        if over:
            over_flags.append(
                {"step": s["step"], "activity": s["activity"], "pct_of_standard": pct}
            )

    return {
        "operation": operation,
        "steps": tracked,
        "total_standard_min": total_std,
        "total_actual_min": total_actual,
        "over_standard_steps": over_flags,
        "a16_agent": {
            "displays_current_step": True,
            "tracks_time_per_step": True,
            "flags_over_120pct": True,
            "records_quality_checkpoints": True,
            "auto_advances_mo": True,
            "alerts_on_resistance_fail": True,
        },
        "continuous_improvement": [
            "Step 4 (HV winding) variance across operators → training opportunity",
            "Step 2 (threading) has most variance → SOP clarification needed",
            "Step 9 failure rate correlates with wire batch quality → feeds A10 prediction",
        ],
    }
