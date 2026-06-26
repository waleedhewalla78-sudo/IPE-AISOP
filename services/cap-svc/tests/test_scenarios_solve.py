"""Scenario solve with mocked solver — R2-01."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.v1.scenarios import solve_scenario
from ipe_shared.auth.jwt import TokenPayload


@pytest.mark.asyncio
async def test_solve_scenario_no_data():
    tid = str(uuid4())
    scenario_id = uuid4()
    scenario = MagicMock(id=scenario_id)

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=scenario)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ]
    )

    user = TokenPayload(sub="u", tenant_id=tid, role="planner", exp=9999999999)

    with patch("app.api.v1.scenarios.tenant_ctx") as ctx:
        ctx.get.return_value = tid
        response = await solve_scenario(scenario_id, session=session, current_user=user)

    assert response.success is True
    assert response.data["schedule"]["status"] == "NO_DATA"


@pytest.mark.asyncio
async def test_solve_scenario_with_ops():
    tid = str(uuid4())
    scenario_id = uuid4()
    mo_id = str(uuid4())
    scenario = MagicMock(id=scenario_id)

    demand = MagicMock()
    demand.original_demand_id = uuid4()
    demand.data = {
        "mo_id": mo_id,
        "planned_end": datetime(2026, 8, 1, tzinfo=UTC).isoformat(),
        "feasibility_score": 0.8,
        "material_score": 1.0,
    }
    supply = MagicMock()
    supply.data = {
        "mo_id": mo_id,
        "routing_id": str(uuid4()),
        "work_center_id": str(uuid4()),
        "sequence": 1,
        "duration_planned_mins": 60,
        "operation_name": "Cut",
    }
    resource = MagicMock()
    resource.data = {
        "work_center_id": supply.data["work_center_id"],
        "name": "WC-1",
        "capacity_hours_per_day": 8,
        "oee": 0.9,
    }

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=scenario)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[demand])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[supply])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[resource])))),
        ]
    )

    user = TokenPayload(sub="u", tenant_id=tid, role="planner", exp=9999999999)

    with patch("app.api.v1.scenarios.tenant_ctx") as ctx, patch(
        "app.api.v1.scenarios.solve_schedule",
        return_value={"solver_status": "OPTIMAL", "assignments": []},
    ), patch("app.api.v1.scenarios.log_audit_event", new_callable=AsyncMock):
        ctx.get.return_value = tid
        response = await solve_scenario(scenario_id, session=session, current_user=user)

    assert response.success is True
    assert response.data["total_operations"] == 1
    assert response.data["schedule"]["solver_status"] == "OPTIMAL"
