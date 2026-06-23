import os
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32chars!")

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ipe_shared.config import settings
settings.JWT_SECRET_KEY = "test-secret-key-for-testing-only-32chars!"

TENANT_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

DB_AVAILABLE = bool(os.environ.get("IPE_DATABASE_URL_SYNC") or os.environ.get("DATABASE_URL"))
skip_if_no_db = pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")


def _auth_headers():
    from ipe_shared.auth.jwt import create_access_token
    token = create_access_token(uuid4(), UUID(TENANT_ID), "planner")
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT_ID}


def _make_mock_session():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_scalars.one_or_none.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one_or_none.return_value = None
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


@pytest.mark.asyncio
async def test_material_ctp_valid(client):
    response = await client.post(
        "/api/v1/material/ctp",
        json={
            "order_id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 100,
            "required_date": "2026-07-15T00:00:00",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_material_ctp_missing_fields(client):
    response = await client.post(
        "/api/v1/material/ctp",
        json={},
        headers=_auth_headers(),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_material_ctp_invalid_uuid(client):
    response = await client.post(
        "/api/v1/material/ctp",
        json={
            "order_id": "not-a-uuid",
            "product_id": str(uuid4()),
            "quantity": 100,
            "required_date": "2026-07-15T00:00:00",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_material_ctp_no_auth(client):
    response = await client.post(
        "/api/v1/material/ctp",
        json={
            "order_id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 100,
            "required_date": "2026-07-15T00:00:00",
        },
    )
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_material_ctp_batch_valid(client):
    response = await client.post(
        "/api/v1/material/ctp/batch",
        json={
            "orders": [
                {
                    "order_id": str(uuid4()),
                    "product_id": str(uuid4()),
                    "quantity": 50,
                    "required_date": "2026-07-15T00:00:00",
                },
                {
                    "order_id": str(uuid4()),
                    "product_id": str(uuid4()),
                    "quantity": 100,
                    "required_date": "2026-07-20T00:00:00",
                },
            ]
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_material_ctp_batch_empty(client):
    response = await client.post(
        "/api/v1/material/ctp/batch",
        json={"orders": []},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_material_ctp_batch_no_auth(client):
    response = await client.post(
        "/api/v1/material/ctp/batch",
        json={"orders": []},
    )
    assert response.status_code in (401, 403)
