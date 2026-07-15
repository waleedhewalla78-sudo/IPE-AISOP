"""A1.4 Rough-cut (RCCP) and detailed capacity (CRP) checks."""

from __future__ import annotations

from typing import Any


def run_rccp(
    *,
    week: str = "W31",
    loads: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Quick feasibility: work-centre load vs available hours.

    loads item: work_centre, load_hrs, available_hrs
    """
    loads = loads or [
        {"work_centre": "Core Cutting", "load_hrs": 28, "available_hrs": 40},
        {"work_centre": "Winding", "load_hrs": 36, "available_hrs": 32},
        {"work_centre": "Assembly", "load_hrs": 24, "available_hrs": 40},
        {"work_centre": "Testing", "load_hrs": 18, "available_hrs": 40},
        {"work_centre": "Painting", "load_hrs": 15, "available_hrs": 40},
    ]
    rows: list[dict[str, Any]] = []
    bottlenecks: list[dict[str, Any]] = []
    for item in loads:
        avail = float(item.get("available_hrs") or 0)
        load = float(item.get("load_hrs") or 0)
        util = round(100.0 * load / avail, 1) if avail > 0 else 0.0
        status = "ok"
        if util > 100:
            status = "overload"
        elif util >= 90:
            status = "tight"
        row = {
            "work_centre": item.get("work_centre"),
            "load_hrs": load,
            "available_hrs": avail,
            "utilisation_pct": util,
            "status": status,
        }
        rows.append(row)
        if status == "overload":
            bottlenecks.append(
                {
                    "work_centre": item.get("work_centre"),
                    "overload_hrs": round(load - avail, 1),
                    "utilisation_pct": util,
                }
            )

    suggestions: list[str] = []
    if bottlenecks:
        bn = bottlenecks[0]
        suggestions = [
            f"Shift 1 MO out of {week} (drops {bn['work_centre']} toward 100%)",
            "Saturday overtime for overload hours",
            "Cross-train adjacent WC operators",
        ]

    return {
        "week": week,
        "work_centres": rows,
        "bottlenecks": bottlenecks,
        "feasible": len(bottlenecks) == 0,
        "suggestions": suggestions,
        "agent": "A3",
    }


def run_crp(
    *,
    work_centre: str = "Winding",
    week: str = "W31",
    days: list[dict[str, Any]] | None = None,
    hours_per_shift: float = 7.5,
    shifts_per_day: int = 2,
) -> dict[str, Any]:
    """
    Day/shift-level loading for one WC.

    days item: day, shift1_load_hrs, shift2_load_hrs, notes (optional)
    """
    days = days or [
        {"day": "Monday", "shift1_load_hrs": 8.0, "shift2_load_hrs": 4.5},
        {"day": "Tuesday", "shift1_load_hrs": 7.0, "shift2_load_hrs": 6.5},
        {"day": "Wednesday", "shift1_load_hrs": 4.5, "shift2_load_hrs": 5.3},
        {"day": "Thursday", "shift1_load_hrs": 3.5, "shift2_load_hrs": 4.0},
        {"day": "Friday", "shift1_load_hrs": 2.0, "shift2_load_hrs": 0.0},
    ]
    daily_avail = hours_per_shift * shifts_per_day
    detail: list[dict[str, Any]] = []
    peak_util = 0.0
    week_load = 0.0
    for d in days:
        s1 = float(d.get("shift1_load_hrs") or 0)
        s2 = float(d.get("shift2_load_hrs") or 0)
        total = s1 + s2
        util = round(100.0 * total / daily_avail, 1) if daily_avail else 0.0
        peak_util = max(peak_util, util)
        week_load += total
        status = "ok"
        if util > 100:
            status = "overload"
        elif util >= 85:
            status = "tight"
        detail.append(
            {
                "day": d.get("day"),
                "shift1_load_hrs": s1,
                "shift2_load_hrs": s2,
                "total_hrs": round(total, 1),
                "available_hrs": daily_avail,
                "utilisation_pct": util,
                "status": status,
                "notes": d.get("notes"),
            }
        )

    week_avail = daily_avail * len(days)
    week_util = round(100.0 * week_load / week_avail, 1) if week_avail else 0.0
    recommendation = None
    if any(r["status"] == "overload" for r in detail):
        recommendation = (
            f"Move lowest-priority MO off peak day into a day with slack "
            f"({work_centre} weekly util {week_util}%)."
        )

    return {
        "work_centre": work_centre,
        "week": week,
        "hours_per_shift": hours_per_shift,
        "shifts_per_day": shifts_per_day,
        "days": detail,
        "weekly_load_hrs": round(week_load, 1),
        "weekly_available_hrs": week_avail,
        "weekly_utilisation_pct": week_util,
        "peak_utilisation_pct": peak_util,
        "recommendation": recommendation,
        "agent": "A3",
    }
