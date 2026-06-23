from datetime import UTC, datetime

DEFAULT_WEIGHTS = {
    "customer": 0.25,
    "margin": 0.20,
    "urgency": 0.30,
    "strategic": 0.15,
    "penalty": 0.10,
}


def compute_priority_score(demand_line: dict, tenant_config: dict | None = None) -> dict:
    weights = DEFAULT_WEIGHTS.copy()
    if tenant_config and "priority_weights" in tenant_config:
        tw = tenant_config["priority_weights"]
        for k in weights:
            if k in tw:
                weights[k] = float(tw[k])
        total = sum(weights.values())
        if total > 0 and abs(total - 1.0) > 0.001:
            for k in weights:
                weights[k] /= total

    customer_tier = int(demand_line.get("customer_tier") or 3)
    customer_score = {1: 100.0, 2: 70.0, 3: 40.0}.get(customer_tier, 40.0)

    margin_pct = float(demand_line.get("margin_pct") or 0)
    margin_score = min(max(margin_pct, 0.0), 100.0)

    required_date = demand_line.get("required_date")
    if required_date:
        if isinstance(required_date, str):
            due = datetime.fromisoformat(required_date.replace("Z", "+00:00"))
        else:
            due = required_date
    else:
        due = datetime.now(UTC)
    days_until = (due - datetime.now(UTC)).total_seconds() / 86400.0
    urgency_score = min(100.0, (30.0 / max(days_until, 1.0)) * 100.0)

    tags = demand_line.get("tags") or demand_line.get("category_tags") or []
    strategic_score = 100.0 if "strategic" in tags else 40.0

    penalty_cost = float(demand_line.get("penalty_cost") or 0)
    penalty_score = min(100.0, (penalty_cost / 10000.0) * 100.0)

    priority = (
        customer_score * weights["customer"]
        + margin_score * weights["margin"]
        + urgency_score * weights["urgency"]
        + strategic_score * weights["strategic"]
        + penalty_score * weights["penalty"]
    )
    priority = round(min(max(priority, 0.0), 100.0), 4)

    breakdown = {
        "customer": round(customer_score, 4),
        "margin": round(margin_score, 4),
        "urgency": round(urgency_score, 4),
        "strategic": round(strategic_score, 4),
        "penalty": round(penalty_score, 4),
    }

    return {
        "priority_score": priority,
        "priority_breakdown": breakdown,
    }


def calculate_priority(demand_line: dict, tenant_config: dict | None = None) -> dict:
    """Legacy wrapper: delegates to compute_priority_score and adapts to test expectations."""
    result = compute_priority_score(demand_line, tenant_config)
    score = result["priority_score"]
    bd = result["priority_breakdown"]
    normalized = score / 100.0
    return {
        "priority_score": round(normalized, 4),
        "components": {
            "customer_tier": round(bd.get("customer", 0) / 100.0, 4),
            "urgency": round(bd.get("urgency", 0) / 100.0, 4),
            "margin": round(bd.get("margin", 0) / 100.0, 4),
            "penalty": round(bd.get("penalty", 0) / 100.0, 4),
            "strategic_product": round(bd.get("strategic", 0) / 100.0, 4),
            "quantity": 0.0,
        },
        "priority_breakdown": {
            "customer_tier": round(bd.get("customer", 0) / 100.0, 4),
            "urgency": round(bd.get("urgency", 0) / 100.0, 4),
            "penalty": round(bd.get("penalty", 0) / 100.0, 4),
            "margin": round(bd.get("margin", 0) / 100.0, 4),
            "strategic_product": round(bd.get("strategic", 0) / 100.0, 4),
            "quantity": 0.0,
        },
    }
