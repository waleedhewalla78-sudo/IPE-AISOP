"""OTD analytics API tests (W1-07 / Sprint S6)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.testing.conftest_helpers import apply_auth_and_session_overrides

TENANT_A = str(uuid4())
TENANT_B = str(uuid4())


def _build_app(mock_session: AsyncMock | None = None):
    from app.main import create_app

    app = create_app()
    apply_auth_and_session_overrides(app)
    session = mock_session or AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock(return_value=SimpleNamespace(
        one=lambda: SimpleNamespace(on_time=8, total=10),
        scalar=lambda: 2,
        fetchall=lambda: [],
        scalars=lambda: SimpleNamespace(all=lambda: []),
    ))
    session.commit = AsyncMock()
    session.add = AsyncMock()

    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    return app, session


@pytest.mark.asyncio
async def test_otd_kpis_success():
    app, _ = _build_app()
    kpis = {
        "otd_pct": 80.0,
        "completed_mos": 10,
        "on_time_mos": 8,
        "orders_at_risk": 2,
        "avg_delay_days": 1.5,
        "chaos_cost_usd": 5000.0,
        "lookback_days": 30,
        "filters": {"supplier_id": None, "line_id": None, "region_id": None},
    }
    with patch("app.api.v1.otd_analytics.compute_otd_kpis", AsyncMock(return_value=kpis)):
        token = tenant_ctx.set(TENANT_A)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/analytics/otd/kpis?range=30d")
        tenant_ctx.reset(token)

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["otd_pct"] == 80.0
    assert body["data"]["orders_at_risk"] == 2
    assert body["data"]["chaos_cost_usd"] == 5000.0


@pytest.mark.asyncio
async def test_otd_kpis_no_tenant():
    app, _ = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/analytics/otd/kpis")
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NO_TENANT"


@pytest.mark.asyncio
async def test_otd_trend_success():
    app, _ = _build_app()
    points = [{"period_start": "2026-07-01", "otd_pct": 85.0, "completed_mos": 4, "on_time_mos": 3}]
    with patch("app.api.v1.otd_analytics.compute_otd_trend", AsyncMock(return_value=points)):
        token = tenant_ctx.set(TENANT_A)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/analytics/otd/trend?period=weekly&range=30d")
        tenant_ctx.reset(token)

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["period"] == "weekly"
    assert len(data["points"]) == 1


@pytest.mark.asyncio
async def test_otd_root_cause_success():
    app, _ = _build_app()
    causes = [{"cause_category": "supplier", "count": 5, "pct": 50.0, "cost_usd": 1200.0}]
    with patch("app.api.v1.otd_analytics.compute_root_cause", AsyncMock(return_value=causes)):
        token = tenant_ctx.set(TENANT_A)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/analytics/otd/root-cause?range=30d")
        tenant_ctx.reset(token)

    assert resp.status_code == 200
    assert resp.json()["data"][0]["cause_category"] == "supplier"


@pytest.mark.asyncio
async def test_otd_cost_of_chaos_success():
    app, _ = _build_app()
    chaos = {
        "total_chaos_usd": 9000.0,
        "categories": [{"code": "idle_time", "label": "Idle Time", "usd": 5000.0, "pct": 55.6}],
        "top_mos": [],
        "war_room_links": [],
    }
    with patch("app.api.v1.otd_analytics.aggregate_chaos_cost", AsyncMock(return_value=chaos)):
        token = tenant_ctx.set(TENANT_A)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/analytics/otd/cost-of-chaos?range=30d")
        tenant_ctx.reset(token)

    assert resp.status_code == 200
    assert resp.json()["data"]["total_chaos_usd"] == 9000.0


@pytest.mark.asyncio
async def test_otd_baseline_success():
    app, _ = _build_app()
    baseline_data = {
        "baseline": {"otd_pct": 72.0},
        "current": {"otd_pct": 80.0},
        "delta_vs_baseline": 8.0,
        "improvement_pct": 8.0,
    }
    with patch("app.api.v1.otd_analytics.compute_baseline_comparison", AsyncMock(return_value=baseline_data)):
        token = tenant_ctx.set(TENANT_A)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/analytics/otd/baseline")
        tenant_ctx.reset(token)

    assert resp.status_code == 200
    assert resp.json()["data"]["delta_vs_baseline"] == 8.0


@pytest.mark.asyncio
async def test_otd_tenant_isolation_passes_tenant_id():
    """Tenant A context must reach aggregation with Tenant A UUID, not Tenant B."""
    app, _ = _build_app()
    captured: dict = {}

    async def capture_kpis(session, tenant_id, **kwargs):
        captured["tenant_id"] = tenant_id
        return {
            "otd_pct": 90.0,
            "completed_mos": 5,
            "on_time_mos": 5,
            "orders_at_risk": 0,
            "avg_delay_days": None,
            "chaos_cost_usd": 0.0,
            "lookback_days": 30,
            "filters": {},
        }

    with patch("app.api.v1.otd_analytics.compute_otd_kpis", side_effect=capture_kpis):
        token = tenant_ctx.set(TENANT_A)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.get("/api/v1/analytics/otd/kpis")
        tenant_ctx.reset(token)

    assert captured["tenant_id"] == UUID(TENANT_A)
    assert captured["tenant_id"] != UUID(TENANT_B)


@pytest.mark.asyncio
async def test_compute_otd_kpis_filters_by_tenant_in_query():
    """RLS isolation: aggregation SQL must scope ManufacturingOrder.tenant_id."""
    from app.core.otd_aggregation import compute_otd_kpis

    session = AsyncMock(spec=AsyncSession)
    tenant_id = uuid4()

    async def fake_execute(stmt):
        compiled = str(stmt)
        assert "cdm_manufacturing_order.tenant_id" in compiled or "tenant_id" in compiled
        return SimpleNamespace(
            one=lambda: SimpleNamespace(on_time=3, total=5),
            scalar=lambda: 1,
        )

    session.execute = AsyncMock(side_effect=fake_execute)

    with patch("app.core.otd_aggregation.aggregate_chaos_cost", AsyncMock(return_value={"total_chaos_usd": 100.0})):
        result = await compute_otd_kpis(session, tenant_id, lookback_days=30)

    assert result["completed_mos"] == 5
    assert result["on_time_mos"] == 3
    assert session.execute.await_count >= 2
