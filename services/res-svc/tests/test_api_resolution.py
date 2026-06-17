import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["service"] == "res-svc"


@pytest.mark.asyncio
async def test_scenarios_no_tenant(client):
    response = await client.post("/api/v1/resolution/scenarios", json={"mo_id": "00000000-0000-0000-0000-000000000001"})
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"
