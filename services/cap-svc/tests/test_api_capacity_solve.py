from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

TENANT_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


def _auth_headers():
    from uuid import UUID
    from ipe_shared.testing.conftest_helpers import make_auth_headers
    return make_auth_headers(role="planner", tenant_id=UUID(TENANT_ID))


def _make_mock_session():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_scalars.one_or_none.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one_or_none.return_value = None
    mock_result.fetchone.return_value = (0, 0, 0)
    mock_result.fetchall.return_value = []
    mock_result.scalar.return_value = 0
    mock_session.execute = AsyncMock(return_value=mock_result)
    return mock_session


@pytest.fixture
def app_with_overrides():
    from app.main import create_app
    from ipe_shared.database.session import get_session as get_db_session
    from ipe_shared.testing.conftest_helpers import (
        apply_auth_and_session_overrides,
        make_mock_session,
    )
    from uuid import UUID

    _app = create_app()
    apply_auth_and_session_overrides(
        _app,
        role="planner",
        user_id=None,
        tenant_id=UUID(TENANT_ID),
    )

    async def _mock_get_session():
        yield make_mock_session()

    _app.dependency_overrides[get_db_session] = _mock_get_session

    yield _app

    _app.dependency_overrides.clear()


@pytest.fixture
async def client(app_with_overrides):
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app_with_overrides)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def mock_kafka():
    with patch("ipe_shared.events.producer.kafka_producer") as mock_producer:
        mock_producer.send_event = AsyncMock()
        mock_producer.send_avro = AsyncMock()
        mock_producer.build_envelope = MagicMock(return_value=MagicMock(model_dump=MagicMock(return_value={})))
        yield mock_producer


@pytest.mark.asyncio
async def test_capacity_solve_returns_success(client):
    response = await client.post(
        "/api/v1/capacity/solve",
        json={
            "horizon_hours": 168,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_capacity_solve_with_mo_ids(client):
    response = await client.post(
        "/api/v1/capacity/solve",
        json={
            "mo_ids": [str(uuid4())],
            "horizon_hours": 72,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_network_optimize_returns_success(client):
    response = await client.post(
        "/api/v1/capacity/network-optimize",
        json={
            "horizon_days": 14,
            "alpha": 0.5,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_green_schedule_returns_success(client):
    response = await client.post(
        "/api/v1/capacity/green-schedule",
        json={
            "horizon_hours": 168,
            "alpha": 0.5,
            "beta": 0.3,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
