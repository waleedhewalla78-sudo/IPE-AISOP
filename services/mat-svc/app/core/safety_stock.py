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
