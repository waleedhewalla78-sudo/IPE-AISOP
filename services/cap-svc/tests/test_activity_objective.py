"""Unit tests for activity-based scheduling objective."""

from app.core.activity_objective import estimate_activity_costs, solve_activity_optimized


def test_estimate_activity_costs_includes_components():
    work_centers = [{
        "id": "WC001",
        "cost_per_hour": 60.0,
        "overtime_cost_multiplier": 1.5,
    }]
    operations = [
        {"work_center_id": "WC001", "duration": 60, "mo_id": "MO1"},
        {"work_center_id": "WC001", "duration": 60, "mo_id": "MO2"},
    ]
    result = estimate_activity_costs(operations, work_centers, setup_cost_per_change=100.0)
    assert result["setup_usd"] >= 0
    assert result["total_usd"] >= result["setup_usd"]
    assert "overtime_usd" in result
    assert "expedite_usd" in result


def test_solve_activity_optimized_returns_breakdown():
    work_centers = [{
        "id": "WC001",
        "name": "Assembly",
        "capacity_hours_per_day": 16,
        "oee": 0.9,
        "energy_kwh_per_hour": 2.0,
        "cost_per_hour": 60.0,
        "overtime_cost_multiplier": 1.5,
    }]
    operations = [
        {
            "id": "OP001",
            "mo_id": "MO001",
            "sequence": 1,
            "work_center_id": "WC001",
            "duration_planned_mins": 120,
            "operation_name": "Op 1",
            "priority_score": 0.9,
            "due_date_minutes": 480,
        },
    ]

    result = solve_activity_optimized(work_centers, operations, horizon=1000, alpha=0.5)
    assert result["status"] in ("OPTIMAL", "FEASIBLE", "HEURISTIC")
    assert "activity_cost_breakdown" in result
    breakdown = result["activity_cost_breakdown"]
    assert "total_usd" in breakdown
    assert breakdown["total_usd"] >= 0
