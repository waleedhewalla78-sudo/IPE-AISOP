from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ipe_shared.schemas.common import APIResponse
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.models.tenant import Tenant
from sqlalchemy import select

from app.odoo.client import OdooClient
from app.odoo.sync import SyncAdapter

router = APIRouter(prefix="/sync", tags=["sync"])


class SyncRequest(BaseModel):
    odoo_url: str
    odoo_db: str
    odoo_username: str
    odoo_password: str
    entity: str = "all"


@router.post("/run")
async def run_sync(
    req: SyncRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    result = await session.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "Tenant not found"},
        )

    try:
        client = OdooClient(req.odoo_url, req.odoo_db, req.odoo_username, req.odoo_password)
        client.authenticate()
    except Exception as e:
        return APIResponse(
            success=False, data=None,
            error={"code": "ODOO_CONNECT_FAILED", "message": str(e)},
        )

    adapter = SyncAdapter(client, tenant_id, session)

    try:
        if req.entity == "products":
            data = {"products": await adapter.sync_products()}
        elif req.entity == "demands":
            data = {"demands": await adapter.sync_demands()}
        elif req.entity == "supply":
            data = {"supply": await adapter.sync_supply()}
        else:
            data = await adapter.sync_all()
    except Exception as e:
        return APIResponse(
            success=False, data=None,
            error={"code": "SYNC_FAILED", "message": str(e)},
        )

    return APIResponse(success=True, data=data, error=None)
