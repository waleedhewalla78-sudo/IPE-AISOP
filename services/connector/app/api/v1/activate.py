import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.odoo.client import OdooClient
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.events.odoo_sync_monitor import odoo_sync_monitor
from ipe_shared.integrations.odoo_credentials import decrypt_odoo_password
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.tenant import Tenant
from ipe_shared.schemas.common import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync/odoo", tags=["sync-odoo"])


def _resolve_odoo_mo_id(client: OdooClient, erp_mo_id: str) -> int | None:
    try:
        return int(erp_mo_id)
    except ValueError:
        pass
    rows = client.execute(
        "mrp.production",
        "search_read",
        args=[[["name", "=", erp_mo_id]]],
        kwargs={"fields": ["id"], "limit": 1},
    )
    if rows:
        return int(rows[0]["id"])
    return None


class ActivateRequest(BaseModel):
    mo_ids: list[UUID]
    odoo_url: str | None = None
    odoo_db: str | None = None
    odoo_username: str | None = None
    odoo_password: str | None = None
    approved_by: str = "system"


@router.post("/activate")
async def activate_schedule(
    req: ActivateRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    tid = UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id

    if not req.mo_ids:
        return APIResponse(success=True, data={
            "activated": [], "failed": [],
            "total": 0, "activated_count": 0, "failed_count": 0,
        }, error=None)

    result = await session.execute(select(Tenant).where(Tenant.id == tid))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "Tenant not found"},
        )

    cfg = tenant.config or {}
    odoo_url = req.odoo_url or tenant.erp_base_url or cfg.get("odoo_url")
    odoo_db = req.odoo_db or cfg.get("odoo_db")
    odoo_username = req.odoo_username or cfg.get("odoo_username")
    odoo_password = req.odoo_password or decrypt_odoo_password(cfg)
    if not all([odoo_url, odoo_db, odoo_username, odoo_password]):
        return APIResponse(
            success=False, data=None,
            error={"code": "ODOO_CREDS", "message": "Configure tenant Odoo creds or pass request body"},
        )

    try:
        client = OdooClient(odoo_url, odoo_db, odoo_username, odoo_password)
        client.authenticate()
    except Exception as e:
        return APIResponse(
            success=False, data=None,
            error={"code": "ODOO_CONNECT_FAILED", "message": str(e)},
        )

    activated = []
    failed = []

    for mo_id in req.mo_ids:
        result = await session.execute(
            select(ManufacturingOrder).where(
                ManufacturingOrder.id == mo_id,
                ManufacturingOrder.tenant_id == tid,
            )
        )
        mo = result.scalar_one_or_none()
        if not mo:
            failed.append({"mo_id": str(mo_id), "reason": "NOT_FOUND"})
            continue

        if not mo.ai_suggested_start or not mo.ai_suggested_end:
            failed.append({"mo_id": str(mo_id), "reason": "NO_AI_SUGGESTION"})
            continue

        if not mo.erp_mo_id:
            failed.append({"mo_id": str(mo_id), "reason": "NO_ERP_MO_ID"})
            continue

        erp_mo_id = mo.erp_mo_id
        erp_id = _resolve_odoo_mo_id(client, erp_mo_id)
        if erp_id is None:
            failed.append({"mo_id": str(mo_id), "reason": "INVALID_ERP_MO_ID"})
            continue

        try:
            odoo_result = client.execute(
                "mrp.production", "search_read",
                args=[[["id", "=", erp_id]]],
                kwargs={"fields": ["id", "date_start", "date_finished", "write_date"]},
            )
            if not odoo_result:
                failed.append({"mo_id": str(mo_id), "reason": "ERP_MO_NOT_FOUND"})
                continue

            odoo_mo = odoo_result[0]

            new_start = mo.ai_suggested_start.strftime("%Y-%m-%d %H:%M:%S")
            new_end = mo.ai_suggested_end.strftime("%Y-%m-%d %H:%M:%S")

            write_vals = {"date_start": new_start, "date_finished": new_end}
            try:
                client.write("mrp.production", [erp_id], write_vals)
            except Exception:
                client.write("mrp.production", [erp_id], {
                    "date_planned_start": new_start,
                    "date_planned_finished": new_end,
                })

            try:
                client.execute("mrp.production", "button_unreserve", args=[[erp_id]])
                client.execute("mrp.production", "button_plan", args=[[erp_id]])
            except Exception:
                logger.warning("Reservation handling failed for MO %s (non-critical)", erp_mo_id)

            try:
                client.execute(
                    "mrp.production", "message_post",
                    args=[[erp_id]],
                    kwargs={
                        "body": (
                            f"Schedule updated by IPE AI — approved by {req.approved_by}.\n"
                            f"New planned start: {new_start}\n"
                            f"New planned end: {new_end}\n"
                            f"AI schedule version: {mo.ai_schedule_version or 0}"
                        ),
                    },
                )
            except Exception:
                logger.warning("Chatter post failed for MO %s (non-critical)", erp_mo_id)

            mo.planned_start = mo.ai_suggested_start
            mo.planned_end = mo.ai_suggested_end
            mo.ai_suggested_start = None
            mo.ai_suggested_end = None
            mo.ai_schedule_version = (mo.ai_schedule_version or 0) + 1
            session.add(mo)

            activated.append({
                "mo_id": str(mo_id),
                "erp_mo_id": erp_mo_id,
                "new_planned_start": new_start,
                "new_planned_end": new_end,
            })
            odoo_sync_monitor.record_sync("ipe_to_odoo", "schedule_activate", erp_mo_id, True)

        except Exception as e:
            error_str = str(e)
            if "UserError" in error_str or "reservation" in error_str.lower():
                reason = "MATERIAL_CONFLICT"
            else:
                reason = f"ODOO_ERROR: {error_str[:200]}"
            failed.append({"mo_id": str(mo_id), "reason": reason})
            odoo_sync_monitor.record_sync(
                "ipe_to_odoo",
                "schedule_activate",
                erp_mo_id if "erp_mo_id" in locals() else str(mo_id),
                False,
            )
            logger.error("Failed to activate MO %s: %s", mo_id, error_str)

    await session.commit()

    return APIResponse(success=True, data={
        "activated": activated,
        "failed": failed,
        "total": len(req.mo_ids),
        "activated_count": len(activated),
        "failed_count": len(failed),
    }, error=None)
