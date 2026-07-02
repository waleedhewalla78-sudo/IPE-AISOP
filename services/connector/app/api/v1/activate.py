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
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.tenant import Tenant
from ipe_shared.schemas.common import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync/odoo", tags=["sync-odoo"])


class ActivateRequest(BaseModel):
    mo_ids: list[UUID]
    odoo_url: str
    odoo_db: str
    odoo_username: str
    odoo_password: str
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

    try:
        client = OdooClient(req.odoo_url, req.odoo_db, req.odoo_username, req.odoo_password)
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
        try:
            erp_id = int(erp_mo_id)
        except ValueError:
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

        except Exception as e:
            error_str = str(e)
            if "UserError" in error_str or "reservation" in error_str.lower():
                reason = "MATERIAL_CONFLICT"
            else:
                reason = f"ODOO_ERROR: {error_str[:200]}"
            failed.append({"mo_id": str(mo_id), "reason": reason})
            logger.error("Failed to activate MO %s: %s", mo_id, error_str)

    await session.commit()

    return APIResponse(success=True, data={
        "activated": activated,
        "failed": failed,
        "total": len(req.mo_ids),
        "activated_count": len(activated),
        "failed_count": len(failed),
    }, error=None)
