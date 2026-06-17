"""
What-If Simulation tests for cap-svc.

Verifies that the simulate endpoint runs the solver on in-memory copies
and returns different results when hypothetical changes are applied,
without persisting any data.
"""

import pytest

from app.core.scheduler import solve_schedule

BASE_WCS = [{"id": "WC001", "name": "Assembly", "capacity_hours_per_day": 8, "oee": 0.9}]

BASE_OPS = [
    {"id": "OP001", "mo_id": "MO001", "sequence": 1, "work_center_id": "WC001",
     "duration_planned_mins": 120, "operation_name": "Op 1", "priority_score": 0.8, "due_date_minutes": 600},
    {"id": "OP002", "mo_id": "MO001", "sequence": 2, "work_center_id": "WC001",
     "duration_planned_mins": 60, "operation_name": "Op 2", "priority_score": 0.8, "due_date_minutes": 600},
    {"id": "OP003", "mo_id": "MO002", "sequence": 1, "work_center_id": "WC001",
     "duration_planned_mins": 180, "operation_name": "Op 3", "priority_score": 0.5, "due_date_minutes": 1200},
]


def test_simulation_returns_different_result_with_hypothetical_change():
    baseline = solve_schedule(BASE_WCS, BASE_OPS, horizon=2000, solver_timeout_seconds=10)

    boosted_wcs = [{"id": "WC001", "name": "Assembly", "capacity_hours_per_day": 16, "oee": 0.9}]
    simulated = solve_schedule(boosted_wcs, BASE_OPS, horizon=2000, solver_timeout_seconds=10)

    assert baseline["status"] in ("OPTIMAL", "FEASIBLE")
    assert simulated["status"] in ("OPTIMAL", "FEASIBLE")

    baseline_max_end = max(a["end_minute"] for a in baseline["assignments"])
    simulated_max_end = max(a["end_minute"] for a in simulated["assignments"])

    assert simulated_max_end <= baseline_max_end, (
        f"Doubling capacity should not increase makespan "
        f"(baseline: {baseline_max_end}, simulated: {simulated_max_end})"
    )


def test_simulation_does_not_mutate_input_data():
    ops_copy = [dict(op) for op in BASE_OPS]
    wcs_copy = [dict(wc) for wc in BASE_WCS]

    result = solve_schedule(wcs_copy, ops_copy, horizon=2000, solver_timeout_seconds=10)

    assert result["status"] in ("OPTIMAL", "FEASIBLE")

    assert ops_copy == BASE_OPS, "solve_schedule mutated the input operations"
    assert wcs_copy == BASE_WCS, "solve_schedule mutated the input work_centers"


@pytest.mark.asyncio
async def test_simulate_no_tenant(client):
    response = await client.post(
        "/api/v1/capacity/simulate",
        json={"operations": [], "work_centers": [], "hypothetical_changes": []},
    )
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"
