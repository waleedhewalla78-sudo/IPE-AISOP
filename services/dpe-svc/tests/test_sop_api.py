import pytest
from uuid import UUID

from ipe_shared.auth.jwt import create_access_token


@pytest.fixture
def auth_headers():
    token = create_access_token(
        user_id=UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
        tenant_id=UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
        role="admin",
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    }


class TestSopForecastIngest:
    @pytest.mark.asyncio
    async def test_ingest_forecast(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/sop/forecast",
            json={
                "product_family": "Electronics",
                "period_type": "weekly",
                "period_start": "2026-01-06",
                "period_end": "2026-01-13",
                "forecast_qty": 500,
                "capacity_qty": 400,
                "confidence_pct": 0.85,
                "source": "pipeline",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["product_family"] == "Electronics"
        assert data["forecast_qty"] == 500
        assert data["status"] == "ingested"

    @pytest.mark.asyncio
    async def test_ingest_no_tenant(self, client):
        token = create_access_token(
            user_id=UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
            tenant_id=UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
            role="admin",
        )
        resp = await client.post(
            "/api/v1/sop/forecast",
            json={
                "product_family": "Electronics",
                "period_start": "2026-01-06",
                "period_end": "2026-01-13",
                "forecast_qty": 500,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        result = resp.json()
        assert resp.status_code == 200
        assert result["success"] is True
        assert result["data"]["product_family"] == "Electronics"


class TestSopSolve:
    @pytest.mark.asyncio
    async def test_solve_sop_balanced(self, client, auth_headers):
        demand = []
        capacity = []
        base_d = "2026-01-06"
        base_c = "2026-01-06"
        for i in range(4):
            wd = 6 + i * 7
            demand.append({
                "period_start": f"2026-01-{wd:02d}",
                "period_end": f"2026-01-{wd + 7:02d}",
                "product_family": "A",
                "forecast_qty": 100,
                "confidence_pct": 0.8,
            })
            capacity.append({
                "period_start": f"2026-01-{wd:02d}",
                "period_end": f"2026-01-{wd + 7:02d}",
                "work_center_group": "WC-A",
                "capacity_hours": 100,
                "capacity_qty": 100,
            })

        resp = await client.post(
            "/api/v1/sop/solve",
            json={"demand": demand, "capacity": capacity, "bottleneck_threshold_pct": 10.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_demand"] == 400.0
        assert data["solve_time_ms"] < 10000

    @pytest.mark.asyncio
    async def test_solve_sop_bottleneck(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/sop/solve",
            json={
                "demand": [
                    {"period_start": "2026-01-06", "period_end": "2026-01-13",
                     "product_family": "A", "forecast_qty": 200, "confidence_pct": 0.9}
                ],
                "capacity": [
                    {"period_start": "2026-01-06", "period_end": "2026-01-13",
                     "work_center_group": "WC-A", "capacity_hours": 100, "capacity_qty": 100}
                ],
                "bottleneck_threshold_pct": 10.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["bottleneck_count"] >= 1


class TestCostAccountingAPI:
    @pytest.mark.asyncio
    async def test_cogm(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/cost-accounting/cogm",
            json={
                "material_cost": 1000,
                "labor_cost": 500,
                "energy_cost": 200,
                "overhead_cost": 300,
                "quantity": 100,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_cogm"] == 2000.0
        assert data["cogm_per_unit"] == 20.0
        assert "5100-RAW-MATERIAL" in data["gl_accounts"]

    @pytest.mark.asyncio
    async def test_copq(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/cost-accounting/copq",
            json={
                "total_quantity": 1000,
                "defect_rate_pct": 5.0,
                "rework_rate_pct": 2.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_copq"] > 0

    @pytest.mark.asyncio
    async def test_full_cost_accounting(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/cost-accounting/full",
            json={
                "product_id": "PROD-001",
                "quantity": 100,
                "selling_price": 100.0,
                "material_cost": 3000.0,
                "labor_cost": 1000.0,
                "energy_cost": 500.0,
                "overhead_cost": 500.0,
                "actual_costs": {"material": 3300.0, "labor": 1100.0},
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["cogm"]["total_cogm"] == 5000.0
        assert data["revenue"] == 10000.0
        assert len(data["variances"]) >= 2