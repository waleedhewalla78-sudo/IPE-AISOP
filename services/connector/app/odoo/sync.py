import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.product import Product
from ipe_shared.models.demand import DemandLine
from ipe_shared.models.supply import SupplyOrder
from ipe_shared.models.bom import BillOfMaterial, BomLine
from ipe_shared.events.producer import kafka_producer

from app.odoo.client import OdooClient
from app.core.mapper import (
    ODOO_TO_CDM_PRODUCT,
    ODOO_TO_CDM_DEMAND,
    ODOO_TO_CDM_SUPPLY,
    map_odoo_to_cdm,
)

logger = logging.getLogger(__name__)


class SyncAdapter:
    def __init__(self, client: OdooClient, tenant_id: UUID, session: AsyncSession):
        self.client = client
        self.tenant_id = tenant_id
        self.session = session

    async def sync_products(self) -> dict:
        try:
            records = self.client.search_read(
                "product.product",
                [("active", "=", True)],
                fields=list(ODOO_TO_CDM_PRODUCT.keys()),
            )
        except Exception as e:
            logger.error("Odoo product fetch failed: %s", e)
            return {"synced": 0, "error": str(e)}

        synced = 0
        for rec in records:
            mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_PRODUCT)
            mapped["tenant_id"] = self.tenant_id
            mapped["erp_source_type"] = "odoo"
            existing = await self.session.execute(
                select(Product).where(
                    Product.tenant_id == self.tenant_id,
                    Product.erp_source_id == mapped["erp_source_id"],
                )
            )
            if existing.scalar_one_or_none():
                continue
            self.session.add(Product(**mapped))
            synced += 1
        await self.session.commit()

        if synced > 0:
            await kafka_producer.send_event("supply", "updated", str(self.tenant_id), {
                "tenant_id": str(self.tenant_id),
                "products_synced": synced,
                "timestamp": datetime.utcnow().isoformat(),
            })

        return {"synced": synced, "total": len(records)}

    async def sync_demands(self) -> dict:
        try:
            records = self.client.search_read(
                "sale.order.line",
                [("state", "in", ["sale", "done"])],
                fields=list(ODOO_TO_CDM_DEMAND.keys()),
            )
        except Exception as e:
            logger.error("Odoo demand fetch failed: %s", e)
            return {"synced": 0, "error": str(e)}

        synced = 0
        for rec in records:
            mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_DEMAND)
            mapped["tenant_id"] = self.tenant_id
            mapped["erp_source_type"] = "odoo"
            mapped["demand_type"] = "MTO"
            existing = await self.session.execute(
                select(DemandLine).where(
                    DemandLine.tenant_id == self.tenant_id,
                    DemandLine.erp_source_id == mapped["erp_source_id"],
                )
            )
            if existing.scalar_one_or_none():
                continue
            self.session.add(DemandLine(**mapped))
            synced += 1
        await self.session.commit()

        if synced > 0:
            await kafka_producer.send_event("demand", "created", str(self.tenant_id), {
                "tenant_id": str(self.tenant_id),
                "demands_synced": synced,
                "timestamp": datetime.utcnow().isoformat(),
            })

        return {"synced": synced, "total": len(records)}

    async def sync_supply(self) -> dict:
        try:
            records = self.client.search_read(
                "purchase.order.line",
                [("state", "in", ["purchase", "done"])],
                fields=list(ODOO_TO_CDM_SUPPLY.keys()),
            )
        except Exception as e:
            logger.error("Odoo supply fetch failed: %s", e)
            return {"synced": 0, "error": str(e)}

        synced = 0
        for rec in records:
            mapped = map_odoo_to_cdm(rec, ODOO_TO_CDM_SUPPLY)
            mapped["tenant_id"] = self.tenant_id
            mapped["erp_source_type"] = "odoo"
            existing = await self.session.execute(
                select(SupplyOrder).where(
                    SupplyOrder.tenant_id == self.tenant_id,
                    SupplyOrder.erp_source_id == mapped["erp_source_id"],
                )
            )
            if existing.scalar_one_or_none():
                continue
            self.session.add(SupplyOrder(**mapped))
            synced += 1
        await self.session.commit()

        if synced > 0:
            await kafka_producer.send_event("supply", "updated", str(self.tenant_id), {
                "tenant_id": str(self.tenant_id),
                "supply_synced": synced,
                "timestamp": datetime.utcnow().isoformat(),
            })

        return {"synced": synced, "total": len(records)}

    async def sync_ai_schedule(self, mo_data: list[dict]) -> dict:
        """Write AI schedule suggestions to Odoo shadow fields.

        Args:
            mo_data: List of dicts with keys:
                erp_mo_id (int), ai_suggested_start (str), ai_suggested_end (str),
                ai_schedule_version (int), ai_rationale (str, optional).
        Returns:
            Dict with synced count and errors.
        """
        synced = 0
        errors = []
        for entry in mo_data:
            try:
                erp_id = int(entry["erp_mo_id"])
                values = {
                    "x_ai_suggested_start": entry.get("ai_suggested_start"),
                    "x_ai_suggested_end": entry.get("ai_suggested_end"),
                    "x_ai_schedule_version": entry.get("ai_schedule_version", 0),
                }
                if entry.get("ai_rationale"):
                    values["x_ai_rationale"] = entry["ai_rationale"]
                self.client.write("mrp.production", [erp_id], values)
                synced += 1
            except Exception as e:
                errors.append({"erp_mo_id": entry.get("erp_mo_id"), "error": str(e)})
        return {"synced": synced, "errors": errors}

    async def sync_all(self) -> dict:
        products = await self.sync_products()
        demands = await self.sync_demands()
        supply = await self.sync_supply()
        return {
            "products": products,
            "demands": demands,
            "supply": supply,
        }
