from __future__ import annotations

from datetime import UTC, datetime, timedelta

REGULATORY_PHASE_OUT: dict[str, dict] = {
    "EU": {"rohs": True, "weee": True, "reach": True, "conflict_minerals": True},
    "US": {"rohs": False, "weee": False, "reach": False, "conflict_minerals": True},
    "APAC": {"rohs": True, "weee": False, "reach": False, "conflict_minerals": False},
}

COMPONENT_OBSOLESCENCE: dict[str, float] = {
    "semiconductor": 0.85,
    "capacitor": 0.60,
    "resistor": 0.40,
    "connector": 0.50,
    "motor": 0.30,
    "pump": 0.35,
    "sensor": 0.70,
    "default": 0.50,
}


def calculate_eol_plan(
    product_id: str,
    regulatory_region: str = "EU",
) -> dict:
    region_rules = REGULATORY_PHASE_OUT.get(regulatory_region, REGULATORY_PHASE_OUT["EU"])

    now = datetime.now(UTC)
    predicted_eol_date = now + timedelta(days=730)
    phase_out_date = predicted_eol_date + timedelta(days=180)

    default_components = [
        {"component": "semiconductor", "obsolescence_score": 0.85, "months_until_eol": 18},
        {"component": "capacitor", "obsolescence_score": 0.60, "months_until_eol": 36},
        {"component": "motor", "obsolescence_score": 0.30, "months_until_eol": 60},
        {"component": "sensor", "obsolescence_score": 0.70, "months_until_eol": 24},
    ]

    eol_risk_score = 0.0
    for comp in default_components:
        obs_score = comp["obsolescence_score"]
        eol_risk_score += obs_score * 25

    eol_risk_score = min(100, eol_risk_score)

    alternative_sourcing = []
    if eol_risk_score > 50:
        alternative_sourcing = [
            {"component": "semiconductor", "alternative_supplier": "Secondary Supplier A", "lead_time_days": 30, "cost_premium_pct": 15},
            {"component": "sensor", "alternative_supplier": "Regional Distributor B", "lead_time_days": 14, "cost_premium_pct": 8},
        ]

    phase_out_timeline = {
        "current_phase": "active" if eol_risk_score < 40 else ("transition" if eol_risk_score < 70 else "phase_out"),
        "predicted_eol_date": predicted_eol_date.isoformat(),
        "phase_out_date": phase_out_date.isoformat(),
        "regulatory_notices": [],
    }

    if region_rules.get("rohs"):
        phase_out_timeline["regulatory_notices"].append("RoHS compliance review required before EOL")
    if region_rules.get("weee"):
        phase_out_timeline["regulatory_notices"].append("WEEE disposal plan required at EOL")
    if region_rules.get("reach"):
        phase_out_timeline["regulatory_notices"].append("REACH substance declaration update required")

    return {
        "eol_risk_score": round(eol_risk_score, 2),
        "predicted_eol_date": predicted_eol_date.isoformat(),
        "phase_out_timeline": phase_out_timeline,
        "component_obsolescence": default_components,
        "alternative_sourcing": alternative_sourcing,
        "regulatory_region": regulatory_region,
        "regulatory_compliance": region_rules,
    }