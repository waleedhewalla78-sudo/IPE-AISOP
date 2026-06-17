from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx

TENANT_ID = str(uuid4())


class MockRow:
    def __init__(self, values):
        self._values = values

    def __getitem__(self, i):
        return self._values[i]

    def __iter__(self):
        return iter(self._values)


class MockResult:
    def __init__(self, rows, scalar_val=None):
        self._rows = rows
        self._scalar = scalar_val

    def one(self):
        return self._rows[0] if self._rows else [None]

    def scalar(self):
        return self._scalar

    def fetchall(self):
        return self._rows


MOCK_ROWS = list(
    [
        MockResult([MockRow([130, 150])]),
        MockResult([MockRow([200, 250])]),
        MockResult([MockRow([8.5])]),
        MockResult([MockRow([1250000.00])]),
        MockResult([MockRow([180, 200])]),
        MockResult(
            [
                MockRow(["2026-06-01", True, 88.2]),
                MockRow(["2026-06-01", False, 75.4]),
                MockRow(["2026-06-02", True, 91.0]),
            ]
        ),
    ]
)


def _build_app():
    from app.main import create_app

    app = create_app()
    app.dependency_overrides.clear()
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(side_effect=list(MOCK_ROWS))

    async def override_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    return app


@pytest.mark.asyncio
async def test_executive_summary_all_metrics_present():
    app = _build_app()
    token = tenant_ctx.set(TENANT_ID)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/executive-summary")
    tenant_ctx.reset(token)
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["ai_otd_pct"] == 86.7
    assert data["manual_otd_pct"] == 80.0
    assert data["avg_planning_cycle_days"] == 8.5
    assert data["inventory_value"] == 1250000.0
    assert data["delay_coverage_pct"] == 90.0
    assert len(data["otd_trend"]) == 3


@pytest.mark.asyncio
async def test_executive_summary_no_tenant():
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/executive-summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NO_TENANT"
