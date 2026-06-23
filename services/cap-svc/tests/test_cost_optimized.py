import pytest
from datetime import datetime
from app.core.energy_cost import (
    build_tou_rate_map,
    calculate_energy_cost,
    calculate_labor_cost,
)
from app.core.scheduler_cost import solve_cost_optimized


def test_build_tou_rate_map():
    tariffs = [
        {"day_of_week": 0, "hour_start": 0, "hour_end": 7, "rate_per_kwh": 0.10},
        {"day_of_week": 0, "hour_start": 8, "hour_end": 16, "rate_per_kwh": 0.20},
        {"day_of_week": 0, "hour_start": 17, "hour_end": 23, "rate_per_kwh": 0.15},
    ]
    rate_map = build_tou_rate_map(tariffs)
    assert rate_map[(0, 5)] == 0.10
    assert rate_map[(0, 12)] == 0.20
    assert rate_map[(0, 20)] == 0.15


def test_build_tou_rate_map_cross_midnight():
    tariffs = [
        {"day_of_week": 0, "hour_start": 22, "hour_end": 23, "rate_per_kwh": 0.08},
    ]
    rate_map = build_tou_rate_map(tariffs)
    assert rate_map[(0, 22)] == 0.08
    assert rate_map[(0, 23)] == 0.08
    assert (0, 24) not in rate_map


def test_calculate_energy_cost_basic():
    rate_map = {(0, 0): 0.20}
    result = calculate_energy_cost(
        operation_start_minute=0,
        duration_minutes=60,
        energy_kwh_per_hour=2.0,
        rate_map=rate_map,
    )
    assert result["total_energy_kwh"] == 2.0
    assert result["total_energy_cost"] == 0.40


def test_calculate_energy_cost_cross_hour_boundary():
    rate_map = {(0, 0): 0.20, (0, 1): 0.30}
    result = calculate_energy_cost(
        operation_start_minute=45,
        duration_minutes=60,
        energy_kwh_per_hour=2.0,
        rate_map=rate_map,
    )
    assert result["total_energy_kwh"] == 2.0
    assert result["total_energy_cost"] == 0.55


def test_calculate_energy_cost_zero_energy():
    rate_map = {(0, 8): 0.20}
    result = calculate_energy_cost(0, 60, 0.0, rate_map)
    assert result["total_energy_cost"] == 0.0


def test_calculate_energy_cost_empty_rate_map():
    result = calculate_energy_cost(0, 60, 2.0, {})
    assert result["total_energy_cost"] == 0.0


def test_calculate_labor_cost_regular_hours():
    result = calculate_labor_cost(
        duration_minutes=480,
        cost_per_hour=50.0,
        overtime_multiplier=1.5,
        regular_hours_per_day=8,
        operation_start_minute=480,
    )
    assert result["total_labor_cost"] == 400.0
    assert result["overtime_minutes"] == 0


def test_calculate_labor_cost_with_overtime():
    result = calculate_labor_cost(
        duration_minutes=600,
        cost_per_hour=50.0,
        overtime_multiplier=1.5,
        regular_hours_per_day=8,
        operation_start_minute=480,
    )
    assert result["overtime_minutes"] > 0
    assert result["overtime_cost"] > 0
    assert result["total_labor_cost"] == result["regular_cost"] + result["overtime_cost"]


def test_solve_cost_optimized_feasible():
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
            "due_date_minutes": 240,
        },
        {
            "id": "OP002",
            "mo_id": "MO001",
            "sequence": 2,
            "work_center_id": "WC001",
            "duration_planned_mins": 60,
            "operation_name": "Op 2",
            "priority_score": 0.9,
            "due_date_minutes": 300,
        },
    ]

    tariffs = [
        {"day_of_week": 0, "hour_start": 0, "hour_end": 7, "rate_per_kwh": 0.10},
        {"day_of_week": 0, "hour_start": 8, "hour_end": 16, "rate_per_kwh": 0.25},
    ]

    result = solve_cost_optimized(
        work_centers, operations, horizon=1000,
        solver_timeout_seconds=10, alpha=0.5, tariffs=tariffs,
    )

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert len(result["assignments"]) == 2
    assert "cost_summary" in result
    assert result["cost_summary"]["total_cost"] >= 0
    assert result["cost_summary"]["alpha"] == 0.5
    assert len(result["cost_breakdown"]) == 2


def test_solve_cost_optimized_alpha_range():
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
            "due_date_minutes": 240,
        },
    ]

    tariffs = [
        {"day_of_week": 0, "hour_start": 0, "hour_end": 23, "rate_per_kwh": 0.20},
    ]

    result_cost = solve_cost_optimized(
        work_centers, operations, horizon=1000,
        solver_timeout_seconds=10, alpha=0.1, tariffs=tariffs,
    )
    assert result_cost["cost_summary"]["alpha"] == 0.1

    result_speed = solve_cost_optimized(
        work_centers, operations, horizon=1000,
        solver_timeout_seconds=10, alpha=0.9, tariffs=tariffs,
    )
    assert result_speed["cost_summary"]["alpha"] == 0.9


def test_solve_cost_optimized_no_tariffs():
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
            "duration_planned_mins": 60,
            "operation_name": "Op 1",
            "priority_score": 0.9,
            "due_date_minutes": 240,
        },
    ]

    result = solve_cost_optimized(
        work_centers, operations, horizon=1000,
        solver_timeout_seconds=10, alpha=0.5, tariffs=[],
    )

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert result["cost_summary"]["total_energy_cost"] == 0.0


def test_solve_cost_optimized_no_overlap():
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
        {"id": "OP001", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001", "duration_planned_mins": 60, "operation_name": "Op 1", "priority_score": 0.9, "due_date_minutes": 240},
        {"id": "OP002", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001", "duration_planned_mins": 60, "operation_name": "Op 2", "priority_score": 0.9, "due_date_minutes": 300},
        {"id": "OP003", "mo_id": "MO002", "sequence": 1, "work_center_id": "WC001", "duration_planned_mins": 60, "operation_name": "Op 3", "priority_score": 0.5, "due_date_minutes": 360},
    ]

    result = solve_cost_optimized(
        work_centers, operations, horizon=1000,
        solver_timeout_seconds=10, alpha=0.5,
    )

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    wc_ops = sorted(
        [a for a in result["assignments"] if a["work_center_id"] == "WC001"],
        key=lambda a: a["start_minute"],
    )
    for i in range(len(wc_ops) - 1):
        assert wc_ops[i]["end_minute"] <= wc_ops[i + 1]["start_minute"]


def test_solve_cost_optimized_cost_breakdown_fields():
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
        {"id": "OP001", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001", "duration_planned_mins": 120, "operation_name": "Op 1", "priority_score": 0.9, "due_date_minutes": 240},
    ]

    tariffs = [
        {"day_of_week": 0, "hour_start": 0, "hour_end": 23, "rate_per_kwh": 0.20},
    ]

    result = solve_cost_optimized(
        work_centers, operations, horizon=1000,
        solver_timeout_seconds=10, alpha=0.5, tariffs=tariffs,
    )

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    summary = result["cost_summary"]
    assert "total_energy_kwh" in summary
    assert "total_energy_cost" in summary
    assert "total_labor_cost" in summary
    assert "total_cost" in summary
    assert "alpha" in summary
    assert "optimality_gap" in summary

    breakdown = result["cost_breakdown"][0]
    assert "operation_id" in breakdown
    assert "work_center_id" in breakdown
    assert "energy_kwh" in breakdown
    assert "energy_cost" in breakdown
    assert "labor_cost" in breakdown
    assert "overtime_minutes" in breakdown
