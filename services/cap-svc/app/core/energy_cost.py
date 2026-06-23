"""Energy cost calculator for TOU-aware scheduling.

Maps operation time windows against Time-of-Use (TOU) electricity tariffs
and multiplies by energy_kwh_per_hour to compute energy cost.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def build_tou_rate_map(tariffs: list[dict]) -> dict[tuple[int, int], float]:
    """Build a lookup map from (day_of_week, hour) -> rate_per_kwh.

    Args:
        tariffs: List of dicts with keys: day_of_week (0-6), hour_start (0-23),
                 hour_end (0-23), rate_per_kwh.

    Returns:
        Dict mapping (day_of_week, hour) to rate_per_kwh.
    """
    rate_map: dict[tuple[int, int], float] = {}
    for t in tariffs:
        dow = int(t.get("day_of_week", 0))
        h_start = int(t.get("hour_start", 0))
        h_end = int(t.get("hour_end", 23))
        rate = float(t.get("rate_per_kwh", 0.0))
        for h in range(h_start, h_end + 1):
            rate_map[(dow, h % 24)] = rate
    return rate_map


def calculate_energy_cost(
    operation_start_minute: int,
    duration_minutes: int,
    energy_kwh_per_hour: float,
    rate_map: dict[tuple[int, int], float],
    reference_date: datetime | None = None,
) -> dict[str, Any]:
    """Calculate energy cost for an operation based on TOU rates.

    Args:
        operation_start_minute: Start time in minutes from horizon origin.
        duration_minutes: Duration of the operation in minutes.
        energy_kwh_per_hour: Power consumption of the resource (kWh/hour).
        rate_map: TOU rate map from build_tou_rate_map().
        reference_date: Base date for mapping minutes to day/hour.
                        Defaults to Monday 00:00 of the current week.

    Returns:
        Dict with total_energy_kwh, total_energy_cost, breakdown_by_hour.
    """
    if not rate_map or energy_kwh_per_hour <= 0:
        return {
            "total_energy_kwh": 0.0,
            "total_energy_cost": 0.0,
            "breakdown_by_hour": [],
        }

    if reference_date is None:
        now = datetime.now()
        reference_date = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    total_kwh = 0.0
    total_cost = 0.0
    breakdown = []

    end_minute = operation_start_minute + duration_minutes
    minute_cursor = operation_start_minute

    while minute_cursor < end_minute:
        dt = reference_date + timedelta(minutes=minute_cursor)
        hour = dt.hour
        dow = dt.weekday()
        rate = rate_map.get((dow, hour), 0.0)

        next_hour_boundary = reference_date + timedelta(
            hours=(dt - reference_date).seconds // 3600 + 1,
            minutes=0, seconds=0, microseconds=0,
        )
        minutes_to_next_hour = int((next_hour_boundary - dt).total_seconds() / 60)
        chunk_minutes = min(minutes_to_next_hour, end_minute - minute_cursor)

        chunk_hours = chunk_minutes / 60.0
        chunk_kwh = energy_kwh_per_hour * chunk_hours
        chunk_cost = chunk_kwh * rate

        total_kwh += chunk_kwh
        total_cost += chunk_cost
        breakdown.append({
            "day_of_week": dow,
            "hour": hour,
            "minutes": chunk_minutes,
            "rate_per_kwh": rate,
            "energy_kwh": round(chunk_kwh, 4),
            "cost": round(chunk_cost, 4),
        })

        minute_cursor += chunk_minutes

    return {
        "total_energy_kwh": round(total_kwh, 4),
        "total_energy_cost": round(total_cost, 4),
        "breakdown_by_hour": breakdown,
    }


def calculate_labor_cost(
    duration_minutes: int,
    cost_per_hour: float,
    overtime_multiplier: float,
    regular_hours_per_day: float,
    operation_start_minute: int,
    reference_date: datetime | None = None,
) -> dict[str, Any]:
    """Calculate labor cost including overtime multipliers.

    Args:
        duration_minutes: Duration of the operation.
        cost_per_hour: Base hourly labor cost.
        overtime_multiplier: Multiplier for overtime hours (e.g. 1.5).
        regular_hours_per_day: Regular working hours per day (e.g. 8).
        operation_start_minute: Start time in minutes from horizon origin.
        reference_date: Base date for mapping minutes to day/hour.

    Returns:
        Dict with total_labor_cost, regular_cost, overtime_cost, overtime_minutes.
    """
    if cost_per_hour <= 0:
        return {
            "total_labor_cost": 0.0,
            "regular_cost": 0.0,
            "overtime_cost": 0.0,
            "overtime_minutes": 0,
        }

    if reference_date is None:
        now = datetime.now()
        reference_date = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    total_cost = 0.0
    overtime_minutes = 0
    minute_cursor = operation_start_minute
    end_minute = operation_start_minute + duration_minutes

    while minute_cursor < end_minute:
        chunk_end = min(minute_cursor + 60, end_minute)
        chunk_minutes = chunk_end - minute_cursor
        chunk_hours = chunk_minutes / 60.0

        dt = reference_date + timedelta(minutes=minute_cursor)
        hour_of_day = dt.hour

        is_regular = 8 <= hour_of_day < 8 + int(regular_hours_per_day)
        if is_regular:
            total_cost += chunk_hours * cost_per_hour
        else:
            total_cost += chunk_hours * cost_per_hour * float(overtime_multiplier)
            overtime_minutes += chunk_minutes

        minute_cursor = chunk_end

    regular_cost = (duration_minutes - overtime_minutes) / 60.0 * cost_per_hour
    overtime_cost = overtime_minutes / 60.0 * cost_per_hour * float(overtime_multiplier)

    return {
        "total_labor_cost": round(total_cost, 4),
        "regular_cost": round(regular_cost, 4),
        "overtime_cost": round(overtime_cost, 4),
        "overtime_minutes": overtime_minutes,
    }
