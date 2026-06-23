import os
os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from ipe_shared.config import settings
settings.JWT_SECRET_KEY = "dev-jwt-secret-change-in-production-min-32-chars"

DB_AVAILABLE = bool(os.environ.get("IPE_DATABASE_URL_SYNC") or os.environ.get("DATABASE_URL"))
skip_if_no_db = pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")


def _auth_headers():
    from ipe_shared.auth.jwt import create_access_token
    token = create_access_token(uuid4(), uuid4(), "planner")
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

    from datetime import datetime, UTC
    mock_mo_row = ("planned", 80.0, None, None, uuid4())
    mock_result.one_or_none = MagicMock(return_value=mock_mo_row)

    mock_session.execute = AsyncMock(return_value=mock_result)
    return mock_session


@pytest.fixture
def app_with_overrides():
    from app.main import create_app
    from ipe_shared.auth.dependencies import get_current_user
    from ipe_shared.auth.jwt import TokenPayload
    from ipe_shared.database.session import get_session

    _app = create_app()

    async def _mock_current_user():
        return TokenPayload(sub=str(uuid4()), tenant_id=str(uuid4()), role="planner", type="access")

    mock_session = _make_mock_session()

    async def _mock_get_session():
        yield mock_session

    _app.dependency_overrides[get_current_user] = _mock_current_user
    _app.dependency_overrides[get_session] = _mock_get_session

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
    with patch("app.api.v1.feasibility.kafka_producer") as mock_producer:
        mock_producer.send_event = AsyncMock()
        mock_producer.send_avro = AsyncMock()
        mock_producer.build_envelope = MagicMock(return_value=MagicMock(model_dump=MagicMock(return_value={})))
        yield mock_producer


@pytest.mark.asyncio
async def test_feasibility_rescore_valid(client):
    mo_id = uuid4()
    response = await client.post(
        f"/api/v1/feasibility/rescore/{mo_id}",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_feasibility_rescore_invalid_uuid(client):
    response = await client.post(
        "/api/v1/feasibility/rescore/not-a-uuid",
        headers=_auth_headers(),
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_feasibility_queue(client):
    response = await client.get(
        "/api/v1/feasibility/queue",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_feasibility_kpis(client):
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
    assert "otd_pct" in data["data"]


@pytest.mark.asyncio
async def test_feasibility_score_valid(client):
    response = await client.post(
        "/api/v1/feasibility/score",
        json={
            "mo_id": str(uuid4()),
            "demand_score": 90.0,
            "bom_score": 85.0,
            "material_score": 80.0,
            "capacity_score": 75.0,
            "labor_score": 90.0,
            "autonomy_mode": "shadow",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "feasibility_score" in data["data"]
    assert "gate_scores" in data["data"]
    assert "action_taken" in data["data"]
    assert "xai_explanation" in data["data"]


@pytest.mark.asyncio
async def test_feasibility_score_no_gate_scores(client):
    response = await client.post(
        "/api/v1/feasibility/score",
        json={
            "mo_id": str(uuid4()),
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["feasibility_score"] == 55.0


@pytest.mark.asyncio
async def test_feasibility_score_autonomous_mode(client):
    response = await client.post(
        "/api/v1/feasibility/score",
        json={
            "mo_id": str(uuid4()),
            "demand_score": 100.0,
            "bom_score": 100.0,
            "material_score": 95.0,
            "capacity_score": 100.0,
            "labor_score": 100.0,
            "autonomy_mode": "autonomous",
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["feasibility_score"] >= 90.0
    assert data["data"]["action_taken"] == "auto_confirmed"


@pytest.mark.asyncio
async def test_feasibility_score_no_auth(client):
    response = await client.post(
        "/api/v1/feasibility/score",
        json={
            "mo_id": str(uuid4()),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_compliance_kpis(client):
    response = await client.get(
        "/api/v1/feasibility/compliance-kpis",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "schedule_adherence" in data["data"]
    assert "ai_decisions" in data["data"]
    assert "cost_savings" in data["data"]
    assert "recent_audit_log" in data["data"]
