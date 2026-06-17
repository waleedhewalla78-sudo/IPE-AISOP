import math

G1_DEMAND_WEIGHT = 0.05
G2_BOM_WEIGHT = 0.05
G3_MATERIAL_WEIGHT = 0.35
G4_CAPACITY_WEIGHT = 0.30
G5_LABOR_WEIGHT = 0.25


def _resolve(v: float | None, default: float) -> float:
    if v is None or math.isnan(v) or math.isinf(v):
        return default
    return v


def calculate_feasibility(
    demand_score: float | None = None,
    bom_score: float | None = None,
    material_score: float | None = None,
    capacity_score: float | None = None,
    labor_score: float | None = None,
    autonomy_mode: str = "shadow",
) -> dict:
    demand_score = _resolve(demand_score, 100.0)
    bom_score = _resolve(bom_score, 100.0)
    material_score = _resolve(material_score, 50.0)
    capacity_score = _resolve(capacity_score, 50.0)
    labor_score = _resolve(labor_score, 50.0)

    def clamp(v: float) -> float:
        return max(0.0, min(100.0, v))

    g1 = clamp(demand_score)
    g2 = clamp(bom_score)
    g3 = clamp(material_score)
    g4 = clamp(capacity_score)
    g5 = clamp(labor_score)

    composite = (
        g1 * G1_DEMAND_WEIGHT
        + g2 * G2_BOM_WEIGHT
        + g3 * G3_MATERIAL_WEIGHT
        + g4 * G4_CAPACITY_WEIGHT
        + g5 * G5_LABOR_WEIGHT
    )

    score_rounded = round(composite, 2)

    gate_scores = {
        "demand": round(g1, 2),
        "bom": round(g2, 2),
        "material": round(g3, 2),
        "capacity": round(g4, 2),
        "labor": round(g5, 2),
    }

    gate_ranking = sorted(
        [("demand", g1), ("bom", g2), ("material", g3), ("capacity", g4), ("labor", g5)],
        key=lambda x: x[1],
    )
    primary_constraint = gate_ranking[0][0] if gate_ranking else None

    if autonomy_mode == "autonomous" and score_rounded >= 90.0:
        action_taken = "auto_confirmed"
    elif score_rounded >= 70.0:
        action_taken = "queued_for_planner"
    else:
        action_taken = "routed_to_resolution"

    return {
        "feasibility_score": score_rounded,
        "gate_scores": gate_scores,
        "primary_constraint": primary_constraint,
        "action_taken": action_taken,
        "is_feasible": score_rounded >= 50.0,
        "risk_level": (
            "low" if score_rounded >= 80.0
            else "medium" if score_rounded >= 50.0
            else "high"
        ),
    }
