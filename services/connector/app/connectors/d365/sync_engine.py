"""D365 / Dataverse sync engine scaffold."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class D365SyncEngine:
    """Bidirectional sync scaffold for Dynamics 365 (Dataverse REST)."""

    def __init__(self, db_session: Any, tenant_id: str, config: Any) -> None:
        self.db = db_session
        self.tenant_id = tenant_id
        self.config = config

    async def sync_all(self) -> dict[str, Any]:
        return {
            "products": await self.sync_products(),
            "mos": await self.sync_manufacturing_orders(),
            "status": "skipped",
            "message": "D365 scaffold — credentials required",
        }

    async def sync_products(self) -> dict[str, Any]:
        logger.info("D365 product sync: SKIPPED (scaffold)")
        return {"synced": 0, "status": "skipped"}

    async def sync_manufacturing_orders(self) -> dict[str, Any]:
        logger.info("D365 MO sync: SKIPPED (scaffold)")
        return {"synced": 0, "status": "skipped"}

    async def activate(self, mo_ids: list[str], schedule_data: dict[str, Any]) -> dict[str, Any]:
        logger.info("D365 activate for %s MOs: SKIPPED (scaffold)", len(mo_ids))
        return {"activated": 0, "status": "skipped"}
