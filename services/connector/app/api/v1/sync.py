import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.models.tenant import Tenant
from ipe_shared.integrations.odoo_credentials import decrypt_odoo_password
from ipe_shared.events.odoo_sync_monitor import odoo_sync_monitor
from ipe_shared.schemas.common import APIResponse

from app.odoo.client import OdooClient
from app.odoo.sync_engine import OdooSyncEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["sync"])


class SyncRequest(BaseModel):
    odoo_url: str | None = None
    odoo_db: str | None = None
    odoo_username: str | None = None
    odoo_password: str | None = None
    entity: str = "all"


def _odoo_creds_from_tenant(tenant: Tenant, req: SyncRequest) -> tuple[str, str, str, str]:
    cfg = tenant.config or {}
    url = req.odoo_url or tenant.erp_base_url or cfg.get("odoo_url")
    db = req.odoo_db or cfg.get("odoo_db")
    user = req.odoo_username or cfg.get("odoo_username")
    password = req.odoo_password or decrypt_odoo_password(cfg)
    if not all([url, db, user, password]):
        raise ValueError("Odoo credentials incomplete — set tenant.config or request body")
    return url, db, user, password


@router.post("/run")
async def run_sync(
    req: SyncRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
    result = await session.execute(select(Tenant).where(Tenant.id == tid))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Tenant not found"})

    try:
        url, db, user, password = _odoo_creds_from_tenant(tenant, req)
        client = OdooClient(url, db, user, password)
        client.authenticate()
    except Exception as e:
        return APIResponse(success=False, data=None, error={"code": "ODOO_CONNECT_FAILED", "message": str(e)})

    engine = OdooSyncEngine(client, tid, session)
    try:
        if req.entity == "products":
            data = {"products": await engine.sync_products()}
        elif req.entity == "work_centers":
            data = {"work_centers": await engine.sync_work_centers()}
        elif req.entity == "boms":
            data = {"boms": await engine.sync_boms(), "bom_details": await engine.sync_bom_details()}
        elif req.entity == "bom_details":
            data = {"bom_details": await engine.sync_bom_details()}
        elif req.entity == "customers":
            data = {"customers": await engine.sync_customers()}
        elif req.entity == "suppliers":
            data = {"suppliers": await engine.sync_suppliers()}
        elif req.entity == "manufacturing_orders":
            data = {"manufacturing_orders": await engine.sync_manufacturing_orders()}
        elif req.entity == "demands":
            data = {"demands": await engine.sync_demands()}
        elif req.entity == "supply":
            data = {"supply": await engine.sync_supply()}
        elif req.entity == "inventory":
            data = {"inventory": await engine.sync_inventory()}
        else:
            data = await engine.run_full_sync(trigger="manual")
    except Exception as e:
        logger.exception("Sync failed")
        return APIResponse(success=False, data=None, error={"code": "SYNC_FAILED", "message": str(e)})

    return APIResponse(success=True, data=data, error=None)


@router.get("/status")
async def sync_status(session: AsyncSession = Depends(get_db_session)):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
    row = await session.execute(
        text("""
            SELECT id, started_at, finished_at, status, entity_counts, error_summary
            FROM cdm_sync_run
            WHERE tenant_id = :tid
            ORDER BY started_at DESC
            LIMIT 1
        """),
        {"tid": tid},
    )
    last = row.fetchone()
    if not last:
        return APIResponse(
            success=True,
            data={
                "last_sync": None,
                "next_sync_estimate_minutes": 15,
                "monitor": odoo_sync_monitor.get_sync_status(),
            },
            error=None,
        )

    return APIResponse(
        success=True,
        data={
            "last_sync": {
                "id": str(last[0]),
                "started_at": last[1].isoformat() if last[1] else None,
                "finished_at": last[2].isoformat() if last[2] else None,
                "status": last[3],
                "entity_counts": last[4],
                "error_summary": last[5],
            },
            "next_sync_estimate_minutes": 15,
            "monitor": odoo_sync_monitor.get_sync_status(),
        },
        error=None,
    )


@router.get("/data-quality")
async def sync_data_quality(session: AsyncSession = Depends(get_db_session)):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
    rows = await session.execute(
        text("""
            SELECT f.mo_id, mo.erp_mo_id, f.flag_code, f.message, f.created_at
            FROM cdm_data_quality_flag f
            JOIN cdm_manufacturing_order mo ON mo.id = f.mo_id
            WHERE f.tenant_id = :tid AND f.resolved_at IS NULL
            ORDER BY f.created_at DESC
            LIMIT 100
        """),
        {"tid": tid},
    )
    flags = [
        {
            "mo_id": str(r[0]),
            "erp_mo_id": r[1],
            "flag_code": r[2],
            "message": r[3],
            "created_at": r[4].isoformat() if r[4] else None,
        }
        for r in rows.fetchall()
    ]
    return APIResponse(success=True, data={"flags": flags, "count": len(flags)}, error=None)
