import pytest
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.core.rfq_workflow import _rfq_store, _rfq_response_store


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
    token = create_access_token(
        user_id=uuid4(),
        tenant_id=uuid4(),
        role="planner",
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(uuid4())}


@pytest.fixture(autouse=True)
def clear_rfq_stores():
    _rfq_store.clear()
    _rfq_response_store.clear()
    yield
    _rfq_store.clear()
    _rfq_response_store.clear()


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "scn-svc"


@pytest.mark.asyncio
async def test_supplier_score_post(client, auth_headers):
    response = await client.post(
        "/api/v1/scn/supplier/score",
        json={"supplier_id": "supp-1", "historical_data": {"otif": {"score": 90.0}}},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "composite_score" in data["data"]
    assert "risk_tier" in data["data"]
    assert "xai_explanation" in data["data"]


@pytest.mark.asyncio
async def test_supplier_score_get(client, auth_headers):
    response = await client.get(
        "/api/v1/scn/supplier/supp-1/score",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["supplier_id"] == "supp-1"


@pytest.mark.asyncio
async def test_rfq_lifecycle(client, auth_headers):
    create_resp = await client.post(
        "/api/v1/scn/rfq",
        json={"title": "Test RFQ", "description": "Test"},
        headers=auth_headers,
    )
    assert create_resp.status_code == 200
    rfq_id = create_resp.json()["data"]["rfq_id"]

    publish_resp = await client.post(
        f"/api/v1/scn/rfq/{rfq_id}/publish",
        headers=auth_headers,
    )
    assert publish_resp.status_code == 200
    assert publish_resp.json()["data"]["state"] == "published"

    respond_resp = await client.post(
        f"/api/v1/scn/rfq/{rfq_id}/respond",
        json={"rfq_id": rfq_id, "supplier_id": "supp-1", "price": 100.0, "lead_time_days": 14},
        headers=auth_headers,
    )
    assert respond_resp.status_code == 200
    assert respond_resp.json()["data"]["supplier_id"] == "supp-1"

    evaluate_resp = await client.post(
        f"/api/v1/scn/rfq/{rfq_id}/evaluate",
        headers=auth_headers,
    )
    assert evaluate_resp.status_code == 200
    assert evaluate_resp.json()["data"]["state"] == "under_review"

    award_resp = await client.post(
        f"/api/v1/scn/rfq/{rfq_id}/award",
        json={"rfq_id": rfq_id, "winning_supplier_id": "supp-1"},
        headers=auth_headers,
    )
    assert award_resp.status_code == 200
    assert award_resp.json()["data"]["state"] == "awarded"


@pytest.mark.asyncio
async def test_visibility_endpoint(client, auth_headers):
    response = await client.post(
        "/api/v1/scn/visibility",
        json={
            "suppliers": [
                {"id": "oem-1", "name": "OEM", "tier": 0, "type": "oem", "dependencies": [
                    {"supplier_id": "supp-1", "name": "Tier 1", "tier": 1, "lead_time_days": 7, "risk_score": 0.4},
                ]},
            ],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "graph" in data["data"]
    assert data["data"]["graph"]["node_count"] >= 1


@pytest.mark.asyncio
async def test_visibility_with_risk_propagation(client, auth_headers):
    response = await client.post(
        "/api/v1/scn/visibility",
        json={
            "suppliers": [
                {"id": "s1", "name": "S1", "tier": 1, "type": "supplier", "dependencies": [
                    {"supplier_id": "s2", "name": "S2", "tier": 2, "lead_time_days": 7, "risk_score": 0.6},
                ]},
            ],
            "at_risk_supplier_id": "s2",
            "impact_probability": 0.8,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["risk_propagation"] is not None
    assert len(data["data"]["risk_propagation"]) >= 1