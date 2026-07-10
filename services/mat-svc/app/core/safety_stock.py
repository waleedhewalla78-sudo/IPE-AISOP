"""Dynamic safety stock calculator.

Computes safety stock levels based on:
- Demand variability (standard deviation of daily demand)
- Lead time variability (supplier delay std dev)
- Target service level (z-score mapping)

Formula: SS = z * sqrt(LT * σ_demand² + demand_avg² * σ_LT²)

Where:
  z = service level z-score (e.g. 1.65 for 95%)
  LT = average lead time in days
  σ_demand = standard deviation of daily demand
  demand_avg = average daily demand
  σ_LT = standard deviation of lead time (supplier delay std dev)
"""
from __future__ import annotations

import math
from typing import Any


SERVICE_LEVEL_Z = {
    0.90: 1.28,
    0.91: 1.34,
    0.92: 1.41,
    0.93: 1.48,
    0.94: 1.55,
    0.95: 1.65,
    0.96: 1.75,
    0.97: 1.88,
    0.98: 2.05,
    0.99: 2.33,
    0.995: 2.58,
    0.999: 3.09,
}


def _z_score(service_level: float) -> float:
    """Convert service level (0-1) to z-score.

    Uses linear interpolation between known values.
    """
    if service_level <= 0:
        return 0.0
    if service_level >= 1.0:
        return 3.09

    levels = sorted(SERVICE_LEVEL_Z.keys())
    for i in range(len(levels) - 1):
        if levels[i] <= service_level <= levels[i + 1]:
            lo, hi = levels[i], levels[i + 1]
            z_lo, z_hi = SERVICE_LEVEL_Z[lo], SERVICE_LEVEL_Z[hi]
            t = (service_level - lo) / (hi - lo)
            return z_lo + t * (z_hi - z_lo)

    return SERVICE_LEVEL_Z.get(levels[-1], 1.65)


def _z_score_ibp(service_level_pct: float) -> float:
    """Convert a service level percentage to a z-score for IBP calculations."""
    service_level = service_level_pct / 100 if service_level_pct > 1 else service_level_pct
    service_level = min(max(service_level, 0.0), 0.999)
    try:
        from scipy.stats import norm

        return float(norm.ppf(service_level))
    except Exception:
        return _z_score(service_level)


def _sample_std(values: list[float], mean: float) -> float:
    if len(values) <= 1:
        return 0.0
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(max(0.0, variance))


def calculate_safety_stock_ibp(
    demand_series: list[float],
    lead_time_days_series: list[float],
    service_level_pct: float,
    period_days: int = 7,
) -> dict[str, Any]:
    """Calculate safety stock using the SAP IBP-style independent component formula.

    Formula:
        SS = z * σ_d * sqrt(LT) + z * d_bar * σ_LT

    Demand is assumed to be expressed per planning period. Lead times are supplied
    in days and converted to planning periods using ``period_days``.
    """
    demand_values = [float(value or 0) for value in demand_series]
    lead_time_days = [float(value or 0) for value in lead_time_days_series if value is not None]
    if period_days <= 0:
        raise ValueError("period_days must be greater than zero")
    if not demand_values:
        demand_values = [0.0]
    if not lead_time_days:
        lead_time_days = [14.0]

    avg_demand = sum(demand_values) / len(demand_values)
    demand_stddev = _sample_std(demand_values, avg_demand)
    avg_lead_time_days = sum(lead_time_days) / len(lead_time_days)
    lead_time_stddev_days = _sample_std(lead_time_days, avg_lead_time_days)
    avg_lead_time_periods = avg_lead_time_days / period_days
    lead_time_stddev_periods = lead_time_stddev_days / period_days
    z = _z_score_ibp(service_level_pct)

    demand_component = z * demand_stddev * math.sqrt(max(avg_lead_time_periods, 0.0))
    lead_time_component = z * avg_demand * lead_time_stddev_periods
    safety_stock = demand_component + lead_time_component
    reorder_point = (avg_demand * avg_lead_time_periods) + safety_stock

    demand_cv = demand_stddev / avg_demand if avg_demand else 0.0
    lead_time_cv = lead_time_stddev_days / avg_lead_time_days if avg_lead_time_days else 0.0
    service_level = service_level_pct / 100 if service_level_pct > 1 else service_level_pct

    return {
        "safety_stock_qty": round(safety_stock, 2),
        "reorder_point": round(reorder_point, 2),
        "z_score": round(z, 4),
        "service_level": round(service_level, 4),
        "service_level_pct": round(service_level * 100, 2),
        "components": {
            "demand_component": round(demand_component, 4),
            "lead_time_component": round(lead_time_component, 4),
        },
        "inputs": {
            "avg_demand_per_period": round(avg_demand, 4),
            "demand_stddev": round(demand_stddev, 4),
            "demand_cv": round(demand_cv, 4),
            "avg_lead_time_days": round(avg_lead_time_days, 4),
            "avg_lead_time_periods": round(avg_lead_time_periods, 4),
            "lead_time_stddev_days": round(lead_time_stddev_days, 4),
            "lead_time_stddev_periods": round(lead_time_stddev_periods, 4),
            "lead_time_cv": round(lead_time_cv, 4),
            "period_days": period_days,
        },
    }


def calculate_safety_stock(
    avg_daily_demand: float,
    demand_std_dev: float,
    avg_lead_time_days: float,
    lead_time_std_dev: float,
    service_level: float = 0.95,
) -> dict[str, Any]:
    """Calculate dynamic safety stock level.

    Args:
        avg_daily_demand: Average daily demand quantity.
        demand_std_dev: Standard deviation of daily demand.
        avg_lead_time_days: Average supplier lead time in days.
        lead_time_std_dev: Standard deviation of lead time in days.
        service_level: Target service level (0-1, default 0.95 = 95%).

    Returns:
        Dict with safety_stock_qty, z_score, reorder_point, components breakdown.
    """
    z = _z_score(service_level)

    demand_variance_component = avg_lead_time_days * (demand_std_dev ** 2)
    lead_time_variance_component = (avg_daily_demand ** 2) * (lead_time_std_dev ** 2)
    combined_variance = demand_variance_component + lead_time_variance_component

    safety_stock = z * math.sqrt(max(0, combined_variance))

    reorder_point = (avg_daily_demand * avg_lead_time_days) + safety_stock

    return {
        "safety_stock_qty": round(safety_stock, 2),
        "z_score": round(z, 4),
        "reorder_point": round(reorder_point, 2),
        "service_level": service_level,
        "components": {
            "demand_variance": round(demand_variance_component, 4),
            "lead_time_variance": round(lead_time_variance_component, 4),
            "combined_variance": round(combined_variance, 4),
        },
        "inputs": {
            "avg_daily_demand": avg_daily_demand,
            "demand_std_dev": demand_std_dev,
            "avg_lead_time_days": avg_lead_time_days,
            "lead_time_std_dev": lead_time_std_dev,
        },
    }


def calculate_safety_stock_from_history(
    demand_history: list[float],
    lead_time_days: float,
    lead_time_std_dev: float,
    service_level: float = 0.95,
) -> dict[str, Any]:
    """Calculate safety stock from historical demand data.

    Args:
        demand_history: List of daily demand quantities.
        lead_time_days: Average supplier lead time.
        lead_time_std_dev: Std dev of lead time.
        service_level: Target service level.

    Returns:
        Dict with safety_stock_qty and statistics.
    """
    if not demand_history:
        return {
            "safety_stock_qty": 0,
            "z_score": _z_score(service_level),
            "reorder_point": 0,
            "error": "No demand history",
        }

    n = len(demand_history)
    avg_demand = sum(demand_history) / n
    demand_var = sum((d - avg_demand) ** 2 for d in demand_history) / max(1, n - 1)
    demand_std = math.sqrt(demand_var)

    return calculate_safety_stock(
        avg_daily_demand=avg_demand,
        demand_std_dev=demand_std,
        avg_lead_time_days=lead_time_days,
        lead_time_std_dev=lead_time_std_dev,
        service_level=service_level,
    )


def calculate_all_products_safety_stock(
    products: list[dict],
    service_level: float = 0.95,
) -> list[dict[str, Any]]:
    """Calculate safety stock for multiple products.

    Args:
        products: List of dicts with:
            - product_id: str
            - avg_daily_demand: float
            - demand_std_dev: float
            - avg_lead_time_days: float
            - lead_time_std_dev: float
        service_level: Target service level.

    Returns:
        List of dicts with product_id and safety stock calculation.
    """
    results = []
    for p in products:
        calc = calculate_safety_stock(
            avg_daily_demand=p.get("avg_daily_demand", 0),
            demand_std_dev=p.get("demand_std_dev", 0),
            avg_lead_time_days=p.get("avg_lead_time_days", 0),
            lead_time_std_dev=p.get("lead_time_std_dev", 0),
            service_level=service_level,
        )
        results.append({
            "product_id": p.get("product_id"),
            **calc,
        })
    return results
