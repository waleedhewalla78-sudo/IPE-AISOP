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


@pytest.fixture
def app_with_overrides():
    from app.main import create_app
    from ipe_shared.auth.dependencies import get_current_user

    _app = create_app()

    from ipe_shared.auth.jwt import TokenPayload
    mock_user = TokenPayload(sub=str(uuid4()), tenant_id=str(TENANT_ID), role="admin")

    async def _mock_get_current_user():
        return mock_user

    _app.dependency_overrides[get_current_user] = _mock_get_current_user

    yield _app
    _app.dependency_overrides.clear()


@pytest.fixture
async def client(app_with_overrides):
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app_with_overrides)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_predict_duration_post(client):
    response = await client.post(
        "/api/v1/predict/duration",
        json={
            "product_id": "PROD-001",
            "work_center_id": "WC-001",
            "batch_size": 100.0,
            "duration_planned_mins": 60.0,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data


@pytest.mark.asyncio
async def test_predict_duration_get(client):
    response = await client.get(
        "/api/v1/predict/duration",
        params={
            "product_id": "PROD-001",
            "work_center_id": "WC-001",
            "batch_size": 100.0,
            "duration_planned_mins": 60.0,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_predict_duration_with_skill_tags(client):
    response = await client.post(
        "/api/v1/predict/duration",
        json={
            "product_id": "PROD-001",
            "work_center_id": "WC-001",
            "batch_size": 50.0,
            "duration_planned_mins": 30.0,
            "operator_skill_tags": ["cnc", "welding"],
            "historical_avg_ratio": 1.1,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_train_duration_model(client):
    response = await client.post(
        "/api/v1/predict/duration/train",
        json={
            "historical_records": [
                {"product_id": "P1", "work_center_id": "WC1", "batch_size": 100, "actual_duration": 45.0},
                {"product_id": "P1", "work_center_id": "WC1", "batch_size": 200, "actual_duration": 80.0},
            ]
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
