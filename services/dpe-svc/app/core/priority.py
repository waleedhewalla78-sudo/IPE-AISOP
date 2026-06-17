from datetime import UTC, datetime, timedelta
from math import exp

DEFAULT_WEIGHTS = {
    "urgency": 0.30,
    "customer_tier": 0.20,
    "penalty": 0.20,
    "margin": 0.15,
    "strategic_product": 0.10,
    "quantity": 0.05,
}

STRATEGIC_PRODUCT_IDS: list[str] = []


def calculate_priority(demand: dict, tenant_config: dict | None = None) -> dict:
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

    due_date_str = demand.get("required_date") or demand.get("required_date")
    customer_tier = demand.get("customer_tier") or 3
    penalty_cost = float(demand.get("penalty_cost") or 0)
    margin_pct = float(demand.get("margin_pct") or 0)
    quantity = float(demand.get("quantity") or 1)
    product_id = str(demand.get("product_id") or "")

    if due_date_str:
        if isinstance(due_date_str, str):
            due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
        else:
            due_date = due_date_str
    else:
        due_date = datetime.now(UTC) + timedelta(days=30)

    now = datetime.now(UTC)
    days_until_due = (due_date - now).total_seconds() / 86400.0

    urgency_score = 1.0 / (1.0 + exp(-max(-days_until_due, -30) / 5.0))
    if days_until_due <= 0:
        urgency_score = 1.0
    elif days_until_due <= 3:
        urgency_score = 0.95
    elif days_until_due <= 7:
        urgency_score = 0.80
    elif days_until_due <= 14:
        urgency_score = 0.60
    elif days_until_due <= 30:
        urgency_score = 0.40
    else:
        urgency_score = 0.20

    tier_score = max(0, (4 - (customer_tier or 3))) / 3.0

    penalty_score = min(penalty_cost / 50000.0, 1.0)

    margin_score = min(margin_pct / 50.0, 1.0) if margin_pct else 0.3

    strategic_ids = STRATEGIC_PRODUCT_IDS
    if tenant_config and "strategic_product_ids" in tenant_config:
        strategic_ids = tenant_config["strategic_product_ids"]
    strategic_score = 1.0 if product_id in strategic_ids else 0.0

    quantity_score = min(quantity / 10000.0, 1.0)

    priority = (
        urgency_score * weights["urgency"]
        + tier_score * weights["customer_tier"]
        + penalty_score * weights["penalty"]
        + margin_score * weights["margin"]
        + strategic_score * weights["strategic_product"]
        + quantity_score * weights["quantity"]
    )
    priority = round(min(max(priority, 0.0), 1.0), 4)

    breakdown = {
        "urgency": round(urgency_score * weights["urgency"], 4),
        "customer_tier": round(tier_score * weights["customer_tier"], 4),
        "penalty": round(penalty_score * weights["penalty"], 4),
        "margin": round(margin_score * weights["margin"], 4),
        "strategic_product": round(strategic_score * weights["strategic_product"], 4),
        "quantity": round(quantity_score * weights["quantity"], 4),
    }

    components = {
        "urgency": round(urgency_score, 4),
        "customer_tier": round(tier_score, 4),
        "penalty": round(penalty_score, 4),
        "margin": round(margin_score, 4),
        "strategic_product": round(strategic_score, 4),
        "quantity": round(quantity_score, 4),
    }

    return {
        "priority_score": priority,
        "components": components,
        "priority_breakdown": breakdown,
        "days_until_due": round(days_until_due, 1),
    }
