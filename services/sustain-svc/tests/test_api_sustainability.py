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
        role="planner",
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(uuid4())}


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "sustain-svc"


@pytest.mark.asyncio
async def test_circularity_score(client, auth_headers):
    response = await client.post(
        "/api/v1/sustainability/circularity-score",
        json={
            "product_id": "PROD-001",
            "bom_components": [
                {"material": "steel", "weight_kg": 5.0, "recyclable_pct": 92, "join_type": "bolt"},
                {"material": "plastic", "weight_kg": 2.0, "recyclable_pct": 30, "join_type": "snap_fit"},
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "circularity_score" in data["data"]
    assert data["data"]["circularity_score"] > 0


@pytest.mark.asyncio
async def test_eol_plan(client, auth_headers):
    response = await client.get(
        "/api/v1/sustainability/eol-plan?product_id=PROD-001&regulatory_region=EU",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "eol_risk_score" in data["data"]
    assert "phase_out_timeline" in data["data"]


@pytest.mark.asyncio
async def test_recyclability_score(client, auth_headers):
    response = await client.post(
        "/api/v1/sustainability/recyclability-score",
        json={
            "product_id": "PROD-001",
            "bom_components": [
                {"material": "steel", "weight_kg": 5.0, "hazardous": False, "disassembly_steps": 2},
                {"material": "copper", "weight_kg": 0.5, "hazardous": False, "disassembly_steps": 3},
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "score" in data["data"]
    assert data["data"]["grade"] in ("A", "B", "C", "D", "F")