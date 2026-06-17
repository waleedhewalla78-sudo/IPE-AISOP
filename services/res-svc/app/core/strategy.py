

STRATEGIES = {
    "material_shortage": [
        {"strategy": "expedite_supply", "description": "Expedite supplier order for component", "delivery_impact_days": -3, "cost_impact_mult": 1.15, "risk": "medium"},
        {"strategy": "substitute_material", "description": "Use approved substitute component", "delivery_impact_days": 0, "cost_impact_mult": 1.05, "risk": "low"},
        {"strategy": "split_batch", "description": "Split MO: produce what's available now, rest later", "delivery_impact_days": 2, "cost_impact_mult": 1.02, "risk": "low"},
        {"strategy": "reallocate_inventory", "description": "Reallocate inventory from lower-priority MO", "delivery_impact_days": 0, "cost_impact_mult": 1.0, "risk": "medium"},
    ],
    "capacity_overload": [
        {"strategy": "overtime", "description": "Add overtime shift to overloaded work center", "delivery_impact_days": 0, "cost_impact_mult": 1.5, "risk": "low"},
        {"strategy": "alternative_work_center", "description": "Reroute to alternative work center", "delivery_impact_days": 1, "cost_impact_mult": 1.1, "risk": "low"},
        {"strategy": "outsource_operation", "description": "Outsource operation to subcontractor", "delivery_impact_days": 2, "cost_impact_mult": 1.3, "risk": "medium"},
        {"strategy": "resequence", "description": "Resequence operations to balance load", "delivery_impact_days": 0, "cost_impact_mult": 1.0, "risk": "low"},
    ],
    "labor_absence": [
        {"strategy": "cross_training", "description": "Assign cross-trained operator from different line", "delivery_impact_days": 0, "cost_impact_mult": 1.1, "risk": "low"},
        {"strategy": "overtime_existing", "description": "Extend shift for remaining operators", "delivery_impact_days": 0, "cost_impact_mult": 1.5, "risk": "low"},
        {"strategy": "temporary_staff", "description": "Bring in temporary staff", "delivery_impact_days": 1, "cost_impact_mult": 1.25, "risk": "medium"},
    ],
    "supplier_delay": [
        {"strategy": "expedite_supply", "description": "Contact supplier for expedited delivery", "delivery_impact_days": -5, "cost_impact_mult": 1.2, "risk": "medium"},
        {"strategy": "alternate_supplier", "description": "Source from alternate qualified supplier", "delivery_impact_days": 3, "cost_impact_mult": 1.15, "risk": "medium"},
        {"strategy": "reschedule_production", "description": "Reschedule production to match delayed supply", "delivery_impact_days": 5, "cost_impact_mult": 1.0, "risk": "low"},
    ],
    "quality_issue": [
        {"strategy": "rework", "description": "Rework defective items in-house", "delivery_impact_days": 2, "cost_impact_mult": 1.1, "risk": "low"},
        {"strategy": "scrap_reorder", "description": "Scrap and reorder from supplier", "delivery_impact_days": 7, "cost_impact_mult": 1.2, "risk": "medium"},
        {"strategy": "relax_quality_threshold", "description": "Accept with variance if functionally equivalent", "delivery_impact_days": 0, "cost_impact_mult": 1.0, "risk": "high"},
    ],
    "maintenance": [
        {"strategy": "alternative_work_center", "description": "Reroute to alternative work center", "delivery_impact_days": 1, "cost_impact_mult": 1.1, "risk": "low"},
        {"strategy": "expedite_maintenance", "description": "Expedite maintenance crew", "delivery_impact_days": -1, "cost_impact_mult": 1.3, "risk": "low"},
        {"strategy": "outsource_operation", "description": "Outsource while work center is down", "delivery_impact_days": 2, "cost_impact_mult": 1.35, "risk": "medium"},
    ],
}

DEFAULT_STRATEGIES = [
    {"strategy": "reschedule", "description": "Reschedule MO to later date", "delivery_impact_days": 3, "cost_impact_mult": 1.0, "risk": "low"},
    {"strategy": "split_order", "description": "Split order into smaller batches", "delivery_impact_days": 1, "cost_impact_mult": 1.05, "risk": "low"},
    {"strategy": "cancel_order", "description": "Cancel MO with customer notification", "delivery_impact_days": 0, "cost_impact_mult": 0.0, "risk": "high"},
]


def generate_strategies(
    mo_id: str,
    constraint_type: str,
    mo_data: dict | None = None,
) -> list[dict]:
    strategies = STRATEGIES.get(constraint_type, DEFAULT_STRATEGIES)
    base_cost = 1000.0
    if mo_data:
        base_cost = float(mo_data.get("quantity", 1)) * 100.0

    result = []
    for s in strategies:
        cost_impact = round(base_cost * (s["cost_impact_mult"] - 1.0), 2)
        result.append({
            "strategy": s["strategy"],
            "description": s["description"],
            "delivery_impact_days": s["delivery_impact_days"],
            "cost_impact": cost_impact,
            "risk": s["risk"],
            "mo_id": mo_id,
        })

    return result
