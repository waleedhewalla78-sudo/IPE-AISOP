"""Odoo ERP routes — REST adapter + legacy XML-RPC sync."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.feature_flags.flags import get_feature_flags
from ipe_shared.events.odoo_sync_monitor import odoo_sync_monitor
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.integrations.odoo_credentials import decrypt_odoo_password
from ipe_shared.schemas.common import APIResponse

from app.erp.odoo_adapter import OdooAdapter
from app.odoo.client import OdooClient
from app.odoo.sync_engine import OdooSyncEngine
from ipe_shared.models.tenant import Tenant
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/erp/odoo", tags=["erp-odoo"])


class OdooSyncAllRequest(BaseModel):
    mode: str = "xmlrpc"  # xmlrpc (CDM upsert) | rest (adapter pull only)


@router.get("/health")
async def odoo_health():
    adapter = OdooAdapter()
    try:
        data = await adapter.health_check()
        return APIResponse(success=True, data=data, error=None)
    except Exception as e:
        return APIResponse(success=False, data=None, error={"code": "ODOO_HEALTH_FAILED", "message": str(e)})


@router.get("/pull/{domain}")
async def odoo_pull(domain: str, limit: int = 100):
    adapter = OdooAdapter()
    try:
        method = {
            "sales_orders": adapter.pull_sales_orders,
            "stock_levels": adapter.pull_stock_levels,
            "products": adapter.pull_products,
            "bom": adapter.pull_boms,
            "production_orders": adapter.pull_production_orders,
            "purchase_orders": adapter.pull_purchase_orders,
            "suppliers": adapter.pull_suppliers,
            "locations": adapter.pull_locations,
            "cost_data": adapter.pull_cost_data,
        }.get(domain)
        if not method:
            return APIResponse(success=False, data=None, error={"code": "UNKNOWN_DOMAIN", "message": domain})
        data = await method(limit=limit)
        return APIResponse(success=True, data={"domain": domain, "count": len(data), "records": data}, error=None)
    except Exception as e:
        logger.exception("Odoo pull failed")
        return APIResponse(success=False, data=None, error={"code": "PULL_FAILED", "message": str(e)})


@router.post("/sync/all")
async def odoo_sync_all(
    req: OdooSyncAllRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
):
    """Full sync: xmlrpc → CDM (Release 1) or rest pull preview."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    if req.mode == "rest":
        adapter = OdooAdapter()
        try:
            results = {
                "products": len(await adapter.pull_products()),
                "suppliers": len(await adapter.pull_suppliers()),
                "boms": len(await adapter.pull_boms()),
                "production_orders": len(await adapter.pull_production_orders()),
                "sales_orders": len(await adapter.pull_sales_orders()),
                "purchase_orders": len(await adapter.pull_purchase_orders()),
                "stock_levels": len(await adapter.pull_stock_levels()),
            }
            return APIResponse(success=True, data={"mode": "rest", "counts": results}, error=None)
        except Exception as e:
            return APIResponse(success=False, data=None, error={"code": "REST_SYNC_FAILED", "message": str(e)})

    from uuid import UUID

    tid = UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
    result = await session.execute(select(Tenant).where(Tenant.id == tid))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Tenant not found"})

    cfg = tenant.config or {}
    url = tenant.erp_base_url or cfg.get("odoo_url")
    db = cfg.get("odoo_db")
    user = cfg.get("odoo_username")
    password = decrypt_odoo_password(cfg)
    if not all([url, db, user, password]):
        return APIResponse(success=False, data=None, error={"code": "ODOO_CREDS", "message": "Configure tenant Odoo creds"})

    try:
        client = OdooClient(url, db, user, password)
        client.authenticate()
        engine = OdooSyncEngine(client, tid, session)
        data = await engine.run_full_sync(trigger="api")
        return APIResponse(success=True, data=data, error=None)
    except Exception as e:
        logger.exception("XML-RPC sync failed")
        return APIResponse(success=False, data=None, error={"code": "SYNC_FAILED", "message": str(e)})


class ResolutionNotifyRequest(BaseModel):
    mo_id: str
    erp_mo_id: str | None = None
    scenario_id: str
    strategy: str
    approved_by: str
    comment: str | None = None
    delivery_impact_days: float | None = None
    cost_impact: float | None = None


def _resolution_writeback_enabled(tenant: Tenant | None) -> bool:
    if os.getenv("ODOO_RESOLUTION_WRITEBACK_ENABLED", "false").lower() in ("1", "true", "yes"):
        return True
    if get_feature_flags().is_enabled("ipe.odoo.resolution_writeback"):
        return True
    if tenant and (tenant.config or {}).get("odoo_resolution_writeback_enabled"):
        return True
    return False


@router.post("/resolution-notify")
async def resolution_notify(
    req: ResolutionNotifyRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Post IPE resolution approval to Odoo (chatter on MO; draft PO for expedite_po when configured)."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    from uuid import UUID

    tid = UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
    tenant = (await session.execute(select(Tenant).where(Tenant.id == tid))).scalar_one_or_none()
    if not _resolution_writeback_enabled(tenant):
        return APIResponse(
            success=True,
            data={"skipped": True, "reason": "odoo_resolution_writeback_enabled is false"},
            error=None,
        )

    erp_mo_id = req.erp_mo_id
    if not erp_mo_id:
        return APIResponse(success=False, data=None, error={"code": "NO_ERP_MO", "message": "erp_mo_id required"})

    body_lines = [
        f"<p><b>IPE resolution approved</b> — strategy <code>{req.strategy}</code></p>",
        f"<p>Scenario: {req.scenario_id}<br/>Approved by: {req.approved_by}</p>",
    ]
    if req.comment:
        body_lines.append(f"<p>{req.comment}</p>")
    if req.delivery_impact_days is not None:
        body_lines.append(f"<p>Delivery impact: {req.delivery_impact_days:.1f} days</p>")
    if req.cost_impact is not None:
        body_lines.append(f"<p>Cost impact: {req.cost_impact:.2f}</p>")

    adapter = OdooAdapter()
    try:
        chatter = await adapter.push_resolution_notify({
            "erp_mo_id": erp_mo_id,
            "body": "".join(body_lines),
            "subject": f"IPE Resolution — {req.strategy}",
        })
        po_result = None
        if req.strategy == "expedite_po":
            po_result = await adapter.push_procurement_recommendation({
                "plan_id": req.scenario_id[:8],
                "supplier_id": (tenant.config or {}).get("default_supplier_id") if tenant else None,
                "lines": [],
            })
        odoo_sync_monitor.record_sync("ipe_to_odoo", "resolution_notify", erp_mo_id, True)
        return APIResponse(
            success=True,
            data={"chatter": chatter, "draft_po": po_result, "erp_mo_id": erp_mo_id},
            error=None,
        )
    except Exception as e:
        logger.exception("Resolution notify failed")
        odoo_sync_monitor.record_sync("ipe_to_odoo", "resolution_notify", erp_mo_id, False)
        return APIResponse(success=False, data=None, error={"code": "RESOLUTION_NOTIFY_FAILED", "message": str(e)})

