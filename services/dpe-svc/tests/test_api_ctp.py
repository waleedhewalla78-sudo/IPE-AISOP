import os
os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

USER_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
TENANT_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")

DB_AVAILABLE = bool(os.environ.get("IPE_DATABASE_URL_SYNC") or os.environ.get("DATABASE_URL"))
skip_if_no_db = pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")


def _auth_headers():
    from ipe_shared.testing.conftest_helpers import make_auth_headers
    return make_auth_headers(role="planner", tenant_id=TENANT_ID)


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
        user_id=USER_ID,
        tenant_id=TENANT_ID,
    )

    async def _mock_get_session():
        yield make_mock_session()

    _app.dependency_overrides[get_db_session] = _mock_get_session

    yield _app

    _app.dependency_overrides.clear()


@pytest.fixture
async def ctp_client(app_with_overrides):
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app_with_overrides)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_ctp_evaluate_valid_request(ctp_client):
    response = await ctp_client.post(
        "/api/v1/ctp/evaluate",
        json={
            "so_id": 1001,
            "product_id": 2001,
            "requested_qty": 50,
            "requested_delivery_date": "2026-07-15T00:00:00",
            "customer_priority": "high",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert "is_feasible" in data
    assert "confidence_score" in data
    assert 0 <= data["confidence_score"] <= 100


@pytest.mark.asyncio
async def test_ctp_evaluate_missing_required_fields(ctp_client):
    response = await ctp_client.post(
        "/api/v1/ctp/evaluate",
        json={},
        headers=_auth_headers(),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ctp_evaluate_invalid_so_id(ctp_client):
    response = await ctp_client.post(
        "/api/v1/ctp/evaluate",
        json={
            "so_id": -1,
            "product_id": 2001,
            "requested_qty": 50,
            "requested_delivery_date": "2026-07-15T00:00:00",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ctp_evaluate_zero_quantity(ctp_client):
    response = await ctp_client.post(
        "/api/v1/ctp/evaluate",
        json={
            "so_id": 1001,
            "product_id": 2001,
            "requested_qty": 0,
            "requested_delivery_date": "2026-07-15T00:00:00",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ctp_evaluate_no_auth(client):
    response = await client.post(
        "/api/v1/ctp/evaluate",
        json={
            "so_id": 1001,
            "product_id": 2001,
            "requested_qty": 50,
            "requested_delivery_date": "2026-07-15T00:00:00",
        },
    )
    assert response.status_code in (400, 401, 403)
