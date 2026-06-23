from unittest.mock import patch

import pytest
from uuid import UUID

from app.core.digital_twin import BOMNode, DigitalTwinService, DisruptionImpact, SupplierDownstreamImpact
from ipe_shared.auth.jwt import create_access_token


def _bom_nodes_mo001() -> list[BOMNode]:
    return [
        BOMNode("C1", "Comp1", 1, "MO-001", 5.0, 1.0, "SUP-1", False),
        BOMNode("C2", "Comp2", 2, "C1", 3.0, 2.0, "SUP-2", True),
        BOMNode("C3", "Comp3", 2, "C1", 4.0, 1.0, "SUP-3", True),
        BOMNode("C4", "Comp4", 1, "MO-001", 6.0, 1.0, "SUP-4", False),
        BOMNode("C5", "Comp5", 2, "C4", 2.0, 3.0, "SUP-5", True),
        BOMNode("C6", "Comp6", 2, "C4", 1.0, 1.0, "SUP-6", True),
    ]


@pytest.fixture(autouse=True)
def mock_digital_twin_service():
    async def explode_bom(self, mo_id: str):
        if mo_id == "MO-001":
            return _bom_nodes_mo001()
        return []

    async def trace_supplier(self, supplier_id: str, delay_days: float = 7.0):
        if supplier_id == "SUP-001":
            return SupplierDownstreamImpact(
                supplier_id="SUP-001",
                supplier_name="Supplier One",
                tier=1,
                affected_components=["C1", "C4"],
                affected_mos=["MO-001"],
                total_delay_days=delay_days,
                propagation_path=["SUP-001", "C1", "MO-001"],
            )
        if supplier_id == "SUP-T2-001":
            return SupplierDownstreamImpact(
                supplier_id="SUP-T2-001",
                supplier_name="Tier 2 Supplier",
                tier=2,
                affected_components=["C2"],
                affected_mos=["MO-001"],
                total_delay_days=delay_days,
                propagation_path=["SUP-T2-001", "C2", "MO-001"],
            )
        return SupplierDownstreamImpact(
            supplier_id=supplier_id,
            supplier_name="Unknown",
            tier=1,
            affected_components=[],
            affected_mos=[],
            total_delay_days=delay_days,
            propagation_path=[],
        )

    async def simulate_disruption(self, disruption_type: str, source_id: str, delay_days: float = 7.0):
        return DisruptionImpact(
            disruption_type=disruption_type,
            source_id=source_id,
            delay_days=delay_days,
            impacted_mos=[{"mo_id": "MO-001", "delay_days": delay_days}],
            impacted_suppliers=[{"supplier_id": source_id, "tier": 2}],
            total_cost_impact=12500.0,
            resolve_time_ms=42.5,
        )

    with (
        patch.object(DigitalTwinService, "explode_bom", explode_bom),
        patch.object(DigitalTwinService, "trace_supplier", trace_supplier),
        patch.object(DigitalTwinService, "simulate_disruption", simulate_disruption),
    ):
        yield


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


class TestBOMExplosionAPI:
    @pytest.mark.asyncio
    async def test_bom_explosion(self, client, auth_headers):
        resp = await client.get("/api/v1/digital-twin/bom/MO-001", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["mo_id"] == "MO-001"
        assert data["total_components"] == 6
        assert data["max_depth"] == 2

    @pytest.mark.asyncio
    async def test_bom_explosion_unknown(self, client, auth_headers):
        resp = await client.get("/api/v1/digital-twin/bom/MO-999", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_components"] == 0


class TestSupplierTraceAPI:
    @pytest.mark.asyncio
    async def test_supplier_trace(self, client, auth_headers):
        resp = await client.get(
            "/api/v1/digital-twin/supplier/SUP-001?delay_days=7",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["supplier_id"] == "SUP-001"
        assert data["tier"] == 1
        assert len(data["affected_components"]) > 0

    @pytest.mark.asyncio
    async def test_supplier_trace_tier2(self, client, auth_headers):
        resp = await client.get(
            "/api/v1/digital-twin/supplier/SUP-T2-001?delay_days=14",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["tier"] == 2


class TestDisruptionSimulationAPI:
    @pytest.mark.asyncio
    async def test_disruption_simulation(self, client, auth_headers):
        resp = await client.post(
            "/api/v1/digital-twin/disrupt",
            json={
                "disruption_type": "supplier_delay",
                "source_id": "SUP-T2-001",
                "delay_days": 14.0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["disruption_type"] == "supplier_delay"
        assert data["source_id"] == "SUP-T2-001"
        assert len(data["impacted_mos"]) > 0
        assert data["total_cost_impact"] > 0
        assert data["resolve_time_ms"] < 2000
