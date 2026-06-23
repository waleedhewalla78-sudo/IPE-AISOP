import os
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only-32chars!")

from unittest.mock import AsyncMock, MagicMock, patch
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
async def test_sync_run_no_tenant(client):
    response = await client.post(
        "/api/v1/sync/run",
        json={
            "odoo_url": "http://localhost:8069",
            "odoo_db": "test_db",
            "odoo_username": "admin",
            "odoo_password": "admin",
            "entity": "all",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] in ("NOT_FOUND", "ODOO_CONNECT_FAILED")


@pytest.mark.asyncio
async def test_sync_run_products(client):
    response = await client.post(
        "/api/v1/sync/run",
        json={
            "odoo_url": "http://localhost:8069",
            "odoo_db": "test_db",
            "odoo_username": "admin",
            "odoo_password": "admin",
            "entity": "products",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_action_receive_hmac(client):
    import hashlib
    import hmac as hmac_mod
    import json

    body = json.dumps({"action": "confirm_mo", "mo_id": str(uuid4())})
    signature = hmac_mod.new(b"test-secret", body.encode(), hashlib.sha256).hexdigest()

    mock_tenant = MagicMock()
    mock_tenant.api_secret = "test-secret"

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_tenant
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    with patch("app.api.v1.action.get_engine") as mock_engine_fn:
        mock_engine_fn.return_value = MagicMock()
        with patch("app.api.v1.action.async_sessionmaker", return_value=mock_factory):
            response = await client.post(
                "/api/v1/ipe/action",
                content=body,
                headers={
                    "X-IPE-Signature": signature,
                    "X-Tenant-ID": str(TENANT_ID),
                    "Content-Type": "application/json",
                },
            )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["action"] == "confirm_mo"
    assert data["data"]["status"] == "received"


@pytest.mark.asyncio
async def test_action_missing_signature(client):
    response = await client.post(
        "/api/v1/ipe/action",
        json={"action": "test"},
        headers={"X-Tenant-ID": str(TENANT_ID)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "MISSING_SIGNATURE"


@pytest.mark.asyncio
async def test_action_missing_tenant(client):
    response = await client.post(
        "/api/v1/ipe/action",
        json={"action": "test"},
        headers={"X-IPE-Signature": "fake-sig"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "MISSING_TENANT"
