"""API tests for CPM cascade endpoints."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

TEST_TENANT = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"


@pytest.mark.asyncio
async def test_cpm_cascade_no_tenant(client):
    response = await client.post(
        "/api/v1/capacity/cpm/cascade",
        json={
            "mo_id": str(uuid4()),
            "operation_id": str(uuid4()),
            "delta_minutes": 60,
        },
    )
    assert response.status_code == 200
    assert response.json()["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_cpm_cascade_returns_financial_delta(client, auth_headers):
    mo_id = uuid4()
    op_id = uuid4()
    base = datetime(2026, 7, 1, 8, 0, tzinfo=UTC)
    operations = [
        {
            "operation_id": str(op_id),
            "mo_id": str(mo_id),
            "sequence": 10,
            "work_center_id": "wc1",
            "planned_start": base.isoformat(),
            "planned_end": (base + timedelta(minutes=60)).isoformat(),
            "duration_minutes": 60,
        }
    ]
    work_centers = [{"id": "wc1", "cost_per_hour": 60.0, "overtime_cost_multiplier": 1.5}]

    with patch(
        "app.api.v1.capacity._load_cpm_operations",
        new=AsyncMock(return_value=(operations, work_centers)),
    ):
        response = await client.post(
            "/api/v1/capacity/cpm/cascade",
            headers={**auth_headers, "X-Tenant-ID": TEST_TENANT},
            json={
                "mo_id": str(mo_id),
                "operation_id": str(op_id),
                "delta_minutes": 120,
                "mode": "preview",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "financial_delta" in body["data"]
    assert "activity_cost_delta_usd" in body["data"]["financial_delta"]
    assert body["data"]["cascade_ms"] >= 0


@pytest.mark.asyncio
async def test_cpm_apply_sets_ai_suggested(client, auth_headers):
    mo_id = uuid4()
    op_id = uuid4()
    base = datetime(2026, 7, 1, 8, 0, tzinfo=UTC)

    mo = AsyncMock()
    mo.id = mo_id
    mo.ai_suggested_start = None
    mo.ai_suggested_end = None

    wo = AsyncMock()
    wo.id = op_id
    wo.planned_start = None
    wo.planned_end = None

    mo_result = MagicMock()
    mo_result.scalar_one_or_none.return_value = mo
    wo_result = MagicMock()
    wo_result.scalar_one_or_none.return_value = wo

    session = AsyncMock()
    session.execute = AsyncMock(side_effect=[mo_result, wo_result])
    session.commit = AsyncMock()

    from app.main import create_app
    from ipe_shared.testing.conftest_helpers import apply_auth_and_session_overrides

    app = create_app()
    apply_auth_and_session_overrides(app)

    async def override_session():
        yield session

    from ipe_shared.database.session import get_session
    app.dependency_overrides[get_session] = override_session

    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/capacity/cpm/apply",
            headers={**auth_headers, "X-Tenant-ID": TEST_TENANT},
            json={
                "mo_id": str(mo_id),
                "operations": [
                    {
                        "operation_id": str(op_id),
                        "planned_start": base.isoformat(),
                        "planned_end": (base + timedelta(minutes=60)).isoformat(),
                    }
                ],
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["updated_work_orders"] == 1
    assert mo.ai_suggested_start is not None
