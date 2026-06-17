

def classify_demand_type(
    product_data: dict | None = None,
    customer_tier: int | None = None,
    is_engineered: bool = False,
    is_customized: bool = False,
) -> dict:
    if product_data is None:
        product_data = {}

    source_type = product_data.get("source_type", "manufactured")
    _lead_time_days = product_data.get("lead_time_days") or 0
    safety_stock = product_data.get("safety_stock") or 0
    demand_cv = product_data.get("demand_cv")

    if is_engineered:
        demand_type = "ETO"
        confidence = 0.95
        reason = "Engineer-to-order: customer-engineered product"
    elif is_customized:
        demand_type = "CTO"
        confidence = 0.90
        reason = "Configure-to-order: customer-configured options"
    elif customer_tier is not None and customer_tier <= 2:
        demand_type = "MTO"
        confidence = 0.80
        reason = f"Make-to-order: tier {customer_tier} customer"
    elif source_type == "purchased" or source_type == "subcontracted":
        demand_type = "MTO"
        confidence = 0.75
        reason = "Make-to-order: purchased/subcontracted product"
    elif safety_stock and float(safety_stock) > 0:
        demand_type = "MTS"
        confidence = 0.85
        reason = "Make-to-stock: safety stock configured"
    elif demand_cv is not None and float(demand_cv) < 0.5:
        demand_type = "MTS"
        confidence = 0.70
        reason = "Make-to-stock: low demand variability"
    else:
        demand_type = "MTO"
        confidence = 0.60
        reason = "Make-to-order: default classification"

    return {
        "demand_type": demand_type,
        "confidence": round(confidence, 4),
        "reason": reason,
    }
