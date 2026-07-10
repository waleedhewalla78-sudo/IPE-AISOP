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
async def test_material_ctp_feasible_order(client):
    response = await client.post(
        "/api/v1/material/ctp",
        json={
            "order_id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 100,
            "required_date": "2026-08-01T00:00:00",
            "priority_score": 0.8,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "feasible" in data["data"]
    assert "confidence_score" in data["data"]


@pytest.mark.asyncio
async def test_material_ctp_large_quantity(client):
    response = await client.post(
        "/api/v1/material/ctp",
        json={
            "order_id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 5000,
            "required_date": "2026-07-01T00:00:00",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "material_feasible" in data["data"]
    assert "capacity_feasible" in data["data"]


@pytest.mark.asyncio
async def test_material_ctp_with_penalty_cost(client):
    response = await client.post(
        "/api/v1/material/ctp",
        json={
            "order_id": str(uuid4()),
            "product_id": str(uuid4()),
            "quantity": 200,
            "required_date": "2026-07-15T00:00:00",
            "penalty_cost": 500.0,
            "duration_mins_per_unit": 30.0,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "bottleneck" in data["data"]
    assert "material_gaps" in data["data"]
    assert "capacity_gaps" in data["data"]


@pytest.mark.asyncio
async def test_material_ctp_batch_returns_success(client):
    response = await client.post(
        "/api/v1/material/ctp/batch",
        json={
            "orders": [
                {
                    "order_id": str(uuid4()),
                    "product_id": str(uuid4()),
                    "quantity": 100,
                    "required_date": "2026-08-01T00:00:00",
                },
                {
                    "order_id": str(uuid4()),
                    "product_id": str(uuid4()),
                    "quantity": 200,
                    "required_date": "2026-08-15T00:00:00",
                },
            ],
            "duration_mins_per_unit": 60.0,
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "total_orders" in data["data"]
    assert "feasible_count" in data["data"]
