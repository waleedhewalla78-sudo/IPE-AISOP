"""Simple exponential smoothing and moving-average demand forecasts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from statistics import mean, pstdev


def simple_exponential_smoothing(history: list[float], alpha: float = 0.3) -> float:
    if not history:
        return 0.0
    level = history[0]
    for value in history[1:]:
        level = alpha * value + (1 - alpha) * level
    return level


def forecast_series(
    history: list[float],
    periods: int,
    *,
    alpha: float = 0.3,
) -> list[dict[str, float]]:
    """Return next `periods` point forecasts with confidence bands."""
    if not history:
        return [{"value": 0.0, "lower": 0.0, "upper": 0.0} for _ in range(periods)]

    base = simple_exponential_smoothing(history, alpha=alpha)
    spread = pstdev(history) if len(history) > 1 else max(base * 0.1, 1.0)
    return [
        {
            "value": round(base, 4),
            "lower": round(max(0.0, base - 1.96 * spread), 4),
            "upper": round(base + 1.96 * spread, 4),
        }
        for _ in range(periods)
    ]


def mape(actual: list[float], predicted: list[float]) -> float | None:
    pairs = [(a, p) for a, p in zip(actual, predicted, strict=False) if a]
    if not pairs:
        return None
    return round(mean(abs((a - p) / a) for a, p in pairs) * 100, 2)


def forecast_dates(start: datetime, periods: int, *, horizon: str) -> list[datetime]:
    step = timedelta(days=1 if horizon == "short" else 7)
    return [start + step * (i + 1) for i in range(periods)]
