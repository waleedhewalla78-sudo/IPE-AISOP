"""Scenario diff endpoint tests — R2-01."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.v1.scenarios import scenario_diff


@pytest.mark.asyncio
async def test_scenario_diff_with_disruptions():
    tid = str(uuid4())
    scenario_id = uuid4()
    scenario = MagicMock(name="Delay test")

    demand = MagicMock()
    demand.original_demand_id = uuid4()
    demand.data = {
        "quantity": 100,
        "planned_end": "2026-08-01T00:00:00Z",
        "feasibility_score": 0.9,
        "disrupted_end": "2026-08-04T00:00:00Z",
        "delay_days": 3,
        "supply_blocked": True,
        "material_score": 0.0,
    }

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=scenario)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[demand])))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ]
    )

    with patch("app.api.v1.scenarios.tenant_ctx") as ctx:
        ctx.get.return_value = tid
        response = await scenario_diff(scenario_id, session=session)

    assert response.success is True
    assert response.data["impact"]["blocked_count"] == 1
    assert response.data["impact"]["delayed_count"] == 1
