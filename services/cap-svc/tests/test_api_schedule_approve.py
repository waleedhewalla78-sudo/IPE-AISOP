"""API tests for schedule persistence and approve endpoints."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

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


@pytest.mark.asyncio
async def test_approve_returns_409_on_version_conflict(client, auth_headers):
    """BUG-03: stale schedule version surfaces as HTTP 409 at the API layer."""
    mo_id = uuid4()
    conflict_result = {
        "activated": [],
        "failed": [{"mo_id": str(mo_id), "reason": "VERSION_CONFLICT"}],
        "total": 1,
        "activated_count": 0,
        "failed_count": 1,
    }

    with patch(
        "app.api.v1.capacity.approve_schedule_mos",
        AsyncMock(return_value=conflict_result),
    ):
        response = await client.post(
            "/api/v1/capacity/schedule/approve",
            headers=auth_headers,
            json={"mo_ids": [str(mo_id)]},
        )

    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "VERSION_CONFLICT"
    assert body["data"]["failed_count"] == 1
