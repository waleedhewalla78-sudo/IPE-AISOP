"""Equipment health scoring from RUL telemetry."""

from __future__ import annotations


def rul_to_health_score(rul_hours: float, *, critical: float = 48.0) -> float:
    if rul_hours <= 0:
        return 0.0
    if rul_hours >= critical * 4:
        return 100.0
    return round(min(100.0, max(0.0, (rul_hours / (critical * 4)) * 100)), 2)


def predict_failure_date(rul_hours: float) -> dict:
    days = round(rul_hours / 24, 1)
    probability = 1.0 - min(1.0, rul_hours / (48 * 4))
    return {
        "rul_days": days,
        "failure_probability": round(probability, 3),
        "critical": rul_hours < 48,
    }
