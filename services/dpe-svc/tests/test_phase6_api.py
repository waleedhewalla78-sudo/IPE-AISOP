"""Phase 6 Enterprise API smoke tests (ASGI in-process)."""

from uuid import UUID

import pytest

from ipe_shared.auth.jwt import create_access_token

TENANT = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


@pytest.fixture
def auth_headers():
    token = create_access_token(user_id=UUID(TENANT), tenant_id=UUID(TENANT), role="planner")
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": TENANT}


@pytest.mark.asyncio
async def test_enterprise_agents_roster(client, auth_headers):
    resp = await client.get("/api/v1/enterprise/agents", headers=auth_headers)
    assert resp.status_code == 200
    agents = resp.json()["data"]["agents"]
    ids = {a["agent_id"] for a in agents}
    assert {"A13", "A14", "A15", "A16", "A17"} <= ids


@pytest.mark.asyncio
async def test_integrations_status_flags_mock(client, auth_headers):
    resp = await client.get("/api/v1/enterprise/integrations/status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["odoo_accounting"]["live"] is False
    assert data["iot_shop_floor"]["live"] is False


@pytest.mark.asyncio
async def test_commercial_pricing_endpoint(client, auth_headers):
    resp = await client.post(
        "/api/v1/enterprise/commercial/pricing",
        json={"customer_tier": "A", "list_price": 85000, "unit_cost": 59200, "quantity": 10},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["agent_id"] == "A13"
    assert data["recommended_price"] > 0


@pytest.mark.asyncio
async def test_analytics_insights_endpoint(client, auth_headers):
    resp = await client.post(
        "/api/v1/enterprise/analytics/insights", json={}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["agent_id"] == "A14"
    assert data["generated"] >= 1


@pytest.mark.asyncio
async def test_orchestrator_atp_endpoint(client, auth_headers):
    resp = await client.post(
        "/api/v1/enterprise/orchestrator/atp",
        json={"qty": 50, "inventory_available": 12, "capacity_available_hrs": 200},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["coordinated_agents"] == ["A1", "A3", "A11", "A13", "A17"]
    assert data["decision"] in ("accept", "negotiate", "reject")


@pytest.mark.asyncio
async def test_three_way_match_endpoint(client, auth_headers):
    resp = await client.post(
        "/api/v1/enterprise/procurement/three-way-match", json={}, headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["agent_id"] == "A15"
    assert "routing" in data
