"""Demand API edge tests (P8 dpe-svc — AG-02)."""

import pytest


@pytest.mark.asyncio
async def test_classify_demand_no_tenant(client):
    response = await client.post("/api/v1/demand/classify", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_margin_aware_priority_no_tenant(client):
    response = await client.get("/api/v1/demand/priority/margin-aware")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NO_TENANT"
