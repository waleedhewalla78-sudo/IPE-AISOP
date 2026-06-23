"""Tests for heuristic scheduler fallback."""

from app.core.heuristic_scheduler import heuristic_schedule


def test_heuristic_produces_assignments():
    work_centers = [{"id": "WC001", "name": "Line 1"}]
    operations = [
        {
            "id": "OP1",
            "mo_id": "MO-A",
            "sequence": 10,
            "work_center_id": "WC001",
            "duration_planned_mins": 60,
            "due_date_minutes": 120,
            "priority_score": 0.9,
            "operation_name": "Op A",
        },
        {
            "id": "OP2",
            "mo_id": "MO-B",
            "sequence": 10,
            "work_center_id": "WC001",
            "duration_planned_mins": 45,
            "due_date_minutes": 240,
            "priority_score": 0.4,
            "operation_name": "Op B",
        },
    ]
    result = heuristic_schedule(work_centers, operations, horizon=480)
    assert result["solver_status"] == "heuristic_fallback"
    assert len(result["assignments"]) == 2
    assert result["assignments"][0]["start_minute"] <= result["assignments"][1]["start_minute"]
