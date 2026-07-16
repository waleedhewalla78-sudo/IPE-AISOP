"""A16 Shop Floor Intelligence — PP-execution equivalent.

Digital work instructions per MO, operator time tracking, and real-time
production progress with deviation alerts. IoT / machine telemetry is a STUB
(no live MQTT/REST feed — flagged accordingly). Operator input is supplied by
the caller (tablet UI is minimal for Wave 1).
"""

from __future__ import annotations

from typing import Any


def build_work_instructions(
    *,
    mo_id: str = "MO-ST-004",
    product_id: str = "FG-DT250",
    routing: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return ordered digital work instructions derived from a routing."""
    routing = (
        routing
        if routing is not None
        else [
            {
                "seq": 10,
                "work_centre": "Core Cutting",
                "std_minutes": 45,
                "instruction": "Cut core laminations to spec.",
            },
            {
                "seq": 20,
                "work_centre": "Winding",
                "std_minutes": 180,
                "instruction": "Wind primary + secondary coils.",
            },
            {
                "seq": 30,
                "work_centre": "Assembly",
                "std_minutes": 90,
                "instruction": "Assemble core + coil + tank.",
            },
            {
                "seq": 40,
                "work_centre": "Testing",
                "std_minutes": 60,
                "instruction": "Routine + type tests per IEC.",
            },
        ]
    )
    steps = sorted(routing, key=lambda r: r["seq"])
    total_std = sum(float(s.get("std_minutes", 0)) for s in steps)
    return {
        "agent_id": "A16",
        "capability": "work_instructions",
        "mo_id": mo_id,
        "product_id": product_id,
        "steps": [
            {
                "seq": s["seq"],
                "work_centre": s["work_centre"],
                "std_minutes": s.get("std_minutes", 0),
                "instruction": s.get("instruction", ""),
                "status": "pending",
            }
            for s in steps
        ],
        "total_std_minutes": total_std,
    }


def track_time(
    *,
    mo_id: str = "MO-ST-004",
    operation_seq: int = 20,
    operator: str = "Mohamed",
    std_minutes: float = 180.0,
    actual_minutes: float = 205.0,
) -> dict[str, Any]:
    """Log operator time and compute efficiency + deviation alert."""
    efficiency = round(std_minutes / actual_minutes * 100, 1) if actual_minutes else 0.0
    variance = round(actual_minutes - std_minutes, 1)
    variance_pct = round(variance / std_minutes * 100, 1) if std_minutes else 0.0
    alert = None
    if variance_pct > 10:
        alert = (
            f"Operation {operation_seq} on {mo_id} ran {variance_pct}% over standard "
            f"({actual_minutes} vs {std_minutes} min) — review method/skill."
        )
    return {
        "agent_id": "A16",
        "capability": "time_tracking",
        "mo_id": mo_id,
        "operation_seq": operation_seq,
        "operator": operator,
        "std_minutes": std_minutes,
        "actual_minutes": actual_minutes,
        "efficiency_pct": efficiency,
        "variance_minutes": variance,
        "variance_pct": variance_pct,
        "alert": alert,
    }


def production_progress(
    *,
    mo_id: str = "MO-ST-004",
    operations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Aggregate per-operation completion into MO progress with deviations."""
    operations = (
        operations
        if operations is not None
        else [
            {"seq": 10, "work_centre": "Core Cutting", "pct_complete": 100, "on_schedule": True},
            {"seq": 20, "work_centre": "Winding", "pct_complete": 60, "on_schedule": False},
            {"seq": 30, "work_centre": "Assembly", "pct_complete": 0, "on_schedule": True},
            {"seq": 40, "work_centre": "Testing", "pct_complete": 0, "on_schedule": True},
        ]
    )
    if operations:
        overall = round(
            sum(float(o.get("pct_complete", 0)) for o in operations) / len(operations), 1
        )
    else:
        overall = 0.0
    deviations = [
        f"Op {o['seq']} ({o['work_centre']}) behind schedule"
        for o in operations
        if not o.get("on_schedule", True)
    ]
    if overall >= 100:
        status = "complete"
    elif overall > 0:
        status = "in_progress"
    else:
        status = "not_started"
    return {
        "agent_id": "A16",
        "capability": "production_progress",
        "mo_id": mo_id,
        "overall_pct_complete": overall,
        "status": status,
        "operations": operations,
        "deviations": deviations,
        "iot_telemetry": {
            "live": False,
            "blocker": "IoT/machine integration STUB — no live MQTT/REST feed wired",
        },
    }


class ShopFloorIntelligence:
    """A16 facade."""

    agent_id = "A16"
    name = "Shop Floor Intelligence"

    def instructions(self, **kwargs: Any) -> dict[str, Any]:
        return build_work_instructions(**kwargs)

    def time(self, **kwargs: Any) -> dict[str, Any]:
        return track_time(**kwargs)

    def progress(self, **kwargs: Any) -> dict[str, Any]:
        return production_progress(**kwargs)
