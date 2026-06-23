from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DefectPrediction:
    mo_id: str
    defect_probability: float
    risk_level: str
    contributing_factors: dict[str, float]
    recommended_actions: list[str]


QUALITY_RULES: dict[str, dict] = {
    "weld_defect": {
        "work_centers": ["wc-weld-01", "wc-weld-02"],
        "shifts": ["night"],
        "operators_with_high_defect_rate": ["op-003"],
        "base_probability": 0.15,
        "factor_multipliers": {"night_shift": 1.4, "high_defect_operator": 1.8, "overdue_maintenance": 1.3},
    },
    "surface_finish": {
        "work_centers": ["wc-cnc-01", "wc-cnc-02"],
        "shifts": [],
        "operators_with_high_defect_rate": [],
        "base_probability": 0.08,
        "factor_multipliers": {"dull_tool": 1.5, "contaminated_coolant": 1.3},
    },
    "dimensional": {
        "work_centers": ["wc-cnc-01", "wc-inspection-01"],
        "shifts": ["night"],
        "operators_with_high_defect_rate": ["op-007"],
        "base_probability": 0.12,
        "factor_multipliers": {"night_shift": 1.3, "high_defect_operator": 1.6, "tool_wear": 1.4},
    },
}


def predict_defect(
    mo_id: str,
    operation_type: str | None = None,
    work_center_id: str | None = None,
    shift: str | None = None,
    operator_id: str | None = None,
    material_batch: str | None = None,
    days_since_maintenance: int | None = None,
) -> DefectPrediction:
    total_probability = 0.0
    all_factors: dict[str, float] = {}
    matching_rules: list[str] = []

    for rule_name, rule in QUALITY_RULES.items():
        if operation_type and rule_name != operation_type:
            if not any(wc in (work_center_id or "") for wc in rule.get("work_centers", [])):
                continue

        prob = rule["base_probability"]
        factors: dict[str, float] = {}

        if shift == "night" and "night_shift" in rule["factor_multipliers"]:
            prob *= rule["factor_multipliers"]["night_shift"]
            factors["night_shift"] = rule["factor_multipliers"]["night_shift"]

        if operator_id and operator_id in rule.get("operators_with_high_defect_rate", []):
            if "high_defect_operator" in rule["factor_multipliers"]:
                prob *= rule["factor_multipliers"]["high_defect_operator"]
                factors["high_defect_operator"] = rule["factor_multipliers"]["high_defect_operator"]

        if days_since_maintenance and days_since_maintenance > 30:
            if "overdue_maintenance" in rule["factor_multipliers"]:
                prob *= rule["factor_multipliers"]["overdue_maintenance"]
                factors["overdue_maintenance"] = rule["factor_multipliers"]["overdue_maintenance"]

        if work_center_id and work_center_id in rule.get("work_centers", []):
            matching_rules.append(rule_name)

        total_probability += prob
        all_factors.update(factors)

    total_probability = min(1.0, total_probability)

    if total_probability > 0.7:
        risk_level = "high"
    elif total_probability > 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    recommended_actions = []
    if total_probability > 0.5:
        recommended_actions.append("Schedule additional quality inspection before next operation")
    if shift == "night":
        recommended_actions.append("Consider moving operation to day shift for better quality")
    if days_since_maintenance and days_since_maintenance > 30:
        recommended_actions.append("Schedule preventive maintenance before continuing production")
    if total_probability > 0.7:
        recommended_actions.append("Escalate to quality manager for decision on production hold")

    return DefectPrediction(
        mo_id=mo_id,
        defect_probability=round(total_probability, 4),
        risk_level=risk_level,
        contributing_factors=dict(sorted(all_factors.items())),
        recommended_actions=recommended_actions,
    )