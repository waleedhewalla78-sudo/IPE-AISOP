import os
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32chars!")

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from ipe_shared.config import settings
settings.JWT_SECRET_KEY = "test-secret-key-for-testing-only-32chars!"

TENANT_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


def _auth_headers():
    from ipe_shared.auth.jwt import create_access_token
    token = create_access_token(uuid4(), UUID(TENANT_ID), "planner")
    return {"Authorization": f"Bearer {token}"}


def _make_mock_session():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_scalars.one_or_none.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalar.return_value = 0
    mock_result.fetchone.return_value = (0, 0, 0)
    mock_result.fetchall.return_value = []
    mock_session.execute = AsyncMock(return_value=mock_result)
    return mock_session


@pytest.fixture
def app_with_overrides():
    from app.main import create_app
    from ipe_shared.auth.rbac import require_roles
    from ipe_shared.database.session import get_session as get_db_session

    _app = create_app()

    async def _mock_require_roles(*roles):
        return {"sub": str(uuid4()), "tenant_id": TENANT_ID, "role": "planner"}

    mock_session = _make_mock_session()

    async def _mock_get_session():
        yield mock_session

    _app.dependency_overrides[require_roles] = _mock_require_roles
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
async def test_feasibility_queue_returns_success(client):
    response = await client.get(
        "/api/v1/feasibility/queue",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_feasibility_queue_with_tenant(client):
    response = await client.get(
        "/api/v1/feasibility/queue",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_feasibility_kpis_returns_success(client):
    response = await client.get(
        "/api/v1/feasibility/kpis",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_feasibility_kpis_structure(client):
    response = await client.get(
        "/api/v1/feasibility/kpis",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "avg_feasibility_score" in data["data"]
    assert "active_bottlenecks" in data["data"]
    assert "orders_at_risk" in data["data"]
    assert data["data"]["otd_pct"] is None
