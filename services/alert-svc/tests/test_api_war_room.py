"""War room API tests (P8 alert-svc — AG-02)."""

import pytest


@pytest.mark.asyncio
async def test_war_room_aggregate_no_tenant(client):
    response = await client.get("/api/v1/war-room/aggregate")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_war_room_recovery_plan_no_tenant(client):
    response = await client.get("/api/v1/war-room/recovery-plan")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NO_TENANT"
