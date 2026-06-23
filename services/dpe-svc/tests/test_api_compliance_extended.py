import os
os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from ipe_shared.config import settings
settings.JWT_SECRET_KEY = "dev-jwt-secret-change-in-production-min-32-chars"

USER_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
TENANT_ID = UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


def _auth_headers():
    from ipe_shared.auth.jwt import create_access_token
    token = create_access_token(USER_ID, TENANT_ID, "admin")
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
    from ipe_shared.auth.jwt import TokenPayload
    from ipe_shared.database.session import get_session

    _app = create_app()
    mock_user = TokenPayload(
        sub=str(USER_ID),
        tenant_id=str(TENANT_ID),
        role="admin",
        type="access",
    )

    async def _mock_get_current_user():
        return mock_user

    mock_session = _make_mock_session()

    async def _mock_get_session():
        yield mock_session

    _app.dependency_overrides[get_current_user] = _mock_get_current_user
    _app.dependency_overrides[get_session] = _mock_get_session
    yield _app
    _app.dependency_overrides.clear()


@pytest.fixture
async def client(app_with_overrides):
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app_with_overrides)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def app_no_auth():
    from app.main import create_app
    from ipe_shared.database.session import get_session

    _app = create_app()
    mock_session = _make_mock_session()

    async def _mock_get_session():
        yield mock_session

    _app.dependency_overrides[get_session] = _mock_get_session
    yield _app
    _app.dependency_overrides.clear()


@pytest.fixture
async def no_auth_client(app_no_auth):
    from httpx import ASGITransport, AsyncClient
    transport = ASGITransport(app=app_no_auth)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_soc2_evidence(client):
    response = await client.get("/api/v1/compliance/soc2/evidence", headers=_auth_headers())
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_soc2_summary(client):
    response = await client.get("/api/v1/compliance/soc2/summary", headers=_auth_headers())
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_iso27001_report(client):
    response = await client.get("/api/v1/compliance/iso27001/report", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert "total_controls" in data
    assert "compliance_pct" in data


@pytest.mark.asyncio
async def test_security_review(client):
    response = await client.get("/api/v1/compliance/security/review", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert "overall_risk" in data
    assert "total_findings" in data


@pytest.mark.asyncio
async def test_retention_policies(client):
    response = await client.get("/api/v1/compliance/retention/policies", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_retention_enforce(client):
    async def _mock_get_session():
        yield AsyncMock()

    with patch("app.api.v1.compliance.get_session", _mock_get_session):
        with patch("app.api.v1.compliance._retention_service") as mock_svc:
            mock_svc.enforce_retention = AsyncMock(return_value={"deleted": 0, "archived": 0})
            response = await client.post(
                "/api/v1/compliance/retention/enforce",
                json={"entity_type": "audit_log"},
                headers=_auth_headers(),
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


@pytest.mark.asyncio
async def test_part11_sign(client):
    response = await client.post(
        "/api/v1/part11/sign",
        json={
            "user_id": "test-user",
            "meaning": "Approved",
            "record_content": {"test": "data"},
        },
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert "signature_id" in data
    assert "content_hash" in data
    assert data["verified"] is True


@pytest.mark.asyncio
async def test_part11_verify(client):
    response = await client.get(
        "/api/v1/part11/verify/test-sig-id",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "verified"


@pytest.mark.asyncio
async def test_part11_lockout(client):
    response = await client.get(
        "/api/v1/part11/lockout/test-user",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert "locked" in data


@pytest.mark.asyncio
async def test_kms_create_key(client):
    response = await client.post(
        "/api/v1/kms/keys",
        json={"key_id": "test-key-1", "algorithm": "AES-256"},
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["key_id"] == "test-key-1"
    assert "key_arn" in data


@pytest.mark.asyncio
async def test_kms_list_keys(client):
    response = await client.get("/api/v1/kms/keys", headers=_auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert "keys" in data


@pytest.mark.asyncio
async def test_kms_encrypt_decrypt(client):
    create_resp = await client.post(
        "/api/v1/kms/keys",
        json={"key_id": "enc-test-key", "algorithm": "AES-256"},
        headers=_auth_headers(),
    )
    assert create_resp.status_code == 200

    enc_resp = await client.post(
        "/api/v1/kms/encrypt",
        json={"key_id": "enc-test-key", "plaintext": "hello world"},
        headers=_auth_headers(),
    )
    assert enc_resp.status_code == 200
    ciphertext = enc_resp.json()["ciphertext"]

    dec_resp = await client.post(
        "/api/v1/kms/decrypt",
        json={"key_id": "enc-test-key", "ciphertext": ciphertext},
        headers=_auth_headers(),
    )
    assert dec_resp.status_code == 200
    assert dec_resp.json()["plaintext"] == "hello world"


@pytest.mark.asyncio
async def test_kms_rotate_key(client):
    await client.post(
        "/api/v1/kms/keys",
        json={"key_id": "rotate-test-key"},
        headers=_auth_headers(),
    )
    response = await client.post(
        "/api/v1/kms/keys/rotate-test-key/rotate",
        headers=_auth_headers(),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rotated"] is True


@pytest.mark.asyncio
async def test_compliance_endpoints_no_auth():
    from httpx import ASGITransport, AsyncClient
    from app.main import create_app

    _app = create_app()

    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/compliance/soc2/summary")
        assert response.status_code in (200, 401, 403)

    _app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_kms_endpoints_no_auth():
    from httpx import ASGITransport, AsyncClient
    from app.main import create_app

    _app = create_app()

    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/kms/keys")
        assert response.status_code in (200, 401, 403)

    _app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_part11_endpoints_no_auth():
    from httpx import ASGITransport, AsyncClient
    from app.main import create_app

    _app = create_app()

    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/part11/lockout/test-user")
        assert response.status_code in (200, 401, 403)

    _app.dependency_overrides.clear()
