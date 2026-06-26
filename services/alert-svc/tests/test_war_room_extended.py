"""War room aggregate + recovery paths — R2-04."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.v1.war_room import aggregate_supplier_delay, recovery_plan
from ipe_shared.auth.jwt import TokenPayload


@pytest.mark.asyncio
async def test_aggregate_no_tenant():
    user = TokenPayload(sub="u", tenant_id=str(uuid4()), role="admin", exp=9999999999)
    response = await aggregate_supplier_delay(current_user=user)
    assert response.success is False
    assert response.error.code == "NO_TENANT"


@pytest.mark.asyncio
async def test_aggregate_success_severity_counts():
    tid = str(uuid4())
    user = TokenPayload(sub="u", tenant_id=tid, role="admin", exp=9999999999)

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "data": {
            "impacted_mos": [
                {"delay_days": 20},
                {"delay_days": 10},
                {"delay_days": 5},
                {"delay_days": 1},
            ],
            "total_cost_impact": 5000,
        }
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.api.v1.war_room.tenant_ctx") as ctx, patch(
        "app.api.v1.war_room.httpx.AsyncClient", return_value=mock_client
    ):
        ctx.get.return_value = tid
        response = await aggregate_supplier_delay(current_user=user)

    assert response.success is True
    counts = response.data["severity_counts"]
    assert counts["critical"] == 1
    assert counts["high"] == 1
    assert counts["medium"] == 1
    assert counts["low"] == 1


@pytest.mark.asyncio
async def test_aggregate_network_failure():
    tid = str(uuid4())
    user = TokenPayload(sub="u", tenant_id=tid, role="admin", exp=9999999999)

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=RuntimeError("network down"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.api.v1.war_room.tenant_ctx") as ctx, patch(
        "app.api.v1.war_room.httpx.AsyncClient", return_value=mock_client
    ):
        ctx.get.return_value = tid
        response = await aggregate_supplier_delay(current_user=user)

    assert response.success is False
    assert response.error.code == "AGGREGATE_FAILED"


@pytest.mark.asyncio
async def test_recovery_plan_with_disruption_and_scenarios():
    tid = uuid4()
    disruption = MagicMock()
    disruption.id = uuid4()
    disruption.mo_id = uuid4()
    disruption.event_metadata = {"impacted_mo_count": 2}

    scenario = MagicMock()
    scenario.id = uuid4()
    scenario.business_score = 0.9
    scenario.delivery_impact_days = 1
    scenario.cost_impact = 50.0
    scenario.description = "Reroute"
    scenario.strategy = "reroute"

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=disruption)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[scenario])))),
        ]
    )

    user = TokenPayload(sub="u1", tenant_id=str(tid), role="admin", exp=9999999999)

    with patch("app.api.v1.war_room.tenant_ctx") as ctx:
        ctx.get.return_value = str(tid)
        response = await recovery_plan(disruption_id=str(disruption.id), session=session, current_user=user)

    assert response.success is True
    assert response.data["impacted_mo_count"] == 2
    assert len(response.data["recovery_options"]) == 1


@pytest.mark.asyncio
async def test_recovery_plan_res_svc_fallback():
    tid = uuid4()
    disruption = MagicMock()
    disruption.id = uuid4()
    disruption.mo_id = uuid4()
    disruption.event_metadata = {}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": {
            "scenarios": [
                {
                    "id": "s1",
                    "business_score": 0.7,
                    "delivery_impact_days": 3,
                    "cost_impact": 200,
                    "strategy": "expedite",
                }
            ]
        }
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            MagicMock(scalar_one_or_none=MagicMock(return_value=disruption)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ]
    )

    user = TokenPayload(sub="u1", tenant_id=str(tid), role="admin", exp=9999999999)

    with patch("app.api.v1.war_room.tenant_ctx") as ctx, patch(
        "app.api.v1.war_room.httpx.AsyncClient", return_value=mock_client
    ):
        ctx.get.return_value = str(tid)
        response = await recovery_plan(disruption_id=str(disruption.id), session=session, current_user=user)

    assert response.success is True
    assert response.data["recovery_options"][0]["summary"] == "expedite"
