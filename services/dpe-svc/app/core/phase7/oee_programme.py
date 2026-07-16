"""Phase 7 §5.1 — OEE Improvement Programme (measure → improve, with payback)."""

from __future__ import annotations

from typing import Any


def build_oee_programme(
    *,
    work_centre: str = "Winding",
    availability_pct: float = 88.0,
    performance_pct: float = 92.0,
    quality_pct: float = 94.0,
    target_availability_pct: float = 90.0,
    target_performance_pct: float = 94.0,
    target_quality_pct: float = 96.0,
    initiatives: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    def _oee(a: float, p: float, q: float) -> float:
        return round(a / 100.0 * p / 100.0 * q / 100.0 * 100.0, 1)

    current_oee = _oee(availability_pct, performance_pct, quality_pct)
    target_oee = _oee(target_availability_pct, target_performance_pct, target_quality_pct)

    initiatives = initiatives or [
        {
            "month": 1,
            "lever": "quality",
            "action": "Tension calibration checklist at shift start",
            "from_pct": quality_pct,
            "to_pct": target_quality_pct,
            "investment_usd": 0,
            "annual_saving_usd": 22_000,
        },
        {
            "month": 2,
            "lever": "performance",
            "action": "Standardized wire threading SOP",
            "from_pct": performance_pct,
            "to_pct": target_performance_pct,
            "investment_usd": 0,
            "annual_saving_usd": 8_000,
        },
        {
            "month": 3,
            "lever": "availability",
            "action": "Vibration sensor for predictive maintenance",
            "from_pct": availability_pct,
            "to_pct": target_availability_pct,
            "investment_usd": 2_400,
            "annual_saving_usd": 18_000,
        },
    ]

    total_investment = sum(float(i["investment_usd"]) for i in initiatives)
    total_saving = sum(float(i["annual_saving_usd"]) for i in initiatives)
    payback_days = round(total_investment / (total_saving / 365.0), 0) if total_saving else 0

    return {
        "work_centre": work_centre,
        "current_oee_pct": current_oee,
        "target_oee_pct": target_oee,
        "improvement_pp": round(target_oee - current_oee, 1),
        "current_breakdown": {
            "availability_pct": availability_pct,
            "performance_pct": performance_pct,
            "quality_pct": quality_pct,
        },
        "target_breakdown": {
            "availability_pct": target_availability_pct,
            "performance_pct": target_performance_pct,
            "quality_pct": target_quality_pct,
        },
        "plan": sorted(initiatives, key=lambda i: i["month"]),
        "total_investment_usd": total_investment,
        "total_annual_saving_usd": total_saving,
        "payback_days": payback_days,
    }
