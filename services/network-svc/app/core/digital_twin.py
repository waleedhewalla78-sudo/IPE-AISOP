from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.supplier import Supplier
from ipe_shared.models.supply import SupplyOrder

logger = logging.getLogger(__name__)


@dataclass
class BOMNode:
    component_id: str
    component_name: str
    level: int
    parent_id: str | None
    lead_time_days: float
    quantity_per: float
    supplier_id: str | None
    is_leaf: bool


@dataclass
class SupplierDownstreamImpact:
    supplier_id: str
    supplier_name: str
    tier: int
    affected_components: list[str]
    affected_mos: list[str]
    total_delay_days: float
    propagation_path: list[str]


@dataclass
class DisruptionImpact:
    disruption_type: str
    source_id: str
    delay_days: float
    impacted_mos: list[dict[str, Any]]
    impacted_suppliers: list[dict[str, Any]]
    total_cost_impact: float
    resolve_time_ms: float


_BOM_EXPLODE_SQL = text("""
WITH RECURSIVE bom_tree AS (
    SELECT
        bl.component_id,
        mo.product_id AS parent_product_id,
        1 AS level,
        bl.quantity_per,
        COALESCE(p.lead_time_days, 0) AS lead_time_days,
        so_q.supplier_id,
        COALESCE(p.name, '') AS component_name,
        COALESCE(p.source_type, 'purchased') AS source_type
    FROM cdm_manufacturing_order mo
    JOIN cdm_bill_of_material bom ON mo.bom_id = bom.id
    JOIN cdm_bom_line bl ON bl.bom_id = bom.id
    LEFT JOIN cdm_product p ON p.id = bl.component_id
    LEFT JOIN LATERAL (
        SELECT so.supplier_id
        FROM cdm_supply_order so
        WHERE so.product_id = bl.component_id
          AND so.status IN ('confirmed', 'planned', 'open')
        ORDER BY so.expected_date ASC
        LIMIT 1
    ) so_q ON true
    WHERE mo.id = :mo_id

    UNION ALL

    SELECT
        bl.component_id,
        bt.component_id AS parent_product_id,
        bt.level + 1,
        bl.quantity_per,
        COALESCE(p.lead_time_days, 0),
        so_q.supplier_id,
        COALESCE(p.name, ''),
        COALESCE(p.source_type, 'purchased')
    FROM bom_tree bt
    JOIN cdm_bill_of_material sub_bom
        ON sub_bom.product_id = bt.component_id AND sub_bom.is_active = true
    JOIN cdm_bom_line bl ON bl.bom_id = sub_bom.id
    LEFT JOIN cdm_product p ON p.id = bl.component_id
    LEFT JOIN LATERAL (
        SELECT so.supplier_id
        FROM cdm_supply_order so
        WHERE so.product_id = bl.component_id
          AND so.status IN ('confirmed', 'planned', 'open')
        ORDER BY so.expected_date ASC
        LIMIT 1
    ) so_q ON true
    WHERE bt.level < 10
)
SELECT
    component_id,
    parent_product_id,
    level,
    quantity_per,
    lead_time_days,
    supplier_id,
    component_name,
    source_type
FROM bom_tree
ORDER BY level, component_id
""")


_SUPPLIER_TRACE_SQL = text("""
WITH RECURSIVE bom_ancestors AS (
    SELECT
        bom.id AS bom_id,
        bom.product_id,
        bom.parent_bom_id,
        bl.component_id,
        0 AS depth
    FROM cdm_supply_order so
    JOIN cdm_bom_line bl ON bl.component_id = so.product_id
    JOIN cdm_bill_of_material bom ON bom.id = bl.bom_id
    WHERE so.supplier_id = :supplier_id
      AND so.status IN ('confirmed', 'planned', 'open')
      AND bom.is_active = true

    UNION ALL

    SELECT
        parent.id,
        parent.product_id,
        parent.parent_bom_id,
        ba.component_id,
        ba.depth + 1
    FROM bom_ancestors ba
    JOIN cdm_bill_of_material parent ON parent.id = ba.parent_bom_id
    WHERE parent.is_active = true
      AND ba.depth < 10
)
SELECT DISTINCT
    ba.product_id AS root_product_id,
    ba.component_id,
    MIN(ba.depth) AS min_depth
FROM bom_ancestors ba
WHERE ba.parent_bom_id IS NULL
GROUP BY ba.product_id, ba.component_id
""")


class DigitalTwinService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _resolve_mo_id(self, mo_id: str) -> UUID | None:
        try:
            mo_uuid = UUID(mo_id)
            result = await self.session.execute(
                select(ManufacturingOrder.id).where(
                    ManufacturingOrder.id == mo_uuid
                )
            )
            if result.scalar_one_or_none():
                return mo_uuid
        except (ValueError, AttributeError) as e:
            logger.debug("MO ID '%s' not a valid UUID, fallback to ERP: %s", mo_id, e)

        result = await self.session.execute(
            select(ManufacturingOrder.id).where(
                ManufacturingOrder.erp_mo_id == mo_id
            )
        )
        row = result.first()
        return row[0] if row else None

    async def _resolve_supplier_id(self, supplier_id: str) -> UUID | None:
        try:
            sup_uuid = UUID(supplier_id)
            result = await self.session.execute(
                select(Supplier.id).where(Supplier.id == sup_uuid)
            )
            if result.scalar_one_or_none():
                return sup_uuid
        except (ValueError, AttributeError) as e:
            logger.debug("Supplier ID '%s' not UUID, fallback to ERP: %s", supplier_id, e)

        result = await self.session.execute(
            select(Supplier.id).where(Supplier.erp_source_id == supplier_id)
        )
        row = result.first()
        return row[0] if row else None

    async def explode_bom(self, mo_id: str) -> list[BOMNode]:
        mo_uuid = await self._resolve_mo_id(mo_id)
        if mo_uuid is None:
            return []

        result = await self.session.execute(
            _BOM_EXPLODE_SQL, {"mo_id": mo_uuid}
        )
        rows = result.fetchall()
        if not rows:
            return []

        parent_ids = set()
        for row in rows:
            pid = str(row[1]) if row[1] else None
            if pid:
                parent_ids.add(pid)

        nodes: list[BOMNode] = []
        for row in rows:
            component_id = str(row[0])
            parent_product_id = str(row[1]) if row[1] else mo_id
            level = int(row[2])
            quantity_per = float(row[3]) if row[3] is not None else 0.0
            lead_time_days = float(row[4]) if row[4] is not None else 0.0
            supplier_id = str(row[5]) if row[5] else None
            component_name = row[6] or ""
            source_type = row[7] or "purchased"

            is_leaf = component_id not in parent_ids and source_type != "manufactured"

            nodes.append(BOMNode(
                component_id=component_id,
                component_name=component_name,
                level=level,
                parent_id=parent_product_id,
                lead_time_days=lead_time_days,
                quantity_per=quantity_per,
                supplier_id=supplier_id,
                is_leaf=is_leaf,
            ))
        return nodes

    async def trace_supplier(self, supplier_id: str, delay_days: float = 7.0) -> SupplierDownstreamImpact:
        sup_uuid = await self._resolve_supplier_id(supplier_id)
        if sup_uuid is None:
            return SupplierDownstreamImpact(
                supplier_id=supplier_id,
                supplier_name=supplier_id,
                tier=1,
                affected_components=[],
                affected_mos=[],
                total_delay_days=0.0,
                propagation_path=[supplier_id],
            )

        sup_result = await self.session.execute(
            select(Supplier.id, Supplier.name).where(Supplier.id == sup_uuid)
        )
        sup_row = sup_result.first()
        supplier_name = sup_row[1] if sup_row else supplier_id

        trace_result = await self.session.execute(
            _SUPPLIER_TRACE_SQL, {"supplier_id": sup_uuid}
        )
        trace_rows = trace_result.fetchall()

        affected_components: list[str] = []
        affected_mos: list[str] = []
        min_depth = 1

        if trace_rows:
            component_ids = set()
            root_product_ids = set()
            for row in trace_rows:
                comp_id = str(row[1])
                root_id = str(row[0])
                component_ids.add(comp_id)
                root_product_ids.add(root_id)
                min_depth = min(min_depth, int(row[2]) + 1)

            affected_components = list(component_ids)

            if root_product_ids:
                mo_result = await self.session.execute(
                    select(ManufacturingOrder.id).where(
                        ManufacturingOrder.product_id.in_(
                            [UUID(pid) for pid in root_product_ids]
                        )
                    )
                )
                affected_mos = [str(r[0]) for r in mo_result.fetchall()]

        total_delay = delay_days * min_depth * 0.7

        propagation_path = [supplier_id]

        supplied_result = await self.session.execute(
            select(SupplyOrder.product_id).where(
                SupplyOrder.supplier_id == sup_uuid,
                SupplyOrder.status.in_(["confirmed", "planned", "open"]),
            )
        )
        supplied_product_ids = [str(r[0]) for r in supplied_result.fetchall()]

        if supplied_product_ids:
            upstream_result = await self.session.execute(
                select(SupplyOrder.supplier_id).where(
                    SupplyOrder.product_id.in_(
                        [UUID(pid) for pid in supplied_product_ids]
                    ),
                    SupplyOrder.supplier_id != sup_uuid,
                    SupplyOrder.status.in_(["confirmed", "planned", "open"]),
                )
            )
            for r in upstream_result.fetchall():
                sid = str(r[0])
                if sid not in propagation_path:
                    propagation_path.append(sid)

        return SupplierDownstreamImpact(
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            tier=min_depth,
            affected_components=affected_components,
            affected_mos=affected_mos,
            total_delay_days=round(total_delay, 2),
            propagation_path=propagation_path,
        )

    async def simulate_disruption(
        self, disruption_type: str, source_id: str, delay_days: float
    ) -> DisruptionImpact:
        start = time.monotonic()

        impact = await self.trace_supplier(source_id, delay_days)

        impacted_mos = [
            {
                "mo_id": mo_id,
                "delay_days": impact.total_delay_days,
                "affected_components": impact.affected_components,
                "revenue_at_risk": round(len(impact.affected_components) * 15000, 2),
            }
            for mo_id in impact.affected_mos
        ]

        impacted_suppliers = [
            {"supplier_id": sid, "tier": impact.tier}
            for sid in impact.propagation_path
        ]

        total_cost_impact = delay_days * len(impact.affected_components) * 5000
        elapsed = (time.monotonic() - start) * 1000.0

        return DisruptionImpact(
            disruption_type=disruption_type,
            source_id=source_id,
            delay_days=delay_days,
            impacted_mos=impacted_mos,
            impacted_suppliers=impacted_suppliers,
            total_cost_impact=round(total_cost_impact, 2),
            resolve_time_ms=round(elapsed, 2),
        )