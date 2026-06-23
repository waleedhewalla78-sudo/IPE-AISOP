from __future__ import annotations

RECYCLING_INFRASTRUCTURE: dict[str, float] = {
    "EU": 0.85,
    "US": 0.70,
    "APAC": 0.55,
    "default": 0.60,
}

HAZARDOUS_MATERIALS: set[str] = {
    "lead", "mercury", "cadmium", "hexavalent_chromium",
    "pbb", "pbde", "asbestos", "formaldehyde",
}

MATERIAL_RECYCLABILITY: dict[str, float] = {
    "steel": 0.92,
    "aluminum": 0.88,
    "copper": 0.85,
    "gold": 0.95,
    "silver": 0.93,
    "plastic_pet": 0.45,
    "plastic_hdpe": 0.40,
    "plastic_pvc": 0.20,
    "glass": 0.65,
    "rubber": 0.35,
    "wood": 0.55,
    "paper": 0.70,
    "textile": 0.25,
    "electronics_pcb": 0.50,
    "carbon_fiber": 0.15,
    "default": 0.40,
}


def calculate_recyclability_score(
    product_id: str,
    bom_components: list[dict],
) -> dict:
    if not bom_components:
        bom_components = [
            {"material": "steel", "weight_kg": 5.0, "hazardous": False, "disassembly_steps": 2},
            {"material": "plastic_pvc", "weight_kg": 1.5, "hazardous": False, "disassembly_steps": 3},
            {"material": "copper", "weight_kg": 0.8, "hazardous": False, "disassembly_steps": 4},
            {"material": "electronics_pcb", "weight_kg": 0.3, "hazardous": True, "disassembly_steps": 6},
        ]

    total_weight = sum(c.get("weight_kg", 1.0) for c in bom_components)
    if total_weight == 0:
        total_weight = 1.0

    material_score = 0.0
    disassembly_score = 0.0
    hazardous_penalty = 0.0
    breakdown = []

    for comp in bom_components:
        material = comp.get("material", "default").lower()
        weight = comp.get("weight_kg", 1.0)
        is_hazardous = comp.get("hazardous", False)
        disassembly_steps = comp.get("disassembly_steps", 3)

        recyclability_pct = MATERIAL_RECYCLABILITY.get(material, MATERIAL_RECYCLABILITY["default"]) * 100
        weight_fraction = weight / total_weight

        material_score += recyclability_pct * weight_fraction

        step_score = max(0, 100 - (disassembly_steps - 1) * 15)
        disassembly_score += step_score * weight_fraction

        if is_hazardous:
            hazardous_penalty += 20 * weight_fraction
        elif material in HAZARDOUS_MATERIALS:
            hazardous_penalty += 15 * weight_fraction

        breakdown.append({
            "material": material,
            "weight_kg": weight,
            "recyclability_pct": round(recyclability_pct, 2),
            "disassembly_steps": disassembly_steps,
            "hazardous": is_hazardous,
            "component_score": round(recyclability_pct * 0.5 + step_score * 0.3 - (20 if is_hazardous else 0) * weight_fraction, 2),
        })

    infrastructure_score = RECYCLING_INFRASTRUCTURE.get("EU", 0.60) * 100

    raw_score = material_score * 0.50 + disassembly_score * 0.25 + infrastructure_score * 0.15 + hazardous_penalty * (-0.10)
    final_score = max(0, min(100, raw_score))

    grade = "A" if final_score >= 80 else "B" if final_score >= 60 else "C" if final_score >= 40 else "D" if final_score >= 20 else "F"

    recommendations = []
    if disassembly_score < 60:
        recommendations.append("Reduce disassembly complexity to improve end-of-life processing")
    if hazardous_penalty > 0:
        recommendations.append("Substitute hazardous materials with safer alternatives")
    if material_score < 70:
        recommendations.append("Increase use of highly recyclable materials (steel, aluminum)")
    if len(recommendations) == 0:
        recommendations.append("Product meets recyclability standards")

    return {
        "score": round(final_score, 2),
        "grade": grade,
        "material_composition_score": round(material_score, 2),
        "disassembly_complexity_score": round(disassembly_score, 2),
        "infrastructure_availability_score": round(infrastructure_score, 2),
        "hazardous_material_penalty": round(hazardous_penalty, 2),
        "breakdown": breakdown,
        "recommendations": recommendations,
    }