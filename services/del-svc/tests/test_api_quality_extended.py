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
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()
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
async def test_quality_create_event(client):
    with patch("app.api.v1.quality.kafka_producer") as mock_kafka:
        mock_kafka.build_envelope.return_value = {}
        mock_kafka.send_avro = AsyncMock()
        response = await client.post(
            "/api/v1/quality/events",
            json={
                "mo_id": str(uuid4()),
                "product_id": str(uuid4()),
                "event_type": "defect_detected",
                "severity": "minor",
                "defect_category": "surface",
                "defect_count": 2,
            },
            headers=_auth_headers(),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "decision" in data["data"]


@pytest.mark.asyncio
async def test_quality_list_events(client):
    response = await client.get(
        "/api/v1/quality/events",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_quality_no_auth():
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
        response = await ac.post(
            "/api/v1/quality/events",
            json={"mo_id": str(uuid4()), "product_id": str(uuid4()), "event_type": "defect_detected"},
        )
        assert response.status_code in (401, 403)

    _app.dependency_overrides.clear()
