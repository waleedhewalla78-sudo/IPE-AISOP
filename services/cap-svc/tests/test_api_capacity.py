import pytest

from app.core.bottleneck import detect_bottlenecks
from app.core.scheduler import solve_schedule
from app.core.scheduler_cost import solve_cost_optimized

INVALID_UUIDS = ["not-a-uuid", "123", "abc-def-ghi", "", "null", "None"]


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "cap-svc"


@pytest.mark.asyncio
async def test_schedule_no_tenant(client):
    response = await client.post("/api/v1/capacity/schedule", json={})
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"


@pytest.mark.parametrize("bad_uuid", INVALID_UUIDS)
@pytest.mark.asyncio
async def test_schedule_invalid_uuid_returns_422(bad_uuid, client):
    """Prompt 1.1: Invalid UUID in mo_ids is rejected by Pydantic validation."""
    response = await client.post(
        "/api/v1/capacity/schedule",
        json={"mo_ids": [bad_uuid]},
    )
    assert response.status_code == 422


def test_solver_returns_valid_schedule():
    work_centers = [{"id": "WC001", "name": "Assembly", "capacity_hours_per_day": 16, "oee": 0.9}]

    operations = [
        {"id": "OP001", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001", "duration_planned_mins": 60, "operation_name": "Op 1", "priority_score": 0.9, "due_date_minutes": 240},
        {"id": "OP002", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001", "duration_planned_mins": 30, "operation_name": "Op 2", "priority_score": 0.9, "due_date_minutes": 240},
        {"id": "OP003", "mo_id": "MO002", "sequence": 1, "work_center_id": "WC001", "duration_planned_mins": 45, "operation_name": "Op 3", "priority_score": 0.5, "due_date_minutes": 480},
        {"id": "OP004", "mo_id": "MO002", "sequence": 2, "work_center_id": "WC001", "duration_planned_mins": 90, "operation_name": "Op 4", "priority_score": 0.5, "due_date_minutes": 480},
    ]

    result = solve_schedule(work_centers, operations, horizon=1000, solver_timeout_seconds=10)

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert len(result["assignments"]) == 4
    assert result["mo_tardiness"] is not None

    wc_assignments = [a for a in result["assignments"] if a["work_center_id"] == "WC001"]
    wc_assignments.sort(key=lambda a: a["start_minute"])

    for i in range(len(wc_assignments) - 1):
        assert wc_assignments[i]["end_minute"] <= wc_assignments[i + 1]["start_minute"], \
            f"Overlap detected between {wc_assignments[i]['operation_id']} and {wc_assignments[i+1]['operation_id']}"

    mo001_ops = sorted([a for a in result["assignments"] if a["mo_id"] == "MO001"], key=lambda a: a["sequence"])
    assert mo001_ops[0]["end_minute"] <= mo001_ops[1]["start_minute"], "Precedence violation in MO001"

    assert len(result["mo_tardiness"]) == 2


def test_bottleneck_detection():
    work_centers = [
        {"id": "WC001", "name": "Assembly", "capacity_hours_per_day": 8, "oee": 0.9},
        {"id": "WC002", "name": "Machining", "capacity_hours_per_day": 8, "oee": 0.9},
    ]

    assignments = [
        {"operation_id": "OP001", "work_center_id": "WC001", "duration": 960},
        {"operation_id": "OP002", "work_center_id": "WC001", "duration": 960},
        {"operation_id": "OP003", "work_center_id": "WC002", "duration": 120},
    ]

    bottlenecks = detect_bottlenecks(assignments, work_centers, horizon_minutes=1440)

    wc1_bn = [b for b in bottlenecks if b["work_center_id"] == "WC001"]
    wc2_bn = [b for b in bottlenecks if b["work_center_id"] == "WC002"]

    assert len(wc1_bn) == 1
    assert wc1_bn[0]["is_bottleneck"] is True
    assert wc1_bn[0]["utilization_pct"] > 85

    assert len(wc2_bn) == 1
    assert wc2_bn[0]["is_bottleneck"] is False


def test_frozen_horizon_respects_fixed_ops():
    """Frozen operations must keep their exact start/end times."""
    work_centers = [{"id": "WC001", "name": "Assembly", "capacity_hours_per_day": 16, "oee": 0.9}]
    operations = [
        {"id": "OP001", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001", "duration_planned_mins": 60, "operation_name": "Op 1", "priority_score": 0.9, "due_date_minutes": 480},
        {"id": "OP002", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001", "duration_planned_mins": 30, "operation_name": "Op 2", "priority_score": 0.9, "due_date_minutes": 480},
    ]
    frozen = [
        {"operation_id": "OP001", "fixed_start": 100, "fixed_end": 160},
    ]

    result = solve_schedule(work_centers, operations, horizon=1000, solver_timeout_seconds=10, frozen_ops=frozen)

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    op1 = [a for a in result["assignments"] if a["operation_id"] == "OP001"][0]
    assert op1["start_minute"] == 100
    assert op1["end_minute"] == 160


def test_warm_start_hints_accepted():
    """Warm start hints should not prevent a feasible solution."""
    work_centers = [{"id": "WC001", "name": "Assembly", "capacity_hours_per_day": 16, "oee": 0.9}]
    operations = [
        {"id": "OP001", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001", "duration_planned_mins": 60, "operation_name": "Op 1", "priority_score": 0.9, "due_date_minutes": 480},
        {"id": "OP002", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001", "duration_planned_mins": 30, "operation_name": "Op 2", "priority_score": 0.9, "due_date_minutes": 480},
    ]

    result = solve_schedule(work_centers, operations, horizon=1000, solver_timeout_seconds=10, warm_start={"OP001": 50, "OP002": 150})

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert len(result["assignments"]) == 2


def test_frozen_and_warm_start_together():
    """Combining frozen ops and warm start should produce a valid schedule."""
    work_centers = [{"id": "WC001", "name": "Assembly", "capacity_hours_per_day": 16, "oee": 0.9}]
    operations = [
        {"id": "OP001", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001", "duration_planned_mins": 60, "operation_name": "Op 1", "priority_score": 0.9, "due_date_minutes": 480},
        {"id": "OP002", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001", "duration_planned_mins": 30, "operation_name": "Op 2", "priority_score": 0.9, "due_date_minutes": 480},
        {"id": "OP003", "mo_id": "MO002", "sequence": 1, "work_center_id": "WC001", "duration_planned_mins": 45, "operation_name": "Op 3", "priority_score": 0.5, "due_date_minutes": 720},
    ]
    frozen = [
        {"operation_id": "OP001", "fixed_start": 0, "fixed_end": 60},
    ]

    result = solve_schedule(work_centers, operations, horizon=1000, solver_timeout_seconds=10, frozen_ops=frozen, warm_start={"OP003": 200})

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    op1 = [a for a in result["assignments"] if a["operation_id"] == "OP001"][0]
    assert op1["start_minute"] == 0
    assert op1["end_minute"] == 60

    wc_assignments = sorted([a for a in result["assignments"] if a["work_center_id"] == "WC001"], key=lambda a: a["start_minute"])
    for i in range(len(wc_assignments) - 1):
        assert wc_assignments[i]["end_minute"] <= wc_assignments[i + 1]["start_minute"], "No-overlap violated with frozen ops"


@pytest.mark.asyncio
async def test_cost_optimized_no_tenant(client):
    response = await client.post("/api/v1/capacity/cost-optimized", json={})
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"


def test_cost_optimized_solver_returns_valid():
    work_centers = [{
        "id": "WC001", "name": "Assembly",
        "capacity_hours_per_day": 16, "oee": 0.9,
        "energy_kwh_per_hour": 2.0, "cost_per_hour": 60.0,
        "overtime_cost_multiplier": 1.5,
    }]

    operations = [
        {"id": "OP001", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001", "duration_planned_mins": 60, "operation_name": "Op 1", "priority_score": 0.9, "due_date_minutes": 240},
        {"id": "OP002", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001", "duration_planned_mins": 30, "operation_name": "Op 2", "priority_score": 0.9, "due_date_minutes": 240},
    ]

    tariffs = [
        {"day_of_week": 0, "hour_start": 0, "hour_end": 23, "rate_per_kwh": 0.20},
    ]

    result = solve_cost_optimized(
        work_centers, operations, horizon=1000,
        solver_timeout_seconds=10, alpha=0.5, tariffs=tariffs,
    )

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert len(result["assignments"]) == 2
    assert "cost_summary" in result
    assert "cost_breakdown" in result

    wc_assignments = [a for a in result["assignments"] if a["work_center_id"] == "WC001"]
    wc_assignments.sort(key=lambda a: a["start_minute"])
    for i in range(len(wc_assignments) - 1):
        assert wc_assignments[i]["end_minute"] <= wc_assignments[i + 1]["start_minute"]
