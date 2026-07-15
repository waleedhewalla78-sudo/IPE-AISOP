"""A12 carbon footprint + supplier ESG helpers."""

from __future__ import annotations

from typing import Any


DEFAULT_FACTORS_KG_CO2E_PER_KG = {
    "copper": 4.5,
    "silicon_steel": 2.1,
    "insulation": 3.2,
    "steel": 1.8,
    "aluminum": 8.0,
    "default": 2.5,
}

PROCESS_KWH = {
    "winding": 65,
    "assembly": 45,
    "testing": 40,
    "finishing": 30,
}
KWH_TO_CO2E = 0.45  # kg CO2e / kWh grid mix


def calculate_product_carbon(
    product_id: str,
    *,
    materials: list[dict[str, Any]] | None = None,
    processes: list[str] | None = None,
    transport_kg_co2e: float = 320.0,
    industry_benchmark: float | None = 2100.0,
) -> dict[str, Any]:
    materials = materials or [
        {"name": "copper_wire", "material": "copper", "weight_kg": 151},
        {"name": "silicon_steel", "material": "silicon_steel", "weight_kg": 200},
        {"name": "insulation", "material": "insulation", "weight_kg": 26.5},
        {"name": "other", "material": "default", "weight_kg": 22},
    ]
    processes = processes or list(PROCESS_KWH.keys())

    material_breakdown = []
    material_total = 0.0
    for m in materials:
        factor = DEFAULT_FACTORS_KG_CO2E_PER_KG.get(str(m.get("material", "default")).lower(), DEFAULT_FACTORS_KG_CO2E_PER_KG["default"])
        kg = float(m.get("weight_kg", 0))
        co2 = round(kg * factor, 1)
        material_total += co2
        material_breakdown.append({"name": m.get("name"), "kg_co2e": co2})

    process_breakdown = []
    production_total = 0.0
    for p in processes:
        kwh = PROCESS_KWH.get(p, 20)
        co2 = round(kwh * KWH_TO_CO2E, 1)
        production_total += co2
        process_breakdown.append({"process": p, "kg_co2e": co2})

    total = round(material_total + production_total + transport_kg_co2e, 1)
    vs_bench = None
    if industry_benchmark:
        vs_bench = round((industry_benchmark - total) / industry_benchmark * 100, 1)

    return {
        "agent_id": "A12",
        "product_id": product_id,
        "material_carbon_kg_co2e": round(material_total, 1),
        "material_breakdown": material_breakdown,
        "production_carbon_kg_co2e": round(production_total, 1),
        "process_breakdown": process_breakdown,
        "transport_carbon_kg_co2e": transport_kg_co2e,
        "total_kg_co2e": total,
        "industry_benchmark_kg_co2e": industry_benchmark,
        "better_than_average_pct": vs_bench,
        "reduction_opportunities": [
            {"action": "Switch to recycled copper", "delta_kg_co2e": -280},
            {"action": "Source steel regionally", "delta_kg_co2e": -180},
            {"action": "Rooftop solar allocation", "delta_kg_co2e": -35},
        ],
    }


def score_supplier_esg(
    supplier_name: str,
    *,
    environmental: float = 50,
    social: float = 50,
    governance: float = 50,
) -> dict[str, Any]:
    overall = round((environmental + social + governance) / 3, 1)
    flag = "ok" if overall >= 70 else ("watch" if overall >= 55 else "risk")
    return {
        "agent_id": "A12",
        "supplier": supplier_name,
        "environmental": environmental,
        "social": social,
        "governance": governance,
        "overall_esg": overall,
        "flag": flag,
    }
