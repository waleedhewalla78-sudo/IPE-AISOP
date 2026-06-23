from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


SCORING_WEIGHTS: dict[str, float] = {
    "otif": 0.35,
    "quality_defect_rate": 0.25,
    "cost_competitiveness": 0.20,
    "sustainability": 0.10,
    "responsiveness": 0.10,
}

HISTORICAL_WINDOWS: dict[str, int] = {
    "30d": 30,
    "90d": 90,
    "365d": 365,
}


def _compute_trend(values: list[float]) -> dict:
    if not values:
        return {"direction": "stable", "change_pct": 0.0}
    if len(values) == 1:
        return {"direction": "stable", "change_pct": 0.0}
    first = values[0]
    last = values[-1]
    if first == 0:
        change_pct = 0.0
    else:
        change_pct = round(((last - first) / first) * 100, 2)
    if change_pct > 2:
        direction = "improving"
    elif change_pct < -2:
        direction = "declining"
    else:
        direction = "stable"
    return {"direction": direction, "change_pct": change_pct}


def calculate_supplier_scorecard(
    tenant_id: str,
    supplier_id: str,
    historical_data: dict | None = None,
) -> dict:
    if historical_data is None:
        historical_data = {}

    otif_data = historical_data.get("otif", {})
    quality_data = historical_data.get("quality_defect_rate", {})
    cost_data = historical_data.get("cost_competitiveness", {})
    sustainability_data = historical_data.get("sustainability", {})
    responsiveness_data = historical_data.get("responsiveness", {})

    otif_score = min(100.0, max(0.0, otif_data.get("score", 85.0)))
    quality_score = min(100.0, max(0.0, quality_data.get("score", 90.0)))
    cost_score = min(100.0, max(0.0, cost_data.get("score", 78.0)))
    sustainability_score = min(100.0, max(0.0, sustainability_data.get("score", 70.0)))
    responsiveness_score = min(100.0, max(0.0, responsiveness_data.get("score", 82.0)))

    composite_score = (
        otif_score * SCORING_WEIGHTS["otif"]
        + quality_score * SCORING_WEIGHTS["quality_defect_rate"]
        + cost_score * SCORING_WEIGHTS["cost_competitiveness"]
        + sustainability_score * SCORING_WEIGHTS["sustainability"]
        + responsiveness_score * SCORING_WEIGHTS["responsiveness"]
    )
    composite_score = round(min(100.0, max(0.0, composite_score)), 2)

    if composite_score >= 80:
        risk_tier = "low"
    elif composite_score >= 60:
        risk_tier = "medium"
    else:
        risk_tier = "high"

    dimension_scores = {
        "otif": {"score": round(otif_score, 2), "weight": SCORING_WEIGHTS["otif"]},
        "quality_defect_rate": {"score": round(quality_score, 2), "weight": SCORING_WEIGHTS["quality_defect_rate"]},
        "cost_competitiveness": {"score": round(cost_score, 2), "weight": SCORING_WEIGHTS["cost_competitiveness"]},
        "sustainability": {"score": round(sustainability_score, 2), "weight": SCORING_WEIGHTS["sustainability"]},
        "responsiveness": {"score": round(responsiveness_score, 2), "weight": SCORING_WEIGHTS["responsiveness"]},
    }

    trends = {}
    for dimension, key in [
        ("otif", "otif"),
        ("quality_defect_rate", "quality_defect_rate"),
        ("cost_competitiveness", "cost_competitiveness"),
        ("sustainability", "sustainability"),
        ("responsiveness", "responsiveness"),
    ]:
        dim_data = historical_data.get(key, {})
        history = dim_data.get("history", [])
        trends[dimension] = _compute_trend(history)

    historical_trends = {}
    for window_name, window_days in HISTORICAL_WINDOWS.items():
        window_scores = {}
        for dim_key in SCORING_WEIGHTS:
            dim_data = historical_data.get(dim_key, {})
            history = dim_data.get("history", [])
            if history:
                idx = max(0, len(history) - min(window_days, len(history)))
                window_values = history[idx:]
                window_scores[dim_key] = round(sum(window_values) / len(window_values), 2) if window_values else 0.0
            else:
                window_scores[dim_key] = 0.0
        historical_trends[window_name] = window_scores

    return {
        "supplier_id": supplier_id,
        "tenant_id": tenant_id,
        "composite_score": composite_score,
        "risk_tier": risk_tier,
        "dimension_scores": dimension_scores,
        "trends": trends,
        "historical_trends": historical_trends,
        "computed_at": datetime.now(UTC).isoformat(),
    }