"""Tests for production intelligence analytics (Sprint S9)."""

import os
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev")
os.environ.setdefault("REDIS_URL", "redis://localhost:6380/0")
os.environ.setdefault("IPE_JWT_SIGNING_MODE", "hs256")
os.environ.setdefault("IPE_JWT_SECRET_KEY", "dev-jwt-secret-change-in-production-min-32-chars")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from ipe_shared.testing.conftest_helpers import make_auth_headers

TENANT_ID = str(uuid4())


@pytest.mark.asyncio
async def test_bottlenecks_endpoint(client):
    with patch(
        "app.api.v1.analytics._load_schedule_context",
        new=AsyncMock(return_value=([], [])),
    ):
        resp = await client.get(
            "/api/v1/analytics/bottlenecks",
            headers=make_auth_headers(tenant_id=TENANT_ID, role="planner"),
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "bottleneck_count" in data
    assert data["threshold_pct"] == 85.0


@pytest.mark.asyncio
async def test_utilisation_endpoint(client):
    mock_wc = [{"id": "wc-1", "name": "CNC-1", "capacity_hours_per_day": 8}]
    mock_assign = [{"work_center_id": "wc-1", "duration": 4800}]
    with patch(
        "app.api.v1.analytics._load_schedule_context",
        new=AsyncMock(return_value=(mock_assign, mock_wc)),
    ):
        resp = await client.get(
            "/api/v1/analytics/utilisation",
            headers=make_auth_headers(tenant_id=TENANT_ID, role="planner"),
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["horizon_days"] == 7
    assert len(data["work_centers"]) == 1


@pytest.mark.asyncio
async def test_changeover_endpoint(client):
    resp = await client.get(
        "/api/v1/analytics/changeover?lookback_days=30",
        headers=make_auth_headers(tenant_id=TENANT_ID, role="planner"),
    )
    assert resp.status_code == 200
    assert "work_centers" in resp.json()["data"]
