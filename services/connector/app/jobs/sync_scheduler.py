"""Background scheduled Odoo sync for Release 1."""

from __future__ import annotations

import asyncio
import logging
import os
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from ipe_shared.database.connection import get_engine
from ipe_shared.models.tenant import Tenant
from ipe_shared.integrations.odoo_credentials import decrypt_odoo_password

from app.odoo.client import OdooClient
from app.odoo.sync_engine import OdooSyncEngine

logger = logging.getLogger(__name__)

SYNC_INTERVAL_SEC = int(os.getenv("ODOO_SYNC_INTERVAL_SEC", "900"))
_scheduler_task: asyncio.Task | None = None


async def _run_tenant_sync(tenant: Tenant) -> None:
    cfg = tenant.config or {}
    url = tenant.erp_base_url or cfg.get("odoo_url")
    db = cfg.get("odoo_db")
    user = cfg.get("odoo_username")
    password = decrypt_odoo_password(cfg)
    if not all([url, db, user, password]):
        logger.debug("Skipping tenant %s — Odoo creds not configured", tenant.id)
        return

    engine_db = get_engine()
    factory = async_sessionmaker(engine_db, expire_on_commit=False)
    async with factory() as session:
        try:
            client = OdooClient(url, db, user, password)
            client.authenticate()
            sync = OdooSyncEngine(client, UUID(str(tenant.id)), session)
            result = await sync.run_full_sync(trigger="scheduled")
            logger.info("Scheduled sync tenant %s: %s", tenant.id, result.get("status"))
        except Exception:
            logger.exception("Scheduled sync failed for tenant %s", tenant.id)


async def _scheduler_loop() -> None:
    while True:
        try:
            engine_db = get_engine()
            factory = async_sessionmaker(engine_db, expire_on_commit=False)
            async with factory() as session:
                result = await session.execute(
                    select(Tenant).where(Tenant.is_active.is_(True), Tenant.erp_type == "odoo")
                )
                for tenant in result.scalars().all():
                    await _run_tenant_sync(tenant)
        except Exception:
            logger.exception("Scheduler loop error")
        await asyncio.sleep(SYNC_INTERVAL_SEC)


def start_sync_scheduler() -> None:
    global _scheduler_task
    if os.getenv("IPE_RELEASE_PROFILE") != "release1":
        return
    if os.getenv("ODOO_SYNC_SCHEDULER", "true").lower() != "true":
        return
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_scheduler_loop())
        logger.info("Odoo sync scheduler started (interval=%ss)", SYNC_INTERVAL_SEC)


async def stop_sync_scheduler() -> None:
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None
