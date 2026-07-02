import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def auth_headers():
    from ipe_shared.auth.jwt import create_access_token
    from uuid import uuid4
    token = create_access_token(
        user_id=uuid4(),
        tenant_id=uuid4(),
        role="quality",
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(uuid4())}


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "quality-svc"


@pytest.mark.asyncio
async def test_spc_xbar(client, auth_headers):
    response = await client.post(
        "/api/v1/quality-events/spc/xbar",
        json={
            "measurements": [
                [10.1, 10.2, 10.0],
                [10.3, 10.1, 9.9],
                [10.0, 10.0, 10.1],
                [10.2, 10.1, 10.0],
                [15.0, 10.0, 10.1],
            ],
            "sigma_multiplier": 3.0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "ucl" in data["data"]
    assert "lcl" in data["data"]
    assert "points_out_of_control" in data["data"]


@pytest.mark.asyncio
async def test_defect_predict(client, auth_headers):
    response = await client.post(
        "/api/v1/quality-events/predict",
        json={
            "mo_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
            "work_center_id": "wc-weld-01",
            "shift": "night",
            "days_since_maintenance": 45,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "defect_probability" in data["data"]
    assert data["data"]["risk_level"] in ("low", "medium", "high")