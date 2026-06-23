import os
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32chars!")

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ipe_shared.config import settings
settings.JWT_SECRET_KEY = "test-secret-key-for-testing-only-32chars!"

DB_AVAILABLE = bool(os.environ.get("IPE_DATABASE_URL_SYNC") or os.environ.get("DATABASE_URL"))
skip_if_no_db = pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")


def _auth_headers():
    from ipe_shared.auth.jwt import create_access_token
    token = create_access_token(uuid4(), uuid4(), "planner")
    return {"Authorization": f"Bearer {token}"}


def _admin_headers():
    from ipe_shared.auth.jwt import create_access_token
    token = create_access_token(uuid4(), uuid4(), "admin")
    return {"Authorization": f"Bearer {token}"}


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
    from ipe_shared.auth.rbac import require_roles
    from ipe_shared.database.session import get_session as get_db_session

    _app = create_app()

    async def _mock_require_roles(*roles):
        return {"sub": str(uuid4()), "tenant_id": str(uuid4()), "role": "planner"}

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


@pytest.mark.asyncio
async def test_capacity_solve_valid(client):
    response = await client.post(
        "/api/v1/capacity/solve",
        json={
            "mo_ids": [str(uuid4())],
            "horizon_hours": 168,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_capacity_solve_empty_mos(client):
    response = await client.post(
        "/api/v1/capacity/solve",
        json={},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_capacity_solve_no_auth(client):
    response = await client.post(
        "/api/v1/capacity/solve",
        json={},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_network_optimize_valid(client):
    response = await client.post(
        "/api/v1/capacity/network-optimize",
        json={
            "demand_ids": [str(uuid4())],
            "alpha": 0.5,
            "horizon_days": 14,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_network_optimize_no_auth(client):
    response = await client.post(
        "/api/v1/capacity/network-optimize",
        json={},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_green_schedule_valid(client):
    response = await client.post(
        "/api/v1/capacity/green-schedule",
        json={
            "mo_ids": [str(uuid4())],
            "horizon_hours": 168,
            "alpha": 0.5,
            "beta": 0.5,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_green_schedule_no_auth(client):
    response = await client.post(
        "/api/v1/capacity/green-schedule",
        json={},
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_cost_optimized_valid(client):
    response = await client.post(
        "/api/v1/capacity/cost-optimized",
        json={
            "mo_ids": [str(uuid4())],
            "horizon_hours": 168,
            "alpha": 0.5,
            "tariffs": [
                {
                    "day_of_week": 0,
                    "hour_start": 0,
                    "hour_end": 23,
                    "rate_per_kwh": 0.20,
                }
            ],
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_cost_optimized_no_auth(client):
    response = await client.post(
        "/api/v1/capacity/cost-optimized",
        json={},
    )
    assert response.status_code in (401, 403)
