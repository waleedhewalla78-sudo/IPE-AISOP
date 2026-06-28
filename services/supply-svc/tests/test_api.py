import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["service"] == "supply-svc"


@pytest.mark.asyncio
async def test_network_empty(client, auth_headers):
    r = await client.get("/api/v1/supply/network", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert "facilities" in body["data"]


@pytest.mark.asyncio
async def test_inventory(client, auth_headers):
    r = await client.get("/api/v1/supply/inventory", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["success"] is True


@pytest.mark.asyncio
async def test_generate_plan(client, auth_headers):
    r = await client.post(
        "/api/v1/supply/plan/generate",
        json={"name": "QA plan", "horizon_days": 14},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["success"] is True
