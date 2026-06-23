"""API tests for schedule persistence and approve endpoints."""

import pytest


@pytest.mark.asyncio
async def test_validate_endpoint(client, auth_headers):
    response = await client.post(
        "/api/v1/capacity/validate",
        headers=auth_headers,
        json={},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "validations" in body["data"]


@pytest.mark.asyncio
async def test_active_schedule_endpoint(client, auth_headers):
    response = await client.get(
        "/api/v1/capacity/schedule/active",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "rows" in body["data"]


@pytest.mark.asyncio
async def test_approve_empty_mos(client, auth_headers):
    response = await client.post(
        "/api/v1/capacity/schedule/approve",
        headers=auth_headers,
        json={"mo_ids": []},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["activated_count"] == 0
