"""Tests for supply chain intelligence (Sprint S10)."""

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
async def test_supplier_risk_endpoint(client):
    mock_rows = [
        {
            "supplier_id": str(uuid4()),
            "name": "Supplier A",
            "reliability_score": 0.55,
            "avg_delay_days": 6.0,
            "risk_tier": "high",
            "sample_size": 10,
            "category": "raw",
            "contributing_factors": {},
        }
    ]
    with patch(
        "app.api.v1.supply_chain.compute_supplier_risk",
        new=AsyncMock(return_value=mock_rows),
    ):
        resp = await client.get(
            "/api/v1/supply-chain/supplier-risk",
            headers=make_auth_headers(tenant_id=TENANT_ID, role="planner"),
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["high_risk_count"] == 1


@pytest.mark.asyncio
async def test_inventory_abc_endpoint(client):
    with patch(
        "app.api.v1.supply_chain.compute_inventory_abc",
        new=AsyncMock(return_value={"items": [], "class_a_count": 0, "class_b_count": 0, "class_c_count": 0}),
    ):
        resp = await client.get(
            "/api/v1/supply-chain/inventory-abc",
            headers=make_auth_headers(tenant_id=TENANT_ID, role="planner"),
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_reorder_suggestions_endpoint(client):
    with patch(
        "app.api.v1.supply_chain.compute_reorder_suggestions",
        new=AsyncMock(return_value=[]),
    ):
        resp = await client.get(
            "/api/v1/supply-chain/reorder-suggestions",
            headers=make_auth_headers(tenant_id=TENANT_ID, role="planner"),
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["count"] == 0
