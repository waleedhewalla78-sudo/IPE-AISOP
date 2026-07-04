"""SAP S/4HANA sync engine scaffold — mirrors Odoo pattern; no live credentials."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SAPSyncEngine:
    """Bidirectional sync scaffold for SAP S/4HANA (OData)."""

    def __init__(self, db_session: Any, tenant_id: str, config: Any) -> None:
        self.db = db_session
        self.tenant_id = tenant_id
        self.config = config

    async def sync_all(self) -> dict[str, Any]:
        results: dict[str, Any] = {
            "products": await self.sync_products(),
            "work_centers": await self.sync_work_centers(),
            "boms": await self.sync_boms(),
            "mos": await self.sync_manufacturing_orders(),
            "status": "skipped",
            "message": "SAP scaffold — credentials required",
        }
        return results

    async def sync_products(self) -> dict[str, Any]:
        logger.info("SAP product sync: SKIPPED (scaffold)")
        return {"synced": 0, "status": "skipped"}

    async def sync_work_centers(self) -> dict[str, Any]:
        logger.info("SAP work center sync: SKIPPED (scaffold)")
        return {"synced": 0, "status": "skipped"}

    async def sync_boms(self) -> dict[str, Any]:
        logger.info("SAP BOM sync: SKIPPED (scaffold)")
        return {"synced": 0, "status": "skipped"}

    async def sync_manufacturing_orders(self) -> dict[str, Any]:
        logger.info("SAP MO sync: SKIPPED (scaffold)")
        return {"synced": 0, "status": "skipped"}

    async def activate(self, mo_ids: list[str], schedule_data: dict[str, Any]) -> dict[str, Any]:
        logger.info("SAP activate for %s MOs: SKIPPED (scaffold)", len(mo_ids))
        return {"activated": 0, "status": "skipped"}
