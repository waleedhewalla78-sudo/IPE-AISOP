"""Direct Odoo activate for Release 1 (no Kafka)."""

from __future__ import annotations

import logging
import os
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.models.tenant import Tenant
from ipe_shared.integrations.odoo_credentials import decrypt_odoo_password

logger = logging.getLogger(__name__)

CONNECTOR_BASE = os.getenv("CONNECTOR_SVC_URL", "http://connector:8009")


async def activate_mos_in_odoo(
    session: AsyncSession,
    tenant_id: UUID,
    mo_ids: list[UUID],
    *,
    approved_by: str = "planner",
    auth_header: str | None = None,
) -> dict:
    """Call connector activate endpoint directly when ERP_SYNC_MODE=direct."""
    if os.getenv("ERP_SYNC_MODE", "kafka").lower() != "direct":
        return {"skipped": True, "reason": "kafka_mode"}

    result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return {"success": False, "error": "tenant_not_found"}

    cfg = tenant.config or {}
    url = tenant.erp_base_url or cfg.get("odoo_url")
    db = cfg.get("odoo_db")
    user = cfg.get("odoo_username")
    password = decrypt_odoo_password(cfg)
    if not all([url, db, user, password]):
        return {"success": False, "error": "odoo_creds_missing"}

    payload = {
        "mo_ids": [str(m) for m in mo_ids],
        "odoo_url": url,
        "odoo_db": db,
        "odoo_username": user,
        "odoo_password": password,
        "approved_by": approved_by,
    }
    headers = {"Content-Type": "application/json", "X-Tenant-ID": str(tenant_id)}
    if auth_header:
        headers["Authorization"] = auth_header

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{CONNECTOR_BASE.rstrip('/')}/api/v1/sync/odoo/activate",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            body = resp.json()
            return {"success": body.get("success", True), "data": body.get("data")}
    except Exception as exc:
        logger.exception("Direct Odoo activate failed")
        return {"success": False, "error": str(exc)}
