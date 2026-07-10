import os
os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

USER_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
TENANT_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


def _auth_headers():
    from ipe_shared.testing.conftest_helpers import make_auth_headers
    return make_auth_headers(role="planner", tenant_id=TENANT_ID)


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
async def client(app_with_overrides):
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app_with_overrides)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_ctp_evaluate_high_priority_feasible(client):
    response = await client.post(
        "/api/v1/ctp/evaluate",
        json={
            "so_id": 1001,
            "product_id": 2001,
            "requested_qty": 50,
            "requested_delivery_date": "2026-09-01T00:00:00",
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
async def test_ctp_evaluate_low_priority_near_date(client):
    response = await client.post(
        "/api/v1/ctp/evaluate",
        json={
            "so_id": 1002,
            "product_id": 2002,
            "requested_qty": 200,
            "requested_delivery_date": "2026-06-25T00:00:00",
            "customer_priority": "low",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert "is_feasible" in data
    assert "binding_constraint" in data


@pytest.mark.asyncio
async def test_ctp_evaluate_medium_priority_default(client):
    response = await client.post(
        "/api/v1/ctp/evaluate",
        json={
            "so_id": 1003,
            "product_id": 2003,
            "requested_qty": 100,
            "requested_delivery_date": "2026-08-01T00:00:00",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert "is_feasible" in data
    assert "constraint_resource" in data


@pytest.mark.asyncio
async def test_ctp_evaluate_large_quantity(client):
    response = await client.post(
        "/api/v1/ctp/evaluate",
        json={
            "so_id": 1004,
            "product_id": 2004,
            "requested_qty": 5000,
            "requested_delivery_date": "2026-09-15T00:00:00",
            "customer_priority": "high",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["confidence_score"] <= 85
