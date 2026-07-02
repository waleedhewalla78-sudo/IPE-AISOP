from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["service"] == "equipment-svc"


@pytest.mark.asyncio
async def test_list_equipment(client, auth_headers):
    r = await client.get("/api/v1/equipment", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert "equipment" in r.json()["data"]


@pytest.mark.asyncio
async def test_equipment_health_not_found(client, auth_headers):
    eid = uuid4()
    r = await client.get(f"/api/v1/equipment/{eid}/health", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is False or "health_score" in (body.get("data") or {})
