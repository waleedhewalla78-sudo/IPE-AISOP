from __future__ import annotations

MATERIAL_RECOVERY_RATES: dict[str, float] = {
    "steel": 0.92,
    "aluminum": 0.88,
    "copper": 0.85,
    "plastic": 0.30,
    "glass": 0.65,
    "paper": 0.70,
    "electronics": 0.50,
    "rubber": 0.35,
    "wood": 0.55,
    "textile": 0.25,
    "default": 0.40,
}

DISASSEMBLY_COST_PER_COMPONENT: dict[str, float] = {
    "screw": 0.02,
    "bolt": 0.03,
    "snap_fit": 0.01,
    "adhesive": 0.15,
    "welded": 0.25,
    "soldered": 0.10,
    "default": 0.05,
}


def calculate_circularity_score(
    product_id: str,
    bom_components: list[dict],
) -> dict:
    if not bom_components:
        bom_components = [
            {"material": "steel", "weight_kg": 5.0, "recyclable_pct": 92, "join_type": "bolt"},
            {"material": "plastic", "weight_kg": 2.0, "recyclable_pct": 30, "join_type": "snap_fit"},
            {"material": "copper", "weight_kg": 0.5, "recyclable_pct": 85, "join_type": "soldered"},
            {"material": "electronics", "weight_kg": 1.0, "recyclable_pct": 50, "join_type": "adhesive"},
        ]

    total_weight = sum(c.get("weight_kg", 1.0) for c in bom_components)
    if total_weight == 0:
        total_weight = 1.0

    material_recovery_total = 0.0
    disassembly_cost_total = 0.0

    for comp in bom_components:
        material = comp.get("material", "default").lower()
        weight = comp.get("weight_kg", 1.0)
        recyclable_pct_override = comp.get("recyclable_pct")
        join_type = comp.get("join_type", "default").lower()

        recovery_rate = recyclable_pct_override / 100.0 if recyclable_pct_override is not None else MATERIAL_RECOVERY_RATES.get(material, MATERIAL_RECOVERY_RATES["default"])
        material_recovery_total += weight * recovery_rate

        disassembly_cost = DISASSEMBLY_COST_PER_COMPONENT.get(join_type, DISASSEMBLY_COST_PER_COMPONENT["default"])
        disassembly_cost_total += disassembly_cost * weight

    material_recovery_pct = (material_recovery_total / total_weight) * 100

    take_back_eligible = material_recovery_pct > 50

    circularity_score = min(100, material_recovery_pct * 0.7 + (20 if take_back_eligible else 0) + (10 if disassembly_cost_total < 2.0 else 0))

    return {
        "circularity_score": round(circularity_score, 2),
        "material_recovery_pct": round(material_recovery_pct, 2),
        "take_back_eligible": take_back_eligible,
        "disassembly_cost_total": round(disassembly_cost_total, 2),
        "component_count": len(bom_components),
        "total_weight_kg": round(total_weight, 2),
    }