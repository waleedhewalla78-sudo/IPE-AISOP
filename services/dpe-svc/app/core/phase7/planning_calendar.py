"""Phase 7 §6 — Integrated Planning Calendar.

A unified schedule of when each planning activity runs, keyed by cadence and mapped
to owning agents. Static config surfaced via API (optionally filterable by cadence).
"""

from __future__ import annotations

from typing import Any

_CALENDAR: dict[str, list[dict[str, Any]]] = {
    "daily": [
        {"time": "06:00", "activity": "Odoo/Excel sync", "agents": []},
        {"time": "06:15", "activity": "Feasibility scoring (all MOs)", "agents": ["A4"]},
        {"time": "06:30", "activity": "Resolution (at-risk MOs only)", "agents": ["A5"]},
        {"time": "07:00", "activity": "Morning brief generated", "agents": ["A7"]},
        {"time": "07:15", "activity": "Planner morning triage", "agents": []},
        {"time": "15:00", "activity": "Shift handover (auto-generated)", "agents": []},
        {"time": "23:00", "activity": "Daily analytics processing", "agents": ["A14"]},
    ],
    "weekly": [
        {"day": "Monday 08:00", "activity": "Demand forecast refresh", "agents": ["A1"]},
        {"day": "Monday 08:30", "activity": "MPS update", "agents": []},
        {"day": "Monday 09:00", "activity": "MRP run", "agents": []},
        {"day": "Monday 09:30", "activity": "PO recommendations", "agents": ["A9"]},
        {"day": "Monday 10:00", "activity": "Safety stock & segmentation check", "agents": ["A2"]},
        {"day": "Monday 14:00", "activity": "Weekly schedule optimization", "agents": ["A3"]},
        {"day": "Monday 16:00", "activity": "Weekly insight report", "agents": ["A14"]},
    ],
    "monthly": [
        {"when": "Week 1", "activity": "S&OP demand review", "agents": ["A1", "A6"]},
        {"when": "Week 2", "activity": "S&OP supply review", "agents": ["A3", "A6"]},
        {"when": "Week 3", "activity": "S&OP reconciliation", "agents": ["A6", "A11"]},
        {"when": "Week 4", "activity": "S&OP management review", "agents": ["A6", "A7", "A17"]},
        {"when": "Month-end", "activity": "Segmentation recalculation", "agents": ["A2"]},
        {"when": "Month-end", "activity": "Supplier performance review", "agents": ["A9"]},
        {"when": "Month-end", "activity": "Monthly performance report", "agents": ["A14"]},
    ],
    "quarterly": [
        {"activity": "Strategic horizon update", "agents": ["A6", "A14"]},
        {"activity": "Portfolio mix optimization", "agents": ["A6", "A11", "A13"]},
        {"activity": "Capacity investment review", "agents": ["A11", "A17"]},
        {"activity": "Demand model recalibration (seasonal factors)", "agents": ["A1"]},
        {"activity": "OEE improvement plan review", "agents": ["A3"]},
    ],
    "annually": [
        {"activity": "AOP integration", "agents": ["A6", "A11"]},
        {"activity": "Strategic planning horizon (24-month)", "agents": ["A6"]},
        {"activity": "Demand decomposition recalibration", "agents": ["A1"]},
        {"activity": "System configuration review", "agents": []},
    ],
}


def build_planning_calendar(*, cadence: str | None = None) -> dict[str, Any]:
    if cadence:
        cadence = cadence.lower()
        entries = _CALENDAR.get(cadence, [])
        return {"cadence": cadence, "entries": entries, "count": len(entries)}
    return {
        "cadences": list(_CALENDAR.keys()),
        "calendar": _CALENDAR,
        "total_activities": sum(len(v) for v in _CALENDAR.values()),
    }
