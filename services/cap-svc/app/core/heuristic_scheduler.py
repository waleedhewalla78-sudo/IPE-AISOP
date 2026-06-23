"""Greedy EDD heuristic used when CP-SAT times out."""

from __future__ import annotations

from typing import Any


def heuristic_schedule(
    work_centers: list[dict],
    operations: list[dict],
    horizon: int,
) -> dict[str, Any]:
    """Priority-weighted earliest-due-date greedy placement per work center."""
    wc_available: dict[str, int] = {str(wc["id"]): 0 for wc in work_centers}

    def sort_key(op: dict) -> tuple:
        due = op.get("due_date_minutes")
        due_val = int(due) if due is not None else horizon
        prio = float(op.get("priority_score") or 0.5)
        return (due_val, -prio, int(op.get("sequence") or 0))

    sorted_ops = sorted(operations, key=sort_key)
    assignments: list[dict] = []
    mo_completion: dict[str, int] = {}

    for op in sorted_ops:
        op_id = str(op["id"])
        wc_id = str(op["work_center_id"])
        mo_id = str(op.get("mo_id", "default"))
        duration = int(op.get("duration_planned_mins") or 60)
        duration = max(1, min(duration, horizon))

        earliest = wc_available.get(wc_id, 0)
        mo_prev = mo_completion.get(mo_id, 0)
        start = max(earliest, mo_prev)
        end = min(start + duration, horizon)
        if end <= start:
            continue

        wc_available[wc_id] = end
        mo_completion[mo_id] = end

        due = op.get("due_date_minutes")
        on_time = due is None or end <= int(due)

        assignments.append({
            "operation_id": op_id,
            "work_center_id": wc_id,
            "start_minute": start,
            "end_minute": end,
            "duration": end - start,
            "on_time": on_time,
            "mo_id": mo_id,
            "sequence": op.get("sequence", 0),
            "bom_level": op.get("bom_level", 0),
            "parent_operation_id": op.get("parent_operation_id"),
            "operation_name": op.get("operation_name", ""),
            "worker_id": None,
        })

    mo_tardiness = []
    for mo_id, completion in mo_completion.items():
        due_dates = [
            int(o["due_date_minutes"])
            for o in operations
            if str(o.get("mo_id")) == mo_id and o.get("due_date_minutes") is not None
        ]
        due = min(due_dates) if due_dates else horizon
        tardiness = max(0, completion - due)
        mo_tardiness.append({
            "mo_id": mo_id,
            "due_date_minute": due,
            "completion_minute": completion,
            "tardiness_minutes": tardiness,
            "on_time": tardiness == 0,
        })

    return {
        "status": "HEURISTIC",
        "assignments": assignments,
        "mo_tardiness": mo_tardiness,
        "solver_status": "heuristic_fallback",
        "skill_relaxed": False,
        "requires_manual_review": True,
    }
