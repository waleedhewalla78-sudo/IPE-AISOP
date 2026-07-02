"""Material recommendation and design rule checking."""

from __future__ import annotations

DEFAULT_CATALOG = [
    {
        "name": "Aluminum 6061-T6",
        "grade": "6061-T6",
        "category": "metal",
        "properties_jsonb": {"tensile_mpa": 310, "yield_mpa": 276, "density_g_cm3": 2.7},
        "cost_per_kg": 3.2,
        "sustainability_score": 72,
    },
    {
        "name": "Stainless Steel 316L",
        "grade": "316L",
        "category": "metal",
        "properties_jsonb": {"tensile_mpa": 515, "yield_mpa": 205, "density_g_cm3": 8.0},
        "cost_per_kg": 4.8,
        "sustainability_score": 65,
    },
    {
        "name": "ABS Polymer",
        "grade": "ABS-GF30",
        "category": "polymer",
        "properties_jsonb": {"tensile_mpa": 90, "yield_mpa": 65, "density_g_cm3": 1.4},
        "cost_per_kg": 2.1,
        "sustainability_score": 45,
    },
    {
        "name": "Titanium Ti-6Al-4V",
        "grade": "Ti-6Al-4V",
        "category": "metal",
        "properties_jsonb": {"tensile_mpa": 950, "yield_mpa": 880, "density_g_cm3": 4.43},
        "cost_per_kg": 35.0,
        "sustainability_score": 58,
    },
    {
        "name": "Polycarbonate",
        "grade": "PC-UV",
        "category": "polymer",
        "properties_jsonb": {"tensile_mpa": 65, "yield_mpa": 62, "density_g_cm3": 1.2},
        "cost_per_kg": 2.8,
        "sustainability_score": 50,
    },
]

DEFAULT_RULES = [
    {"process_type": "machining", "constraint_type": "hardness", "parameter_key": "max_hardness_hrc", "max_value": 45, "unit": "HRC"},
    {"process_type": "injection_molding", "constraint_type": "melt_temp", "parameter_key": "melt_temp_c", "min_value": 200, "max_value": 320, "unit": "C"},
    {"process_type": "sheet_metal", "constraint_type": "thickness", "parameter_key": "thickness_mm", "min_value": 0.5, "max_value": 6.0, "unit": "mm"},
]


def score_material(material: dict, *, required_tensile_mpa: float, max_cost_per_kg: float | None) -> float:
    props = material.get("properties_jsonb") or {}
    tensile = float(props.get("tensile_mpa", 0))
    cost = float(material.get("cost_per_kg", 0))
    sustain = float(material.get("sustainability_score", 50))
    strength_fit = min(1.0, tensile / max(required_tensile_mpa, 1.0))
    cost_fit = 1.0 if max_cost_per_kg is None or cost <= max_cost_per_kg else max(0.0, 1.0 - (cost - max_cost_per_kg) / max_cost_per_kg)
    return round(strength_fit * 0.5 + cost_fit * 0.3 + (sustain / 100) * 0.2, 4)


def recommend_materials(materials: list[dict], *, required_tensile_mpa: float, max_cost_per_kg: float | None, top_n: int = 5) -> list[dict]:
    ranked = []
    for m in materials:
        score = score_material(m, required_tensile_mpa=required_tensile_mpa, max_cost_per_kg=max_cost_per_kg)
        ranked.append({**m, "score": score, "rationale": f"Tensile {m.get('properties_jsonb', {}).get('tensile_mpa')} MPa vs required {required_tensile_mpa}"})
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:top_n]


def check_design_compliance(rules: list[dict], process_type: str, parameters: dict[str, float]) -> list[dict]:
    results = []
    for rule in rules:
        if rule.get("process_type") != process_type:
            continue
        key = rule["parameter_key"]
        if key not in parameters:
            results.append({"rule": key, "result": "skip", "message": "Parameter not provided"})
            continue
        val = parameters[key]
        ok = True
        if rule.get("min_value") is not None and val < float(rule["min_value"]):
            ok = False
        if rule.get("max_value") is not None and val > float(rule["max_value"]):
            ok = False
        results.append({"rule": key, "result": "pass" if ok else "fail", "value": val, "unit": rule.get("unit")})
    return results
