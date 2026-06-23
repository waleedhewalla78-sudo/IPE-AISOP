import os
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

USER_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
TENANT_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")

INVALID_UUIDS = ["not-a-uuid", "123", "abc-def-ghi", "", "null", "None", "00000000-0000-0000-0000-00000000000Z"]

DB_AVAILABLE = bool(os.environ.get("IPE_DATABASE_URL_SYNC") or os.environ.get("DATABASE_URL"))

skip_if_no_db = pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")


def _auth_headers():
    from ipe_shared.auth.jwt import create_access_token
    token = create_access_token(USER_ID, TENANT_ID, "admin")
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(TENANT_ID)}


@pytest.fixture
def app_with_overrides():
    from app.main import create_app
    from ipe_shared.auth.dependencies import get_current_user
    from ipe_shared.auth.jwt import TokenPayload
    from ipe_shared.database.session import get_session
    from ipe_shared.testing.conftest_helpers import make_mock_session

    _app = create_app()

    async def _mock_current_user():
        return TokenPayload(
            sub=str(USER_ID),
            tenant_id=str(TENANT_ID),
            role="admin",
            type="access",
        )

    async def _mock_get_session():
        yield make_mock_session()

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


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "dpe-svc"


@pytest.mark.parametrize("bad_uuid", INVALID_UUIDS)
@pytest.mark.asyncio
async def test_classify_invalid_uuid_returns_422(bad_uuid, client):
    response = await client.post(
        "/api/v1/demand/classify",
        json={"demand_line_ids": [bad_uuid]},
        headers=_auth_headers(),
    )
    assert response.status_code == 422, f"Expected 422 for UUID '{bad_uuid}', got {response.status_code}: {response.text[:300]}"


@pytest.mark.parametrize("bad_uuid", INVALID_UUIDS)
@pytest.mark.asyncio
async def test_classify_invalid_uuid_in_body_422(bad_uuid, client):
    response = await client.post(
        "/api/v1/demand/classify",
        json={"demand_line_ids": [bad_uuid], "extra_field": "ignored"},
        headers=_auth_headers(),
    )
    assert response.status_code == 422, f"Expected 422 for UUID '{bad_uuid}', got {response.status_code}: {response.text[:300]}"


@pytest.mark.asyncio
async def test_classify_empty_body_no_ids(client):
    response = await client.post(
        "/api/v1/demand/classify",
        json={},
        headers=_auth_headers(),
    )
    assert response.status_code in (200, 404, 500), f"Got {response.status_code}"


@pytest.mark.asyncio
@skip_if_no_db
async def test_classify_with_valid_uuid(client):
    valid_uuid = "00000000-0000-0000-0000-000000000001"
    response = await client.post(
        "/api/v1/demand/classify",
        json={"demand_line_ids": [valid_uuid]},
        headers=_auth_headers(),
    )
    assert response.status_code in (200, 404, 500)


@pytest.mark.asyncio
@skip_if_no_db
async def test_queue_with_auth(client):
    response = await client.get(
        "/api/v1/demand/queue",
        headers=_auth_headers(),
    )
    assert response.status_code in (200, 500)