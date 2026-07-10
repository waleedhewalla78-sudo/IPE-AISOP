"""Planning intelligence safety stock API."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.safety_stock_service import SafetyStockService
from app.schemas.safety_stock_api import SafetyStockCalculateRequest
from ipe_shared.auth.rbac import require_roles
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/material/safety-stock", tags=["material-safety-stock"])


def _no_tenant_response() -> APIResponse:
    return APIResponse(
        success=False,
        data=None,
        error={"code": "NO_TENANT", "message": "No tenant context"},
    )


@router.post("/calculate")
async def calculate_safety_stock(
    req: SafetyStockCalculateRequest,
    current_user=Depends(require_roles(["admin", "planner", "manager"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return _no_tenant_response()

    result = await SafetyStockService().calculate_all(
        db=session,
        tenant_id=UUID(tenant_id),
        product_id=req.product_id,
        service_level_pct=req.service_level_pct,
        period_days=req.period_days,
        history_days=req.history_days,
    )
    return APIResponse(success=True, data=result, error=None)


@router.get("/results")
async def get_safety_stock_results(
    product_id: UUID | None = Query(default=None),
    current_user=Depends(require_roles(["admin", "planner", "manager", "auditor"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return _no_tenant_response()

    result = await SafetyStockService().latest_results(session, UUID(tenant_id), product_id)
    return APIResponse(success=True, data=result, error=None)


@router.get("/summary")
async def get_safety_stock_summary(
    current_user=Depends(require_roles(["admin", "planner", "manager", "auditor"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return _no_tenant_response()

    result = await SafetyStockService().summary(session, UUID(tenant_id))
    return APIResponse(success=True, data=result, error=None)


@router.get("/lead-time")
async def get_lead_time_summary(
    product_id: UUID | None = Query(default=None),
    current_user=Depends(require_roles(["admin", "planner", "manager", "auditor"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return _no_tenant_response()

    result = await SafetyStockService().lead_time_summary(session, UUID(tenant_id), product_id)
    return APIResponse(success=True, data=result, error=None)
