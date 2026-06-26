"""War room recovery-plan with mocked DB — R2-04."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.v1.war_room import recovery_plan
from ipe_shared.auth.jwt import TokenPayload


@pytest.mark.asyncio
async def test_recovery_plan_proposed_scenarios_without_disruption():
    tid = uuid4()
    scenario = MagicMock()
    scenario.id = uuid4()
    scenario.mo_id = uuid4()
    scenario.business_score = 0.85
    scenario.delivery_impact_days = 2
    scenario.cost_impact = 100.0
    scenario.description = "Expedite supplier"
    scenario.strategy = "expedite"

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[scenario])))),
        ]
    )

    user = TokenPayload(sub="u1", tenant_id=str(tid), role="admin", exp=9999999999)

    with patch("app.api.v1.war_room.tenant_ctx") as ctx:
        ctx.get.return_value = str(tid)
        response = await recovery_plan(disruption_id=None, session=session, current_user=user)

    assert response.success is True
    assert len(response.data["recovery_options"]) == 1
    assert response.data["recovery_options"][0]["rank"] == 1
