"""Scenario API tests with mocked DB — R2-01."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_clone_scenario_with_tenant(client, auth_headers):
    mo_id = str(uuid4())
    mock_mo = MagicMock()
    mock_mo.id = uuid4()
    mock_mo.product_id = uuid4()

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.execute = AsyncMock(
        return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_mo]))))
    )

    with patch("app.api.v1.scenarios.tenant_ctx") as ctx, patch(
        "app.api.v1.scenarios.get_db_session", return_value=mock_session
    ):
        ctx.get.return_value = str(uuid4())
        from app.api.v1.scenarios import clone_scenario
        from ipe_shared.auth.jwt import TokenPayload

        user = TokenPayload(sub="u", tenant_id=ctx.get.return_value, role="planner", exp=9999999999)
        req = type("Req", (), {"mo_ids": [mo_id], "name": "Test", "description": None})()
        response = await clone_scenario(req, session=mock_session, current_user=user)

    assert response.success is True
    mock_session.commit.assert_awaited()
