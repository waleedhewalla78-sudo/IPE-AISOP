import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.digital_twin import (
    BOMNode,
    DigitalTwinService,
    DisruptionImpact,
    SupplierDownstreamImpact,
)


def _row(*values):
    r = MagicMock()
    r.__getitem__ = lambda self, i: values[i]
    return r


@pytest.fixture
def session():
    s = AsyncMock()
    s.execute = AsyncMock()
    return s


@pytest.fixture
def svc(session):
    return DigitalTwinService(session)


class TestBOMExplosion:
    @pytest.mark.asyncio
    async def test_explode_bom_known_mo(self, svc, session):
        mo_id = "MO-001"
        mo_uuid = uuid.uuid4()

        res1 = MagicMock()
        res1.scalar_one_or_none.return_value = mo_uuid
        res2 = MagicMock()
        res2.fetchall.return_value = [
            _row("C1", mo_uuid, 1, 1.0, 5.0, "SUP-1", "Comp1", "purchased"),
            _row("C2", "C1", 2, 2.0, 3.0, "SUP-2", "Comp2", "purchased"),
            _row("C3", "C1", 2, 1.0, 4.0, "SUP-3", "Comp3", "purchased"),
            _row("C4", mo_uuid, 1, 1.0, 6.0, "SUP-4", "Comp4", "purchased"),
            _row("C5", "C4", 2, 3.0, 2.0, "SUP-5", "Comp5", "purchased"),
            _row("C6", "C4", 2, 1.0, 1.0, "SUP-6", "Comp6", "purchased"),
        ]
        session.execute = AsyncMock(side_effect=[res1, res2])

        nodes = await svc.explode_bom(mo_id)
        assert len(nodes) == 6
        assert nodes[0].level == 1
        assert max(n.level for n in nodes) == 2

    @pytest.mark.asyncio
    async def test_explode_bom_second_mo(self, svc, session):
        mo_id = "MO-002"
        mo_uuid = uuid.uuid4()

        res1 = MagicMock()
        res1.scalar_one_or_none.return_value = mo_uuid
        res2 = MagicMock()
        res2.fetchall.return_value = [
            _row("C1", mo_uuid, 1, 1.0, 5.0, "SUP-1", "Comp1", "purchased"),
            _row("C2", "C1", 2, 1.0, 3.0, "SUP-2", "Comp2", "purchased"),
            _row("C3", "C1", 2, 1.0, 4.0, "SUP-3", "Comp3", "purchased"),
        ]
        session.execute = AsyncMock(side_effect=[res1, res2])

        nodes = await svc.explode_bom(mo_id)
        assert len(nodes) == 3
        leaf_nodes = [n for n in nodes if n.is_leaf]
        assert len(leaf_nodes) == 2

    @pytest.mark.asyncio
    async def test_explode_bom_unknown_mo(self, svc, session):
        res1 = MagicMock()
        res1.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=res1)

        nodes = await svc.explode_bom("MO-999")
        assert len(nodes) == 0

    @pytest.mark.asyncio
    async def test_bom_node_attributes(self, svc, session):
        mo_id = "MO-001"
        mo_uuid = uuid.uuid4()

        res1 = MagicMock()
        res1.scalar_one_or_none.return_value = mo_uuid
        res2 = MagicMock()
        res2.fetchall.return_value = [
            _row("SUB-ASSY-001", str(mo_uuid), 1, 1.0, 5.0, "SUP-001", "Main Assembly", "purchased"),
        ]
        session.execute = AsyncMock(side_effect=[res1, res2])

        nodes = await svc.explode_bom(mo_id)
        sub_assy = [n for n in nodes if n.component_id == "SUB-ASSY-001"][0]
        assert sub_assy.component_name == "Main Assembly"
        assert sub_assy.parent_id == str(mo_uuid)
        assert sub_assy.lead_time_days > 0
        assert sub_assy.quantity_per == 1.0
        assert sub_assy.supplier_id == "SUP-001"

    @pytest.mark.asyncio
    async def test_leaf_nodes_have_no_children(self, svc, session):
        mo_id = "MO-001"
        mo_uuid = uuid.uuid4()

        res1 = MagicMock()
        res1.scalar_one_or_none.return_value = mo_uuid
        res2 = MagicMock()
        res2.fetchall.return_value = [
            _row("C1", mo_uuid, 1, 1.0, 5.0, "SUP-1", "Comp1", "purchased"),
            _row("C2", "C1", 2, 1.0, 3.0, "SUP-2", "Comp2", "purchased"),
            _row("C3", "C1", 2, 1.0, 4.0, "SUP-3", "Comp3", "purchased"),
        ]
        session.execute = AsyncMock(side_effect=[res1, res2])

        nodes = await svc.explode_bom(mo_id)
        leaf_nodes = [n for n in nodes if n.is_leaf]
        for leaf in leaf_nodes:
            assert leaf.level == 2

    @pytest.mark.asyncio
    async def test_max_depth_is_2(self, svc, session):
        mo_id = "MO-001"
        mo_uuid = uuid.uuid4()

        res1 = MagicMock()
        res1.scalar_one_or_none.return_value = mo_uuid
        res2 = MagicMock()
        res2.fetchall.return_value = [
            _row("C1", mo_uuid, 1, 1.0, 5.0, "SUP-1", "Comp1", "purchased"),
            _row("C2", "C1", 2, 1.0, 3.0, "SUP-2", "Comp2", "purchased"),
        ]
        session.execute = AsyncMock(side_effect=[res1, res2])

        nodes = await svc.explode_bom(mo_id)
        assert max(n.level for n in nodes) == 2


class TestSupplierTrace:
    @pytest.mark.asyncio
    async def test_trace_tier1_supplier(self, svc, session):
        sup_uuid = uuid.uuid4()
        prod_uuid = uuid.uuid4()
        mo_uuid = uuid.uuid4()

        res1 = MagicMock()
        res1.scalar_one_or_none.return_value = sup_uuid
        res2 = MagicMock()
        res2.first.return_value = (sup_uuid, "Acme Assemblies")
        res3 = MagicMock()
        res3.fetchall.return_value = [(mo_uuid, "C1", 0)]
        res4 = MagicMock()
        res4.fetchall.return_value = [(mo_uuid,)]
        res5 = MagicMock()
        res5.fetchall.return_value = [(prod_uuid,)]
        res6 = MagicMock()
        res6.fetchall.return_value = []
        session.execute = AsyncMock(side_effect=[res1, res2, res3, res4, res5, res6])

        impact = await svc.trace_supplier("SUP-001", 7.0)
        assert impact.supplier_name == "Acme Assemblies"
        assert len(impact.affected_components) > 0
        assert len(impact.affected_mos) > 0
        assert impact.total_delay_days > 0

    @pytest.mark.asyncio
    async def test_trace_unknown_supplier(self, svc, session):
        res1 = MagicMock()
        res1.first.return_value = None
        session.execute = AsyncMock(return_value=res1)

        impact = await svc.trace_supplier("SUP-UNKNOWN", 5.0)
        assert len(impact.affected_components) == 0
        assert len(impact.affected_mos) == 0
        assert impact.total_delay_days == 0.0

    @pytest.mark.asyncio
    async def test_propagation_path_includes_self(self, svc, session):
        sup_uuid = uuid.uuid4()

        res1 = MagicMock()
        res1.scalar_one_or_none.return_value = sup_uuid
        res2 = MagicMock()
        res2.first.return_value = (sup_uuid, "Acme")
        res3 = MagicMock()
        res3.fetchall.return_value = []
        res4 = MagicMock()
        res4.fetchall.return_value = []
        session.execute = AsyncMock(side_effect=[res1, res2, res3, res4])

        impact = await svc.trace_supplier("SUP-003", 3.0)
        assert impact.supplier_id in impact.propagation_path

    @pytest.mark.asyncio
    async def test_delay_scales_with_tier(self, svc, session):
        sup_uuid_t1 = uuid.uuid4()
        root_uuid1 = uuid.uuid4()

        res1 = MagicMock()
        res1.first.return_value = (sup_uuid_t1,)
        res2 = MagicMock()
        res2.first.return_value = (sup_uuid_t1, "Supplier")
        res3 = MagicMock()
        res3.fetchall.return_value = [(root_uuid1, "C1", 0)]
        res4 = MagicMock()
        res4.fetchall.return_value = []
        res5 = MagicMock()
        res5.fetchall.return_value = []
        session.execute = AsyncMock(side_effect=[res1, res2, res3, res4, res5])

        impact_short = await svc.trace_supplier("SUP-001", 3.0)

        sup_uuid_t2 = uuid.uuid4()
        root_uuid2 = uuid.uuid4()
        res6 = MagicMock()
        res6.first.return_value = (sup_uuid_t2,)
        res7 = MagicMock()
        res7.first.return_value = (sup_uuid_t2, "Supplier")
        res8 = MagicMock()
        res8.fetchall.return_value = [(root_uuid2, "C2", 0)]
        res9 = MagicMock()
        res9.fetchall.return_value = []
        res10 = MagicMock()
        res10.fetchall.return_value = []
        session.execute = AsyncMock(side_effect=[res6, res7, res8, res9, res10])

        impact_long = await svc.trace_supplier("SUP-T2-001", 14.0)
        assert impact_long.total_delay_days > impact_short.total_delay_days


class TestDisruptionSimulation:
    @pytest.mark.asyncio
    async def test_supplier_delay_disruption(self, svc, session):
        sup_uuid = uuid.uuid4()
        prod_uuid = uuid.uuid4()
        mo_uuid = uuid.uuid4()

        res1 = MagicMock()
        res1.scalar_one_or_none.return_value = sup_uuid
        res2 = MagicMock()
        res2.first.return_value = (sup_uuid, "Acme Assemblies")
        res3 = MagicMock()
        res3.fetchall.return_value = [(mo_uuid, "C1", 0)]
        res4 = MagicMock()
        res4.fetchall.return_value = [(mo_uuid,)]
        res5 = MagicMock()
        res5.fetchall.return_value = [(prod_uuid,)]
        res6 = MagicMock()
        res6.fetchall.return_value = []
        session.execute = AsyncMock(side_effect=[res1, res2, res3, res4, res5, res6])

        result = await svc.simulate_disruption(
            disruption_type="supplier_delay",
            source_id="SUP-T2-001",
            delay_days=14.0,
        )
        assert result.disruption_type == "supplier_delay"
        assert result.source_id == "SUP-T2-001"
        assert result.delay_days == 14.0
        assert len(result.impacted_mos) > 0
        assert result.total_cost_impact > 0
        assert result.resolve_time_ms < 2000

    @pytest.mark.asyncio
    async def test_port_strike_disruption(self, svc, session):
        sup_uuid = uuid.uuid4()

        res1 = MagicMock()
        res1.scalar_one_or_none.return_value = sup_uuid
        res2 = MagicMock()
        res2.first.return_value = (sup_uuid, "Port Authority")
        res3 = MagicMock()
        res3.fetchall.return_value = []
        res4 = MagicMock()
        res4.fetchall.return_value = []
        session.execute = AsyncMock(side_effect=[res1, res2, res3, res4])

        result = await svc.simulate_disruption(
            disruption_type="port_strike",
            source_id="SUP-003",
            delay_days=21.0,
        )
        assert result.disruption_type == "port_strike"
        assert len(result.impacted_suppliers) > 0

    @pytest.mark.asyncio
    async def test_disruption_cost_proportional(self, svc, session):
        sup_uuid = uuid.uuid4()
        prod_uuid = uuid.uuid4()
        mo_uuid = uuid.uuid4()

        def make_effects():
            res1 = MagicMock()
            res1.scalar_one_or_none.return_value = sup_uuid
            res2 = MagicMock()
            res2.first.return_value = (sup_uuid, "Supplier")
            res3 = MagicMock()
            res3.fetchall.return_value = [(mo_uuid, "C1", 0)]
            res4 = MagicMock()
            res4.fetchall.return_value = [(mo_uuid,)]
            res5 = MagicMock()
            res5.fetchall.return_value = [(prod_uuid,)]
            res6 = MagicMock()
            res6.fetchall.return_value = []
            return [res1, res2, res3, res4, res5, res6]

        session.execute = AsyncMock(side_effect=make_effects() + make_effects())

        r1 = await svc.simulate_disruption("supplier_delay", "SUP-001", 7.0)
        r2 = await svc.simulate_disruption("supplier_delay", "SUP-001", 14.0)
        assert r2.total_cost_impact > r1.total_cost_impact

    @pytest.mark.asyncio
    async def test_resolve_time_fast(self, svc, session):
        sup_uuid = uuid.uuid4()

        res1 = MagicMock()
        res1.scalar_one_or_none.return_value = sup_uuid
        res2 = MagicMock()
        res2.first.return_value = (sup_uuid, "Supplier")
        res3 = MagicMock()
        res3.fetchall.return_value = []
        res4 = MagicMock()
        res4.fetchall.return_value = []
        session.execute = AsyncMock(side_effect=[res1, res2, res3, res4])

        result = await svc.simulate_disruption("supplier_delay", "SUP-001", 7.0)
        assert result.resolve_time_ms < 100

    @pytest.mark.asyncio
    async def test_disruption_includes_supplier_tier(self, svc, session):
        sup_uuid = uuid.uuid4()

        res1 = MagicMock()
        res1.scalar_one_or_none.return_value = sup_uuid
        res2 = MagicMock()
        res2.first.return_value = (sup_uuid, "Tier2 Supplier")
        res3 = MagicMock()
        res3.fetchall.return_value = []
        res4 = MagicMock()
        res4.fetchall.return_value = []
        session.execute = AsyncMock(side_effect=[res1, res2, res3, res4])

        result = await svc.simulate_disruption("supplier_delay", "SUP-T2-001", 14.0)
        supplier_ids = [s["supplier_id"] for s in result.impacted_suppliers]
        assert "SUP-T2-001" in supplier_ids
