import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["service"] == "procurement-svc"


@pytest.mark.asyncio
async def test_list_suppliers(client, auth_headers):
    r = await client.get("/api/v1/suppliers", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["success"] is True


@pytest.mark.asyncio
async def test_procurement_spend(client, auth_headers):
    r = await client.get("/api/v1/procurement/spend", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["summary"]["total"] > 0


@pytest.mark.asyncio
async def test_compliance_check(client, auth_headers):
    r = await client.post(
        "/api/v1/procurement/compliance/check",
        json={},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True or body["error"]["code"] == "NOT_FOUND"
