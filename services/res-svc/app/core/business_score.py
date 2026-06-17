def score_scenario(
    scenario: dict,
    customer_tier: int = 3,
    penalty_cost: float = 0,
) -> dict:
    delivery_impact = scenario.get("delivery_impact_days", 0)
    cost_impact = float(scenario.get("cost_impact", 0))
    risk = scenario.get("risk", "medium")

    if delivery_impact <= 0:
        delivery_score = 1.0
    elif delivery_impact <= 2:
        delivery_score = 0.8
    elif delivery_impact <= 5:
        delivery_score = 0.5
    else:
        delivery_score = 0.2

    penalty_avoided = min(cost_impact / max(penalty_cost, 1), 1.0) if penalty_cost > 0 else 0.5
    cost_score = 1.0 - min(cost_impact / 10000.0, 1.0)

    risk_map = {"low": 1.0, "medium": 0.6, "high": 0.2}
    risk_score = risk_map.get(risk, 0.5)

    tier_score = max(0, (4 - customer_tier)) / 3.0

    business_score = (
        delivery_score * 0.35
        + cost_score * 0.25
        + risk_score * 0.20
        + penalty_avoided * 0.10
        + tier_score * 0.10
    )
    business_score = round(min(max(business_score, 0), 1.0), 4)

    return {
        "business_score": business_score,
        "components": {
            "delivery": round(delivery_score, 4),
            "cost": round(cost_score, 4),
            "risk": round(risk_score, 4),
            "penalty_avoidance": round(penalty_avoided, 4),
            "customer_tier": round(tier_score, 4),
        },
        "is_recommended": business_score >= 0.6,
    }
