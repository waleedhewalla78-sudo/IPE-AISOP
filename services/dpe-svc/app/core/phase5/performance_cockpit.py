"""B1.5 Performance cockpit — OEE + OTD/cost/quality/safety strip."""

from __future__ import annotations

from typing import Any


def build_performance_cockpit(
    *,
    availability_pct: float = 88.0,
    performance_pct: float = 92.0,
    quality_pct: float = 94.0,
    otd_pct: float = 89.0,
    otd_delta_pp: float = 15.0,
    cost_variance_pct: float = -2.1,
    defect_pct: float = 1.8,
    safety_incidents: int = 0,
    days_since_incident: int = 45,
    wc_oee: dict[str, float] | None = None,
    oee_trend: list[float] | None = None,
) -> dict[str, Any]:
    factory_oee = round(
        (availability_pct / 100.0) * (performance_pct / 100.0) * (quality_pct / 100.0) * 100.0,
        1,
    )
    wc_oee = wc_oee or {
        "Core Cutting": 82.0,
        "Winding": 71.0,
        "Assembly": 78.0,
        "Testing": 85.0,
        "Painting": 80.0,
    }
    oee_trend = oee_trend or [72.0, 74.0, 76.0, factory_oee]
    weak = [name for name, val in wc_oee.items() if val < 75.0]
    return {
        "factory_oee_pct": factory_oee,
        "oee_breakdown": {
            "availability_pct": availability_pct,
            "performance_pct": performance_pct,
            "quality_pct": quality_pct,
        },
        "by_work_centre": [{"work_centre": k, "oee_pct": v} for k, v in wc_oee.items()],
        "oee_trend_pct": oee_trend,
        "attention_wcs": weak,
        "kpis": {
            "otd_pct": otd_pct,
            "otd_delta_pp": otd_delta_pp,
            "otd_target_pct": 95.0,
            "cost_variance_pct": cost_variance_pct,
            "cost_target_band_pct": 3.0,
            "defect_pct": defect_pct,
            "defect_target_pct": 2.0,
            "safety_incidents": safety_incidents,
            "days_since_incident": days_since_incident,
        },
    }
