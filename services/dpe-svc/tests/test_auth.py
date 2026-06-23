from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

TENANT_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
ADMIN_ID = UUID("c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c01")


def _user_row():
    return {
        "id": ADMIN_ID,
        "tenant_id": TENANT_ID,
        "email": "admin@demo.com",
        "full_name": "Alice Admin",
        "role": "admin",
        "password_hash": "$2b$12$placeholder",
        "is_active": True,
    }


@pytest.fixture
def auth_app():
    from app.main import create_app
    from ipe_shared.database.session import get_session

    app = create_app()

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.mappings.return_value.one_or_none.return_value = _user_row()
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def _mock_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = _mock_get_session
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(auth_app):
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=auth_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_login_success(auth_client):
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@demo.com", "password": "demo"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["access_token"]
    assert body["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(auth_client):
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@demo.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(auth_client):
    response = await auth_client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_user(auth_client):
    from ipe_shared.auth.jwt import create_access_token

    token = create_access_token(ADMIN_ID, TENANT_ID, "admin")
    response = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == "admin@demo.com"
    assert data["role"] == "admin"
