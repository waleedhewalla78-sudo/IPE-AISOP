"""Release 1 Odoo sync engine — upsert, audit trail, data quality."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.bom import BillOfMaterial, BomLine
from ipe_shared.models.customer import Customer
from ipe_shared.models.data_quality_flag import DataQualityFlag
from ipe_shared.models.demand import DemandLine
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.product import Product
from ipe_shared.models.routing import RoutingOperation
from ipe_shared.models.supplier import Supplier
from ipe_shared.models.supply import SupplyOrder
from ipe_shared.models.sync_run import SyncRun
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.tenant.quotas import QuotaExceededError, assert_quota, count_tenant_resource
from ipe_shared.events.odoo_sync_monitor import odoo_sync_monitor
from ipe_shared.events.odoo_conflict_resolver import ConflictRecord, odoo_conflict_resolver
from ipe_shared.activity.emit import record_from_kafka_topic
from ipe_shared.events.producer import kafka_producer

from app.core.mapper import (
    ODOO_TO_CDM_BOM,
    ODOO_TO_CDM_BOM_LINE,
    ODOO_TO_CDM_DEMAND,
    ODOO_TO_CDM_MO,
    ODOO_TO_CDM_PARTNER,
    ODOO_TO_CDM_PRODUCT,
    ODOO_TO_CDM_ROUTING_OP,
    ODOO_TO_CDM_SUPPLY,
    ODOO_TO_CDM_WC,
    map_odoo_to_cdm,
    normalize_mo_mapped,
)
from app.odoo.client import OdooClient

logger = logging.getLogger(__name__)

MO_SYNC_FIELDS = [
    k for k in ODOO_TO_CDM_MO.keys()
    if k not in ("date_planned_start", "date_planned_finished")
]
WC_SYNC_FIELDS = list(ODOO_TO_CDM_WC.keys())
BOM_SYNC_FIELDS = [k for k in ODOO_TO_CDM_BOM.keys() if k not in ("bom_line_ids", "operation_ids")]
BOM_DETAIL_FIELDS = ["id", "bom_line_ids", "operation_ids"]


def _coerce_datetime(value: datetime | None, fallback: datetime) -> datetime:
    return value if isinstance(value, datetime) else fallback


class OdooSyncEngine:
    def __init__(self, client: OdooClient, tenant_id: UUID, session: AsyncSession):
        self.client = client
        self.tenant_id = tenant_id
        self.session = session
        self._product_cache: dict[str, UUID] = {}
        self._bom_cache: dict[str, UUID] = {}
        self._touched_mo_ids: list[UUID] = []

    async def _ensure_can_create(self, resource_type: str, current_count: int) -> bool:
        try:
            await assert_quota(str(self.tenant_id), resource_type, current_count)
            return True
        except QuotaExceededError as exc:
            logger.warning("Skipping create — %s", exc)
            return False

    @staticmethod
    def _report_odoo_to_ipe(entity_type: str, result: dict[str, Any]) -> None:
        success = int(result.get("errors", 0)) == 0 and "error" not in result
        odoo_sync_monitor.record_sync("odoo_to_ipe", entity_type, "batch", success)

    def _finish_odoo_to_ipe(self, entity_type: str, result: dict[str, Any]) -> dict[str, Any]:
        self._report_odoo_to_ipe(entity_type, result)
        return result

    async def run_full_sync(self, *, trigger: str = "manual") -> dict[str, Any]:
        run = SyncRun(
            tenant_id=self.tenant_id,
            source="odoo",
            trigger=trigger,
            status="running",
            entity_counts={},
        )
        self.session.add(run)
        await self.session.flush()

        counts: dict[str, Any] = {}
        errors: list[str] = []
        try:
            counts["products"] = await self.sync_products()
            counts["work_centers"] = await self.sync_work_centers()
            counts["customers"] = await self.sync_customers()
            counts["suppliers"] = await self.sync_suppliers()
            counts["boms"] = await self.sync_boms()
            counts["bom_details"] = await self.sync_bom_details()
            counts["inventory"] = await self.sync_inventory()
            counts["manufacturing_orders"] = await self.sync_manufacturing_orders()
            counts["demands"] = await self.sync_demands()
            counts["supply"] = await self.sync_supply()
            counts["lead_times"] = await self.sync_lead_times()

            has_errors = any(
                isinstance(v, dict) and v.get("errors", 0) > 0 for v in counts.values()
            )
            run.entity_counts = counts
            await self.session.commit()

            counts["rescored"] = await self._rescore_synced_mos()

            run.status = "partial" if has_errors else "success"
            run.entity_counts = counts
            run.finished_at = datetime.now(UTC)
            await self.session.commit()

            if run.status in ("partial", "failed"):
                from app.core.sync_alerts import notify_sync_failure

                notify_sync_failure(
                    tenant_id=str(self.tenant_id),
                    sync_run_id=str(run.id),
                    status=run.status,
                    error_summary=run.error_summary,
                    entity_counts=counts,
                )

            for entity_type, value in counts.items():
                if isinstance(value, dict) and entity_type not in {"rescored"}:
                    self._report_odoo_to_ipe(entity_type, value)

            if run.status in ("success", "partial"):
                products = counts.get("products", {})
                mos = counts.get("manufacturing_orders", {})
                summary = (
                    f"Odoo sync {run.status}: "
                    f"products updated={products.get('updated', 0) if isinstance(products, dict) else 0} "
                    f"MOs updated={mos.get('updated', 0) if isinstance(mos, dict) else 0}"
                )
                envelope = kafka_producer.build_envelope(
                    event_type="ipe.sync.completed",
                    tenant_id=str(self.tenant_id),
                    payload={
                        "summary": summary,
                        "sync_run_id": str(run.id),
                        "status": run.status,
                        "trigger": trigger,
                        "entity_counts": counts,
                    },
                )
                await record_from_kafka_topic(
                    self.session,
                    "ipe.sync.completed",
                    envelope,
                    tenant_id=str(self.tenant_id),
                )

            return {"sync_run_id": str(run.id), "status": run.status, **counts}
        except Exception as exc:
            logger.exception("Full sync failed for tenant %s", self.tenant_id)
            run.status = "failed"
            run.error_summary = str(exc)[:2000]
            run.finished_at = datetime.now(UTC)
            run.entity_counts = counts
            await self.session.commit()
            from app.core.sync_alerts import notify_sync_failure

            notify_sync_failure(
                tenant_id=str(self.tenant_id),
                sync_run_id=str(run.id),
                status="failed",
                error_summary=run.error_summary,
                entity_counts=counts,
            )
            raise

    async def sync_products(self) -> dict[str, Any]:
        try:
            records = self.client.search_read(
                "product.product",
                [("active", "=", True)],
                fields=list(ODOO_TO_CDM_PRODUCT.keys()),
            )
        except Exception as e:
            logger.error("Odoo product fetch failed: %s", e)
            return self._finish_odoo_to_ipe("products", {"synced": 0, "updated": 0, "total": 0, "errors": 1, "error": str(e)})
        synced, updated = 0, 0
        product_count = await count_tenant_resource(self.session, self.tenant_id, "products")
        for rec in records:
            mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_PRODUCT)
            erp_id = mapped.get("erp_source_id")
            if not erp_id:
                continue
            existing = await self._get_product(erp_id)
            if existing:
                existing.name = mapped.get("name") or existing.name
                existing.internal_ref = mapped.get("internal_ref") or existing.internal_ref
                existing.standard_cost = mapped.get("standard_cost")
                if mapped.get("list_price") is not None and hasattr(existing, "list_price"):
                    existing.list_price = mapped.get("list_price")
                if mapped.get("standard_cost") is not None and hasattr(existing, "unit_cost"):
                    existing.unit_cost = mapped.get("standard_cost")
                if mapped.get("weight") is not None and hasattr(existing, "weight"):
                    existing.weight = mapped.get("weight")
                if mapped.get("qty_available") is not None:
                    existing.safety_stock = mapped.get("qty_available")
                existing.updated_at = datetime.now(UTC)
                updated += 1
            else:
                if not await self._ensure_can_create("products", product_count):
                    continue
                self.session.add(Product(
                    tenant_id=self.tenant_id,
                    erp_source_id=erp_id,
                    erp_source_type="odoo",
                    name=mapped.get("name") or f"Product {erp_id}",
                    internal_ref=mapped.get("internal_ref"),
                    source_type=mapped.get("source_type") or "manufactured",
                    uom=mapped.get("uom") or "unit",
                    standard_cost=mapped.get("standard_cost"),
                    unit_cost=mapped.get("standard_cost"),
                    list_price=mapped.get("list_price"),
                    weight=mapped.get("weight"),
                    safety_stock=mapped.get("qty_available") or 0,
                ))
                product_count += 1
                synced += 1
        await self.session.flush()
        self._product_cache.clear()
        return self._finish_odoo_to_ipe("products", {"synced": synced, "updated": updated, "total": len(records), "errors": 0})

    async def sync_lead_times(self) -> dict[str, Any]:
        """Daily-oriented sync of PO receipt lead times into cdm_lead_time_history."""
        from app.odoo.mappers.lead_time_mapper import LeadTimeMapper

        try:
            mapper = LeadTimeMapper(self.client, self.tenant_id, self.session)
            result = await mapper.sync()
            return self._finish_odoo_to_ipe("lead_times", result)
        except Exception as e:
            logger.error("Lead time sync failed: %s", e)
            return self._finish_odoo_to_ipe(
                "lead_times", {"synced": 0, "skipped": 0, "errors": 1, "error": str(e)}
            )

    async def sync_inventory(self) -> dict[str, Any]:
        """Sync stock.quant levels into product.safety_stock (available qty proxy for R1)."""
        try:
            records = self.client.search_read(
                "stock.quant",
                [("location_id.usage", "=", "internal"), ("quantity", ">", 0)],
                fields=["product_id", "quantity", "reserved_quantity"],
            )
        except Exception as e:
            logger.error("Odoo stock.quant fetch failed: %s", e)
            return self._finish_odoo_to_ipe("inventory", {"updated": 0, "total": 0, "errors": 1, "error": str(e)})

        by_product: dict[str, float] = {}
        for rec in records:
            product_ref = rec.get("product_id")
            if not isinstance(product_ref, (list, tuple)) or not product_ref:
                continue
            pid = str(product_ref[0])
            qty = float(rec.get("quantity") or 0)
            reserved = float(rec.get("reserved_quantity") or 0)
            available = max(qty - reserved, 0)
            by_product[pid] = by_product.get(pid, 0) + available

        updated = 0
        for erp_id, available in by_product.items():
            product = await self._get_product(erp_id)
            if product:
                product.safety_stock = available
                product.updated_at = datetime.now(UTC)
                updated += 1

        await self.session.flush()
        return self._finish_odoo_to_ipe("inventory", {"updated": updated, "total": len(by_product), "errors": 0})

    async def sync_work_centers(self) -> dict[str, Any]:
        try:
            records = self.client.search_read(
                "mrp.workcenter",
                [("active", "=", True)],
                fields=WC_SYNC_FIELDS,
            )
        except Exception as e:
            logger.error("Odoo workcenter fetch failed: %s", e)
            return self._finish_odoo_to_ipe("work_centers", {"synced": 0, "updated": 0, "total": 0, "errors": 1, "error": str(e)})

        synced, updated = 0, 0
        for rec in records:
            mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_WC)
            erp_id = mapped.get("erp_source_id")
            if not erp_id:
                continue
            cap = mapped.get("capacity_hours_per_day") or 8.0
            result = await self.session.execute(
                select(WorkCenter).where(
                    WorkCenter.tenant_id == self.tenant_id,
                    WorkCenter.erp_source_id == erp_id,
                )
            )
            wc = result.scalar_one_or_none()
            if wc:
                wc.name = mapped.get("name") or wc.name
                wc.capacity_hours_per_day = cap
                wc.updated_at = datetime.now(UTC)
                updated += 1
            else:
                self.session.add(WorkCenter(
                    tenant_id=self.tenant_id,
                    erp_source_id=erp_id,
                    name=mapped.get("name") or f"WC {erp_id}",
                    capacity_hours_per_day=cap,
                ))
                synced += 1
        await self.session.flush()
        return self._finish_odoo_to_ipe("work_centers", {"synced": synced, "updated": updated, "total": len(records), "errors": 0})

    async def sync_boms(self) -> dict[str, Any]:
        try:
            records = self.client.search_read(
                "mrp.bom",
                [("active", "=", True)],
                fields=BOM_SYNC_FIELDS,
            )
        except Exception as e:
            logger.error("Odoo BOM fetch failed: %s", e)
            return self._finish_odoo_to_ipe("boms", {"synced": 0, "updated": 0, "total": 0, "errors": 1, "error": str(e)})

        synced, updated, skipped = 0, 0, 0
        bom_count = await count_tenant_resource(self.session, self.tenant_id, "boms")
        for rec in records:
            mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_BOM)
            erp_id = mapped.get("erp_source_id")
            product_erp_id = mapped.get("product_erp_id")
            if not erp_id or not product_erp_id:
                skipped += 1
                continue
            product = await self._get_product(product_erp_id)
            if not product:
                skipped += 1
                continue

            result = await self.session.execute(
                select(BillOfMaterial).where(
                    BillOfMaterial.tenant_id == self.tenant_id,
                    BillOfMaterial.erp_source_id == erp_id,
                )
            )
            bom = result.scalar_one_or_none()
            if bom:
                bom.product_id = product.id
                bom.is_active = True
                updated += 1
            else:
                if not await self._ensure_can_create("boms", bom_count):
                    skipped += 1
                    continue
                self.session.add(BillOfMaterial(
                    tenant_id=self.tenant_id,
                    product_id=product.id,
                    erp_source_id=erp_id,
                    is_active=True,
                ))
                bom_count += 1
                synced += 1
        await self.session.flush()
        self._bom_cache.clear()
        return self._finish_odoo_to_ipe(
            "boms",
            {"synced": synced, "updated": updated, "skipped": skipped, "total": len(records), "errors": 0},
        )

    async def sync_bom_details(self) -> dict[str, Any]:
        """Sync BOM lines and routing operations (Odoo mrp.bom.line + mrp.routing.workcenter)."""
        from sqlalchemy import delete

        lines_synced = 0
        ops_synced = 0
        try:
            records = self.client.search_read(
                "mrp.bom",
                [("active", "=", True)],
                fields=BOM_DETAIL_FIELDS,
            )
        except Exception as e:
            return self._finish_odoo_to_ipe("bom_details", {"lines": 0, "operations": 0, "errors": 1, "error": str(e)})
        routing_count = await count_tenant_resource(self.session, self.tenant_id, "routings")
        for rec in records:
            bom_erp_id = str(rec.get("id"))
            result = await self.session.execute(
                select(BillOfMaterial).where(
                    BillOfMaterial.tenant_id == self.tenant_id,
                    BillOfMaterial.erp_source_id == bom_erp_id,
                )
            )
            bom = result.scalar_one_or_none()
            if not bom:
                continue

            await self.session.execute(
                delete(BomLine).where(
                    BomLine.tenant_id == self.tenant_id,
                    BomLine.bom_id == bom.id,
                )
            )
            await self.session.execute(
                delete(RoutingOperation).where(
                    RoutingOperation.tenant_id == self.tenant_id,
                    RoutingOperation.bom_id == bom.id,
                )
            )
            await self.session.flush()
            routing_count = await count_tenant_resource(self.session, self.tenant_id, "routings")

            line_ids = rec.get("bom_line_ids") or []
            if line_ids:
                line_recs = self.client.read(
                    "mrp.bom.line",
                    line_ids,
                    fields=list(ODOO_TO_CDM_BOM_LINE.keys()),
                )
                for line_rec in line_recs:
                    mapped = map_odoo_to_cdm(line_rec, ODOO_TO_CDM_BOM_LINE)
                    component = await self._get_product(mapped.get("component_erp_id", ""))
                    if not component:
                        continue
                    self.session.add(BomLine(
                        tenant_id=self.tenant_id,
                        bom_id=bom.id,
                        component_id=component.id,
                        quantity_per=mapped.get("quantity_per") or 1,
                        uom=(mapped.get("uom") or "unit")[:16],
                    ))
                    lines_synced += 1

            op_ids = rec.get("operation_ids") or []
            if op_ids:
                op_recs = self.client.read(
                    "mrp.routing.workcenter",
                    op_ids,
                    fields=list(ODOO_TO_CDM_ROUTING_OP.keys()),
                )
                for op_rec in op_recs:
                    mapped = map_odoo_to_cdm(op_rec, ODOO_TO_CDM_ROUTING_OP)
                    wc = await self._get_work_center(mapped.get("work_center_erp_id", ""))
                    if not wc:
                        continue
                    if not await self._ensure_can_create("routings", routing_count):
                        continue
                    self.session.add(RoutingOperation(
                        tenant_id=self.tenant_id,
                        bom_id=bom.id,
                        sequence=mapped.get("sequence") or 100,
                        work_center_id=wc.id,
                        operation_name=mapped.get("operation_name") or "Operation",
                        duration_planned_mins=mapped.get("duration_planned_mins") or 60,
                    ))
                    routing_count += 1
                    ops_synced += 1

        await self.session.flush()
        return self._finish_odoo_to_ipe(
            "bom_details",
            {"lines": lines_synced, "operations": ops_synced, "boms": len(records), "errors": 0},
        )

    async def sync_customers(self) -> dict[str, Any]:
        try:
            records = self.client.search_read(
                "res.partner",
                [("customer_rank", ">", 0)],
                fields=list(ODOO_TO_CDM_PARTNER.keys()),
            )
        except Exception as e:
            return self._finish_odoo_to_ipe("customers", {"synced": 0, "updated": 0, "total": 0, "errors": 1, "error": str(e)})

        synced, updated = 0, 0
        for rec in records:
            mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_PARTNER)
            erp_id = mapped.get("erp_source_id")
            if not erp_id:
                continue
            existing = await self._get_customer(erp_id)
            if existing:
                existing.name = mapped.get("name") or existing.name
                updated += 1
            else:
                self.session.add(Customer(
                    tenant_id=self.tenant_id,
                    erp_source_id=erp_id,
                    name=mapped.get("name") or f"Customer {erp_id}",
                    tier=3,
                ))
                synced += 1
        await self.session.flush()
        return self._finish_odoo_to_ipe("customers", {"synced": synced, "updated": updated, "total": len(records), "errors": 0})

    async def sync_suppliers(self) -> dict[str, Any]:
        try:
            records = self.client.search_read(
                "res.partner",
                [("supplier_rank", ">", 0)],
                fields=list(ODOO_TO_CDM_PARTNER.keys()),
            )
        except Exception as e:
            return self._finish_odoo_to_ipe("suppliers", {"synced": 0, "updated": 0, "total": 0, "errors": 1, "error": str(e)})

        synced, updated = 0, 0
        for rec in records:
            mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_PARTNER)
            erp_id = mapped.get("erp_source_id")
            if not erp_id:
                continue
            existing = await self._get_supplier(erp_id)
            if existing:
                existing.name = mapped.get("name") or existing.name
                existing.updated_at = datetime.now(UTC)
                updated += 1
            else:
                self.session.add(Supplier(
                    tenant_id=self.tenant_id,
                    erp_source_id=erp_id,
                    name=mapped.get("name") or f"Supplier {erp_id}",
                ))
                synced += 1
        await self.session.flush()
        return self._finish_odoo_to_ipe("suppliers", {"synced": synced, "updated": updated, "total": len(records), "errors": 0})

    async def sync_manufacturing_orders(self) -> dict[str, Any]:
        try:
            records = self.client.search_read(
                "mrp.production",
                [("state", "not in", ["cancel"])],
                fields=MO_SYNC_FIELDS,
            )
        except Exception as e:
            logger.error("Odoo MO fetch failed: %s", e)
            return self._finish_odoo_to_ipe(
                "manufacturing_orders",
                {"synced": 0, "updated": 0, "total": 0, "errors": 1, "error": str(e)},
            )

        synced, updated, skipped, errors = 0, 0, 0, 0
        now = datetime.now(UTC)
        self._touched_mo_ids: list[UUID] = []
        mo_count = await count_tenant_resource(self.session, self.tenant_id, "manufacturing_orders")

        for rec in records:
            mapped = normalize_mo_mapped(map_odoo_to_cdm(rec, ODOO_TO_CDM_MO))
            erp_mo_id = mapped.get("erp_mo_id")
            product_erp_id = mapped.get("product_erp_id")
            bom_erp_id = mapped.get("bom_erp_id")

            if not erp_mo_id or not product_erp_id:
                skipped += 1
                continue

            product = await self._get_product(product_erp_id)
            if not product:
                skipped += 1
                continue

            bom = await self._get_bom(bom_erp_id, product.id) if bom_erp_id else None
            if not bom:
                skipped += 1
                continue

            result = await self.session.execute(
                select(ManufacturingOrder).where(
                    ManufacturingOrder.tenant_id == self.tenant_id,
                    ManufacturingOrder.erp_mo_id == erp_mo_id,
                )
            )
            mo = result.scalar_one_or_none()
            odoo_last_update = mapped.get("erp_last_update")

            if mo:
                apply_odoo_schedule = True
                if mo.planned_start and odoo_last_update and mo.erp_synced_at:
                    if odoo_last_update > mo.erp_synced_at and mo.planned_start != mapped.get("planned_start"):
                        ipe_updated = _coerce_datetime(
                            getattr(mo, "updated_at", None),
                            _coerce_datetime(getattr(mo, "erp_synced_at", None), now),
                        )
                        ipe_version = int(getattr(mo, "version", None) or 1)
                        odoo_version = int(getattr(mo, "ai_schedule_version", None) or 1)
                        conflict = ConflictRecord(
                            entity_type="manufacturing_order",
                            entity_id=str(mo.id),
                            ipe_version=ipe_version,
                            ipe_updated_at=ipe_updated,
                            odoo_version=odoo_version,
                            odoo_updated_at=odoo_last_update,
                            ipe_data={
                                "planned_start": mo.planned_start.isoformat() if mo.planned_start else None,
                                "planned_end": mo.planned_end.isoformat() if mo.planned_end else None,
                            },
                            odoo_data={
                                "planned_start": mapped.get("planned_start").isoformat()
                                if mapped.get("planned_start") else None,
                                "planned_end": mapped.get("planned_end").isoformat()
                                if mapped.get("planned_end") else None,
                            },
                        )
                        if odoo_conflict_resolver.detect_conflict(
                            "manufacturing_order",
                            conflict.ipe_version,
                            conflict.ipe_updated_at,
                            conflict.odoo_version,
                            conflict.odoo_updated_at,
                        ):
                            winner, merged = odoo_conflict_resolver.resolve("manufacturing_order", conflict)
                            if winner == "manual":
                                mo.sync_conflict = {
                                    **merged,
                                    "detected_at": now.isoformat(),
                                    "resolution": "manual",
                                }
                                await self._set_flag(mo.id, "SYNC_CONFLICT", "Odoo dates changed after IPE sync")
                                apply_odoo_schedule = False
                            elif winner == "ipe":
                                apply_odoo_schedule = False
                            else:
                                mo.sync_conflict = None

                mo.product_id = product.id
                mo.bom_id = bom.id
                mo.quantity = mapped.get("quantity") or mo.quantity
                if apply_odoo_schedule:
                    mo.planned_start = mapped.get("planned_start") or mo.planned_start
                    mo.planned_end = mapped.get("planned_end") or mo.planned_end
                mo.status = mapped.get("status") or mo.status
                mo.erp_last_update = odoo_last_update
                mo.erp_synced_at = now
                mo.updated_at = now
                updated += 1
                await self._validate_mo(mo, bom.id)
                self._touched_mo_ids.append(mo.id)
            else:
                if not await self._ensure_can_create("manufacturing_orders", mo_count):
                    skipped += 1
                    continue
                mo = ManufacturingOrder(
                    tenant_id=self.tenant_id,
                    erp_mo_id=erp_mo_id,
                    product_id=product.id,
                    bom_id=bom.id,
                    quantity=mapped.get("quantity") or 1,
                    planned_start=mapped.get("planned_start"),
                    planned_end=mapped.get("planned_end"),
                    status=mapped.get("status") or "draft",
                    erp_last_update=odoo_last_update,
                    erp_synced_at=now,
                )
                self.session.add(mo)
                await self.session.flush()
                mo_count += 1
                synced += 1
                await self._validate_mo(mo, bom.id)
                self._touched_mo_ids.append(mo.id)

        await self.session.flush()
        return self._finish_odoo_to_ipe(
            "manufacturing_orders",
            {
                "synced": synced,
                "updated": updated,
                "skipped": skipped,
                "total": len(records),
                "errors": errors,
            },
        )

    async def sync_demands(self) -> dict[str, Any]:
        try:
            records = self.client.search_read(
                "sale.order.line",
                [("state", "in", ["sale", "done"])],
                fields=list(ODOO_TO_CDM_DEMAND.keys()),
            )
        except Exception as e:
            return self._finish_odoo_to_ipe("demands", {"synced": 0, "updated": 0, "total": 0, "errors": 1, "error": str(e)})

        synced, updated, skipped = 0, 0, 0
        for rec in records:
            mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_DEMAND)
            erp_id = mapped.get("erp_source_id")
            product = await self._get_product(mapped.get("product_erp_id", ""))
            if not erp_id or not product:
                skipped += 1
                continue
            existing = await self._get_demand_line(erp_id)
            req_date = mapped.get("required_date") or datetime.now(UTC)
            customer = await self._get_customer(mapped.get("customer_erp_id", "")) if mapped.get("customer_erp_id") else None
            if existing:
                existing.quantity = mapped.get("quantity") or existing.quantity
                existing.required_date = req_date
                if customer:
                    existing.customer_id = customer.id
                updated += 1
            else:
                self.session.add(DemandLine(
                    tenant_id=self.tenant_id,
                    erp_source_id=erp_id,
                    erp_source_type="odoo",
                    product_id=product.id,
                    quantity=mapped.get("quantity") or 1,
                    required_date=req_date,
                    demand_type="MTO",
                    customer_id=customer.id if customer else None,
                ))
                synced += 1
        await self.session.flush()
        return self._finish_odoo_to_ipe(
            "demands",
            {"synced": synced, "updated": updated, "skipped": skipped, "total": len(records), "errors": 0},
        )

    async def sync_supply(self) -> dict[str, Any]:
        try:
            records = self.client.search_read(
                "purchase.order.line",
                [("state", "in", ["purchase", "done"])],
                fields=list(ODOO_TO_CDM_SUPPLY.keys()),
            )
        except Exception as e:
            return self._finish_odoo_to_ipe("supply", {"synced": 0, "updated": 0, "total": 0, "errors": 1, "error": str(e)})

        synced, updated, skipped = 0, 0, 0
        for rec in records:
            mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_SUPPLY)
            erp_id = mapped.get("erp_source_id")
            product = await self._get_product(mapped.get("product_erp_id", ""))
            if not erp_id or not product:
                skipped += 1
                continue
            existing = await self._get_supply_order(erp_id)
            exp_date = mapped.get("expected_date") or datetime.now(UTC)
            supplier = await self._get_supplier(mapped.get("supplier_erp_id", "")) if mapped.get("supplier_erp_id") else None
            if existing:
                existing.quantity_ordered = mapped.get("quantity_ordered") or existing.quantity_ordered
                existing.quantity_received = mapped.get("quantity_received") or existing.quantity_received
                existing.expected_date = exp_date
                if supplier:
                    existing.supplier_id = supplier.id
                updated += 1
            else:
                self.session.add(SupplyOrder(
                    tenant_id=self.tenant_id,
                    erp_source_id=erp_id,
                    erp_source_type="odoo",
                    product_id=product.id,
                    quantity_ordered=mapped.get("quantity_ordered") or 1,
                    quantity_received=mapped.get("quantity_received") or 0,
                    expected_date=exp_date,
                    supplier_id=supplier.id if supplier else None,
                ))
                synced += 1
        await self.session.flush()
        return self._finish_odoo_to_ipe(
            "supply",
            {"synced": synced, "updated": updated, "skipped": skipped, "total": len(records), "errors": 0},
        )

    async def _get_product(self, erp_id: str) -> Product | None:
        if erp_id in self._product_cache:
            result = await self.session.execute(
                select(Product).where(Product.id == self._product_cache[erp_id])
            )
            return result.scalar_one_or_none()
        result = await self.session.execute(
            select(Product).where(
                Product.tenant_id == self.tenant_id,
                Product.erp_source_id == erp_id,
            )
        )
        product = result.scalar_one_or_none()
        if product:
            self._product_cache[erp_id] = product.id
        return product

    async def _get_demand_line(self, erp_id: str) -> DemandLine | None:
        result = await self.session.execute(
            select(DemandLine).where(
                DemandLine.tenant_id == self.tenant_id,
                DemandLine.erp_source_id == erp_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_supply_order(self, erp_id: str) -> SupplyOrder | None:
        result = await self.session.execute(
            select(SupplyOrder).where(
                SupplyOrder.tenant_id == self.tenant_id,
                SupplyOrder.erp_source_id == erp_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_customer(self, erp_id: str) -> Customer | None:
        if not erp_id:
            return None
        result = await self.session.execute(
            select(Customer).where(
                Customer.tenant_id == self.tenant_id,
                Customer.erp_source_id == erp_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_supplier(self, erp_id: str) -> Supplier | None:
        if not erp_id:
            return None
        result = await self.session.execute(
            select(Supplier).where(
                Supplier.tenant_id == self.tenant_id,
                Supplier.erp_source_id == erp_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_work_center(self, erp_id: str) -> WorkCenter | None:
        if not erp_id:
            return None
        result = await self.session.execute(
            select(WorkCenter).where(
                WorkCenter.tenant_id == self.tenant_id,
                WorkCenter.erp_source_id == erp_id,
            )
        )
        return result.scalar_one_or_none()

    async def _rescore_synced_mos(self) -> dict[str, Any]:
        """Trigger fea-svc rescore for MOs touched in this sync run."""
        import os

        import httpx

        mo_ids = getattr(self, "_touched_mo_ids", [])
        if not mo_ids:
            return {"attempted": 0, "success": 0, "scenarios_proposed": 0}

        fea_url = os.getenv("FEA_SVC_URL", "http://fea-svc:8004").rstrip("/")
        success = 0
        proposed = 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"X-Tenant-ID": str(self.tenant_id)}
            for mo_id in mo_ids:
                try:
                    resp = await client.post(
                        f"{fea_url}/api/v1/feasibility/rescore/{mo_id}",
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        body = resp.json()
                        if body.get("success"):
                            success += 1
                            score = (body.get("data") or {}).get("feasibility_score")
                            if score is not None:
                                proposed += await self._auto_propose_scenarios(
                                    client, headers, mo_id, float(score)
                                )
                except Exception as exc:
                    logger.warning("Rescore failed for MO %s: %s", mo_id, exc)
        return {"attempted": len(mo_ids), "success": success, "scenarios_proposed": proposed}

    async def _auto_propose_scenarios(
        self,
        client: "httpx.AsyncClient",
        headers: dict[str, str],
        mo_id: str,
        feasibility_score: float,
    ) -> int:
        """Propose resolution scenarios when MO score is below tenant threshold (FR-R2-01)."""
        threshold = float(os.getenv("AUTO_PROPOSE_THRESHOLD", "75"))
        if feasibility_score >= threshold:
            return 0

        res_url = os.getenv("RES_SVC_URL", "http://res-svc:8005").rstrip("/")
        try:
            resp = await client.post(
                f"{res_url}/api/v1/resolution/scenarios",
                headers=headers,
                json={"mo_id": mo_id},
                timeout=15.0,
            )
            if resp.status_code == 200 and resp.json().get("success"):
                count = len((resp.json().get("data") or {}).get("scenarios") or [])
                logger.info(
                    "Auto-proposed %s scenarios for MO %s (score=%.1f < %.1f)",
                    count,
                    mo_id,
                    feasibility_score,
                    threshold,
                )
                return count
        except Exception as exc:
            logger.warning("Auto-propose failed for MO %s: %s", mo_id, exc)
        return 0

    async def _get_bom(self, bom_erp_id: str | None, product_id: UUID) -> BillOfMaterial | None:
        if bom_erp_id:
            if bom_erp_id in self._bom_cache:
                result = await self.session.execute(
                    select(BillOfMaterial).where(BillOfMaterial.id == self._bom_cache[bom_erp_id])
                )
                return result.scalar_one_or_none()
            result = await self.session.execute(
                select(BillOfMaterial).where(
                    BillOfMaterial.tenant_id == self.tenant_id,
                    BillOfMaterial.erp_source_id == bom_erp_id,
                )
            )
            bom = result.scalar_one_or_none()
            if bom:
                self._bom_cache[bom_erp_id] = bom.id
                return bom

        result = await self.session.execute(
            select(BillOfMaterial).where(
                BillOfMaterial.tenant_id == self.tenant_id,
                BillOfMaterial.product_id == product_id,
                BillOfMaterial.is_active.is_(True),
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def _validate_mo(self, mo: ManufacturingOrder, bom_id: UUID) -> None:
        await self._clear_flags(mo.id)
        if not bom_id:
            await self._set_flag(mo.id, "MISSING_BOM", "No bill of materials linked")
            mo.feasibility_score = None
            return

        from sqlalchemy import text

        routing = await self.session.execute(
            text("SELECT 1 FROM cdm_routing_operation WHERE bom_id = :bom_id LIMIT 1"),
            {"bom_id": bom_id},
        )
        if routing.first() is None:
            await self._set_flag(mo.id, "MISSING_ROUTING", "BOM has no routing operations")
            mo.feasibility_score = None
            return

        wc_count = await self.session.execute(
            text("SELECT COUNT(*) FROM cdm_work_center WHERE tenant_id = :tid"),
            {"tid": self.tenant_id},
        )
        if (wc_count.scalar() or 0) == 0:
            await self._set_flag(mo.id, "MISSING_WC", "No work centers synced from Odoo")

    async def _set_flag(self, mo_id: UUID, code: str, message: str) -> None:
        await self.session.execute(
            update(DataQualityFlag)
            .where(
                DataQualityFlag.tenant_id == self.tenant_id,
                DataQualityFlag.mo_id == mo_id,
                DataQualityFlag.flag_code == code,
                DataQualityFlag.resolved_at.is_(None),
            )
            .values(resolved_at=datetime.now(UTC))
        )
        self.session.add(DataQualityFlag(
            tenant_id=self.tenant_id,
            mo_id=mo_id,
            flag_code=code,
            message=message,
        ))

    async def _clear_flags(self, mo_id: UUID) -> None:
        await self.session.execute(
            update(DataQualityFlag)
            .where(
                DataQualityFlag.tenant_id == self.tenant_id,
                DataQualityFlag.mo_id == mo_id,
                DataQualityFlag.resolved_at.is_(None),
            )
            .values(resolved_at=datetime.now(UTC))
        )
