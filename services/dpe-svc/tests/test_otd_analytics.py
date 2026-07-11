"""OTD analytics tests — Sprint 4 Wave 1 (W1-06/07)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.otd_aggregator import OTDAggregator
from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.testing.conftest_helpers import apply_auth_and_session_overrides

TENANT = str(uuid4())


def _build_app(mock_session: AsyncMock | None = None):
    from app.main import create_app

    app = create_app()
    apply_auth_and_session_overrides(app)
    session = mock_session or AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock(
        return_value=SimpleNamespace(
            one=lambda: SimpleNamespace(on_time=7, total=10, avg_delay=2.0, max_delay=5.0),
            scalar=lambda: 0,
            fetchall=lambda: [],
            scalars=lambda: SimpleNamespace(all=lambda: []),
            scalar_one_or_none=lambda: None,
        )
    )
    session.commit = AsyncMock()
    session.add = AsyncMock()

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    return app, session


@pytest.mark.asyncio
async def test_otd_70_percent_from_known_mos():
    """10 MOs: 7 on-time, 3 late → OTD = 70%."""
    agg = OTDAggregator()
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock(
        return_value=SimpleNamespace(
            one=lambda: SimpleNamespace(total=10, on_time=7, avg_delay=2.5, max_delay=4.0),
            scalar_one_or_none=lambda: None,
        )
    )
    session.commit = AsyncMock()

    with patch(
        "app.core.otd_aggregator.upsert_daily_snapshot",
        AsyncMock(return_value=SimpleNamespace(metadata_json={}, otd_pct=None, completed_mos=0, on_time_mos=0, avg_delay_days=None, chaos_cost_usd=0)),
    ):
        result = await agg.capture_daily_snapshot(session, uuid4())

    assert result["total"] == 10
    assert result["on_time"] == 7
    assert result["late"] == 3
    assert result["otd_pct"] == 70.0


@pytest.mark.asyncio
async def test_trend_chronological_api():
    app, _ = _build_app()
    points = [
        {"period_start": "2026-07-01", "otd_pct": 70.0, "completed_mos": 10, "on_time_mos": 7},
        {"period_start": "2026-07-02", "otd_pct": 80.0, "completed_mos": 5, "on_time_mos": 4},
    ]
    with patch("app.api.v1.otd_analytics.compute_otd_trend", AsyncMock(return_value=points)), patch(
        "app.api.v1.otd_analytics.compute_baseline_comparison",
        AsyncMock(return_value={"baseline": {"otd_pct": 60.0}, "improvement_pct": 10.0}),
    ):
        token = tenant_ctx.set(TENANT)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/analytics/otd/trend?period=daily&range=90")
        tenant_ctx.reset(token)

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["data"][0]["date"] == "2026-07-01"
    assert data["data"][1]["otd_pct"] == 80.0
    assert data["baseline_otd_pct"] == 60.0


@pytest.mark.asyncio
async def test_root_causes_grouped():
    app, _ = _build_app()
    with patch(
        "app.api.v1.otd_analytics.otd_aggregator.get_root_causes",
        AsyncMock(
            return_value=[
                {"category": "material_shortage", "count": 8, "pct": 34.8, "avg_delay_days": 3.2, "total_cost": 1000},
                {"category": "capacity_overload", "count": 6, "pct": 26.1, "avg_delay_days": 2.1, "total_cost": 800},
            ]
        ),
    ):
        token = tenant_ctx.set(TENANT)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/analytics/otd/root-causes?range=30")
        tenant_ctx.reset(token)

    body = resp.json()["data"]
    assert body["total_late"] == 14
    assert body["causes"][0]["category"] == "material_shortage"


@pytest.mark.asyncio
async def test_summary_endpoint():
    app, _ = _build_app()
    with patch(
        "app.api.v1.otd_analytics.otd_aggregator.get_summary",
        AsyncMock(
            return_value={
                "current_period_otd": 87.5,
                "prior_period_otd": 82.1,
                "trend_direction": "improving",
                "improvement_vs_baseline": 15.2,
                "total_late_this_month": 8,
                "worst_delay_days": 7,
                "total_cost_this_month": 23400,
            }
        ),
    ):
        token = tenant_ctx.set(TENANT)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/analytics/otd/summary")
        tenant_ctx.reset(token)

    assert resp.json()["data"]["current_period_otd"] == 87.5
    assert resp.json()["data"]["trend_direction"] == "improving"


@pytest.mark.asyncio
async def test_backfill_creates_snapshots():
    agg = OTDAggregator()
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock(
        return_value=SimpleNamespace(
            one=lambda: SimpleNamespace(total=4, on_time=3),
            scalar_one_or_none=lambda: None,
        )
    )
    session.commit = AsyncMock()
    session.add = AsyncMock()

    result = await agg.capture_historical(session, uuid4(), months_back=1)
    assert result["snapshots_created"] >= 4  # ~4 weeks in a month
    assert session.add.await_count == result["snapshots_created"] or session.add.call_count == result["snapshots_created"]


@pytest.mark.asyncio
async def test_snapshot_endpoint():
    app, _ = _build_app()
    with patch(
        "app.api.v1.otd_analytics.otd_aggregator.capture_daily_snapshot",
        AsyncMock(
            return_value={
                "snapshot_date": "2026-07-11",
                "otd_pct": 70.0,
                "total": 10,
                "on_time": 7,
                "late": 3,
            }
        ),
    ):
        token = tenant_ctx.set(TENANT)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/analytics/otd/snapshot", json={})
        tenant_ctx.reset(token)

    assert resp.json()["data"]["otd_pct"] == 70.0
    assert resp.json()["data"]["late"] == 3
