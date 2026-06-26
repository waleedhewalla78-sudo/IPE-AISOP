"""Kafka event handler tests (P8 R1-02)."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.events.handlers import _get_avro_payload, handle_capacity_scored, handle_material_scored


@pytest.mark.asyncio
async def test_get_avro_payload_envelope():
    assert await _get_avro_payload({"payload": {"mo_id": "1"}}) == {"mo_id": "1"}


@pytest.mark.asyncio
async def test_get_avro_payload_data_key():
    assert await _get_avro_payload({"data": {"x": 1}}) == {"x": 1}


@pytest.mark.asyncio
async def test_handle_material_scored_missing_tenant():
    with patch("app.events.handlers.tenant_ctx") as ctx:
        ctx.get.return_value = None
        await handle_material_scored({"payload": {"mo_id": str(uuid4()), "material_score": 80}})


@pytest.mark.asyncio
async def test_handle_material_scored_missing_score():
    with patch("app.events.handlers.tenant_ctx") as ctx:
        ctx.get.return_value = str(uuid4())
        await handle_material_scored({"payload": {"mo_id": str(uuid4())}})


@pytest.mark.asyncio
async def test_handle_capacity_scored_infeasible():
    mo_id = str(uuid4())
    tenant_id = str(uuid4())
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
    mock_session.commit = AsyncMock()

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.events.handlers.tenant_ctx") as ctx,
        patch("app.events.handlers.get_engine", return_value=MagicMock()),
        patch("app.events.handlers.async_sessionmaker", return_value=mock_factory),
        patch("app.events.handlers._score_and_publish", new_callable=AsyncMock) as pub,
    ):
        ctx.get.return_value = tenant_id
        await handle_capacity_scored(
            {"payload": {"mo_id": mo_id, "capacity_score": 50, "solver_status": "INFEASIBLE"}}
        )
        pub.assert_awaited_once()
