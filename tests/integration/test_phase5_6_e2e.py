"""E2E integration test for Phase 5-6 endpoints.

Tests S&OP, Cost Accounting, Digital Twin, and new service endpoints
against the live Docker stack.

Usage:
  IPE_JWT_SECRET_KEY="dev-only-change-in-production-min-32-chars-long!!" \
  uv run pytest tests/integration/test_phase5_6_e2e.py -v --asyncio-mode=auto
"""

import os
import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest

DPE_URL = os.environ.get("TEST_DPE_URL", "http://localhost:8020")
SUSTAIN_URL = os.environ.get("TEST_SUSTAIN_URL", "http://localhost:8012")
QUALITY_URL = os.environ.get("TEST_QUALITY_URL", "http://localhost:8013")
SCN_URL = os.environ.get("TEST_SCN_URL", "http://localhost:8014")
NETWORK_URL = os.environ.get("TEST_NETWORK_URL", "http://localhost:8015")

TENANT_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
JWT_SECRET = os.environ.get("IPE_JWT_SECRET_KEY", "dev-only-change-in-production-min-32-chars-long!!")

pytestmark = [pytest.mark.integration]


def _make_token():
    from ipe_shared.auth.jwt import create_access_token
    return create_access_token(
        user_id=uuid.UUID(TENANT_ID),
        tenant_id=uuid.UUID(TENANT_ID),
        role="admin",
    )


@pytest.fixture(scope="module")
def auth_headers():
    token = _make_token()
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": TENANT_ID,
        "Content-Type": "application/json",
    }


@pytest.fixture
async def client():
    async with httpx.AsyncClient(timeout=15) as c:
        yield c


class TestHealthAll:
    @pytest.mark.asyncio
    async def test_dpe_health(self, client):
        r = await client.get(f"{DPE_URL}/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "dpe-svc"

    @pytest.mark.asyncio
    async def test_sustain_health(self, client):
        r = await client.get(f"{SUSTAIN_URL}/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_quality_health(self, client):
        r = await client.get(f"{QUALITY_URL}/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_scn_health(self, client):
        r = await client.get(f"{SCN_URL}/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_network_health(self, client):
        r = await client.get(f"{NETWORK_URL}/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "network-svc"


class TestSopEndpoints:
    @pytest.mark.asyncio
    async def test_sop_forecast_ingest(self, client, auth_headers):
        r = await client.post(
            f"{DPE_URL}/api/v1/sop/forecast",
            json={
                "product_family": "Electronics",
                "period_type": "weekly",
                "period_start": "2026-01-06",
                "period_end": "2026-01-13",
                "forecast_qty": 500,
                "capacity_qty": 450,
                "confidence_pct": 0.85,
                "source": "pipeline",
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["product_family"] == "Electronics"
        assert data["forecast_qty"] == 500
        assert data["status"] == "ingested"

    @pytest.mark.asyncio
    async def test_sop_solve(self, client, auth_headers):
        demand = [
            {"period_start": "2026-01-06", "period_end": "2026-01-13",
             "product_family": "A", "forecast_qty": 200, "confidence_pct": 0.9},
        ]
        capacity = [
            {"period_start": "2026-01-06", "period_end": "2026-01-13",
             "work_center_group": "WC-A", "capacity_hours": 160, "capacity_qty": 150},
        ]
        r = await client.post(
            f"{DPE_URL}/api/v1/sop/solve",
            json={"demand": demand, "capacity": capacity, "bottleneck_threshold_pct": 10.0},
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["total_demand"] == 200.0
        assert data["total_capacity"] == 150.0
        assert data["bottleneck_count"] >= 1
        assert data["solve_time_ms"] < 10000


class TestCostAccountingEndpoints:
    @pytest.mark.asyncio
    async def test_cogm(self, client, auth_headers):
        r = await client.post(
            f"{DPE_URL}/api/v1/cost-accounting/cogm",
            json={
                "material_cost": 5000,
                "labor_cost": 2000,
                "energy_cost": 1000,
                "overhead_cost": 500,
                "quantity": 100,
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["total_cogm"] == 8500.0
        assert data["cogm_per_unit"] == 85.0
        assert "5100-RAW-MATERIAL" in data["gl_accounts"]

    @pytest.mark.asyncio
    async def test_copq(self, client, auth_headers):
        r = await client.post(
            f"{DPE_URL}/api/v1/cost-accounting/copq",
            json={"total_quantity": 1000, "defect_rate_pct": 5.0, "rework_rate_pct": 2.0},
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["total_copq"] > 0
        assert data["copq_as_pct_of_revenue"] > 0

    @pytest.mark.asyncio
    async def test_full_cost_accounting(self, client, auth_headers):
        r = await client.post(
            f"{DPE_URL}/api/v1/cost-accounting/full",
            json={
                "product_id": "PROD-E2E",
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
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["cogm"]["total_cogm"] == 5000.0
        assert data["revenue"] == 10000.0
        assert data["gross_margin"] == 5000.0
        assert len(data["variances"]) >= 2
        assert "xai_explanation" in data


class TestSustainabilityEndpoints:
    @pytest.mark.asyncio
    async def test_circularity_score(self, client, auth_headers):
        r = await client.post(
            f"{SUSTAIN_URL}/api/v1/sustainability/circularity-score",
            json={"product_id": "PROD-E2E"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["product_id"] == "PROD-E2E"
        assert "circularity_score" in data
        assert "xai_explanation" in data


class TestQualityEndpoints:
    @pytest.mark.asyncio
    async def test_spc_xbar(self, client, auth_headers):
        r = await client.post(
            f"{QUALITY_URL}/api/v1/quality/spc/xbar",
            json={"measurements": [[10.1, 10.0, 9.9], [10.2, 10.1, 10.0]]},
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["chart_type"] == "xbar"
        assert "ucl" in data
        assert "lcl" in data


class TestScnEndpoints:
    @pytest.mark.asyncio
    async def test_supplier_score(self, client, auth_headers):
        r = await client.post(
            f"{SCN_URL}/api/v1/scn/supplier/score",
            json={"supplier_id": "SUP-E2E"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["supplier_id"] == "SUP-E2E"
        assert "composite_score" in data
        assert "xai_explanation" in data


class TestDigitalTwinEndpoints:
    @pytest.mark.asyncio
    async def test_bom_explosion(self, client, auth_headers):
        r = await client.get(
            f"{NETWORK_URL}/api/v1/digital-twin/bom/MO-001",
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["mo_id"] == "MO-001"
        assert data["total_components"] == 6
        assert data["max_depth"] == 2

    @pytest.mark.asyncio
    async def test_supplier_trace(self, client, auth_headers):
        r = await client.get(
            f"{NETWORK_URL}/api/v1/digital-twin/supplier/SUP-001?delay_days=7",
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["supplier_id"] == "SUP-001"
        assert data["tier"] == 1
        assert len(data["affected_components"]) > 0

    @pytest.mark.asyncio
    async def test_disruption_simulation(self, client, auth_headers):
        r = await client.post(
            f"{NETWORK_URL}/api/v1/digital-twin/disrupt",
            json={
                "disruption_type": "supplier_delay",
                "source_id": "SUP-T2-001",
                "delay_days": 14.0,
            },
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["disruption_type"] == "supplier_delay"
        assert data["source_id"] == "SUP-T2-001"
        assert len(data["impacted_mos"]) > 0
        assert data["total_cost_impact"] > 0
        assert data["resolve_time_ms"] < 2000