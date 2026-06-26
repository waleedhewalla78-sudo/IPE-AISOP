"""Scenario disruption injection with mocked DB — R2-01."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.v1.scenarios import DisruptionInjection, DisruptionRequest, inject_disruption
from ipe_shared.auth.jwt import TokenPayload


@pytest.mark.asyncio
async def test_inject_disruption_not_found():
    tid = str(uuid4())
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    user = TokenPayload(sub="u", tenant_id=tid, role="planner", exp=9999999999)

    with patch("app.api.v1.scenarios.tenant_ctx") as ctx:
        ctx.get.return_value = tid
        response = await inject_disruption(
            uuid4(),
            DisruptionRequest(disruptions=[]),
            session=session,
            current_user=user,
        )

    assert response.success is False
    assert response.error.code == "NOT_FOUND"


@pytest.mark.asyncio
async def test_inject_disruption_applies_delay_and_capacity():
    tid = str(uuid4())
    scenario_id = uuid4()
    mo_id = uuid4()

    scenario = MagicMock(id=scenario_id)
    demand = MagicMock()
    demand.original_demand_id = mo_id
    demand.data = {
        "planned_end": datetime(2026, 7, 1, tzinfo=UTC).isoformat(),
        "material_score": 0.9,
    }
    supply = MagicMock()
    supply.data = {"mo_id": str(mo_id), "duration_planned_mins": 60}
    resource = MagicMock()
    resource.data = {"work_center_id": str(uuid4())}

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=scenario)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[demand])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[supply])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[resource])))),
        ]
    )
    session.commit = AsyncMock()

    user = TokenPayload(sub="u", tenant_id=tid, role="planner", exp=9999999999)
    req = DisruptionRequest(
        disruptions=[
            DisruptionInjection(mo_id=mo_id, delay_days=3, capacity_multiplier=0.5, supply_blocked=True)
        ]
    )

    with patch("app.api.v1.scenarios.tenant_ctx") as ctx:
        ctx.get.return_value = tid
        response = await inject_disruption(scenario_id, req, session=session, current_user=user)

    assert response.success is True
    assert demand.data["supply_blocked"] is True
    assert demand.data["delay_days"] == 3
    session.commit.assert_awaited()
