import os
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32chars!")

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ipe_shared.config import settings
settings.JWT_SECRET_KEY = "test-secret-key-for-testing-only-32chars!"

TENANT_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


def _auth_headers():
    from ipe_shared.auth.jwt import create_access_token
    token = create_access_token(uuid4(), TENANT_ID, "admin")
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(TENANT_ID)}


def _make_mock_session():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_scalars.one_or_none.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one_or_none.return_value = None
    mock_result.fetchone.return_value = ({},)
    mock_result.fetchall.return_value = []
    mock_result.scalar.return_value = 0
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    return mock_session


@pytest.fixture
def app_with_overrides():
    from app.main import create_app
    from ipe_shared.auth.dependencies import get_current_user
    from ipe_shared.database.session import get_session as get_db_session

    _app = create_app()

    from ipe_shared.auth.jwt import TokenPayload
    mock_user = TokenPayload(sub=str(uuid4()), tenant_id=str(TENANT_ID), role="admin")

    async def _mock_get_current_user():
        return mock_user

    mock_session = _make_mock_session()

    async def _mock_get_session():
        yield mock_session

    _app.dependency_overrides[get_current_user] = _mock_get_current_user
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
async def test_labor_list_skills(client):
    response = await client.get("/api/v1/labor/skills", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_labor_create_skill(client):
    response = await client.post(
        "/api/v1/labor/skills",
        json={"name": "CNC Operator", "category": "manufacturing", "certification_required": True},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"]
    assert data["data"]["name"] == "CNC Operator"


@pytest.mark.asyncio
async def test_labor_list_workers(client):
    response = await client.get("/api/v1/labor/workers", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_labor_create_worker(client):
    response = await client.post(
        "/api/v1/labor/workers",
        json={
            "erp_source_id": "WO-001",
            "name": "John Doe",
            "cost_per_hour": 45.0,
            "overtime_eligible": True,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "John Doe"


@pytest.mark.asyncio
async def test_labor_list_shifts(client):
    response = await client.get("/api/v1/labor/shifts", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_labor_create_shift(client):
    response = await client.post(
        "/api/v1/labor/shifts",
        json={
            "name": "Day Shift",
            "days_of_week": [0, 1, 2, 3, 4],
            "start_hour": 6,
            "end_hour": 14,
            "break_minutes": 30,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Day Shift"


@pytest.mark.asyncio
async def test_labor_no_auth_skills():
    from httpx import ASGITransport, AsyncClient
    from app.main import create_app
    from ipe_shared.database.session import get_session as get_db_session

    _app = create_app()
    mock_session = _make_mock_session()

    async def _mock_get_session():
        yield mock_session

    _app.dependency_overrides[get_db_session] = _mock_get_session

    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/labor/skills")
        assert response.status_code == 200

    _app.dependency_overrides.clear()
