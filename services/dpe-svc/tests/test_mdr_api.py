"""MDR API endpoint tests — R2-05."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_mdr_dashboard_success(client, auth_headers):
    with patch(
        "app.api.v1.mdr.calculate_mdr",
        new=AsyncMock(return_value={"composite_score": 85, "passed": True}),
    ):
        response = await client.get("/api/v1/demand/mdr/dashboard", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_mdr_dashboard_no_tenant(client, auth_headers):
    with patch(
        "app.api.v1.mdr.calculate_mdr",
        new=AsyncMock(return_value={"error": "No tenant context", "passed": False}),
    ):
        response = await client.get("/api/v1/demand/mdr/dashboard", headers=auth_headers)
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_routing_deviations(client, auth_headers):
    with patch(
        "app.api.v1.mdr.detect_routing_deviation",
        new=AsyncMock(return_value=[{"routing_id": "r1", "deviation_pct": 20}]),
    ):
        response = await client.get("/api/v1/demand/mdr/routing-deviations", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["count"] == 1
