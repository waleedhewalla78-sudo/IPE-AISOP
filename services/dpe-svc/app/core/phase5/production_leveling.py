"""A1.6 Production leveling — smooth load across periods."""

from __future__ import annotations

from typing import Any


def level_production(
    *,
    weekly_demand: list[dict[str, Any]],
    capacity_per_week: float,
) -> dict[str, Any]:
    """
    Level production by moving peak load into under-loaded weeks when capacity allows.
    weekly_demand: [{week, demand}]
    """
    if not weekly_demand:
        return {"weeks": [], "peaks_smoothed": 0, "still_over": []}

    total = sum(float(w.get("demand", 0)) for w in weekly_demand)
    avg = total / len(weekly_demand)
    target = min(avg, capacity_per_week)

    leveled: list[dict[str, Any]] = []
    spill = 0.0
    peaks = 0
    still_over: list[str] = []

    # First pass: cap peaks and accumulate spill into later under weeks
    for w in weekly_demand:
        demand = float(w.get("demand", 0))
        planned = demand
        if demand > capacity_per_week:
            spill += demand - capacity_per_week
            planned = capacity_per_week
            peaks += 1
        elif demand < target and spill > 0:
            room = min(capacity_per_week - demand, spill)
            planned = demand + room
            spill -= room
        leveled.append(
            {
                "week": w.get("week"),
                "original_demand": demand,
                "leveled_production": round(planned, 1),
                "utilisation_pct": round(100 * planned / capacity_per_week, 1) if capacity_per_week else 0,
                "over_capacity": planned > capacity_per_week,
            }
        )

    # Push remaining spill to earliest weeks with room
    if spill > 0:
        for row in leveled:
            if spill <= 0:
                break
            room = capacity_per_week - row["leveled_production"]
            if room > 0:
                take = min(room, spill)
                row["leveled_production"] = round(row["leveled_production"] + take, 1)
                row["utilisation_pct"] = round(100 * row["leveled_production"] / capacity_per_week, 1)
                spill -= take

    for row in leveled:
        row["over_capacity"] = row["leveled_production"] > capacity_per_week + 0.01
        if row["over_capacity"]:
            still_over.append(str(row["week"]))

    return {
        "capacity_per_week": capacity_per_week,
        "average_demand": round(avg, 1),
        "weeks": leveled,
        "peaks_smoothed": peaks,
        "residual_spill": round(spill, 1),
        "still_over": still_over,
        "feasible": spill <= 0 and not still_over,
    }
