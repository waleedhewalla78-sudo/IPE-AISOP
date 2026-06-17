from ipe_shared.constants import AutonomyMode

CONFIRM_THRESHOLDS: dict[str, float] = {
    AutonomyMode.SHADOW: 1.01,
    AutonomyMode.SUGGEST: 0.85,
    AutonomyMode.AUTONOMOUS: 0.70,
}


def should_auto_confirm(
    feasibility_score: float,
    autonomy_mode: str,
    primary_constraint: str | None = None,
) -> dict:
    threshold = CONFIRM_THRESHOLDS.get(autonomy_mode, 1.01)

    if autonomy_mode == AutonomyMode.SHADOW:
        return {
            "should_confirm": False,
            "reason": "Shadow mode: no auto-confirm",
            "threshold": threshold,
            "score": feasibility_score,
        }

    can_confirm = feasibility_score >= threshold

    if not can_confirm:
        return {
            "should_confirm": False,
            "reason": f"Score {feasibility_score:.2f} below threshold {threshold:.2f}",
            "threshold": threshold,
            "score": feasibility_score,
        }

    reasons = []
    if autonomy_mode == AutonomyMode.SUGGEST:
        reasons.append("Suggest mode: score above 0.85 threshold")
    elif autonomy_mode == AutonomyMode.AUTONOMOUS:
        reasons.append("Autonomous mode: score above 0.70 threshold")

    if primary_constraint:
        reasons.append(f"Primary constraint: {primary_constraint}")

    return {
        "should_confirm": True,
        "reason": "; ".join(reasons),
        "threshold": threshold,
        "score": feasibility_score,
    }
