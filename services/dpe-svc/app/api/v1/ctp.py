# services/dpe-svc/app/api/v1/ctp.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, conint
from datetime import datetime, date, timedelta
from typing import Literal, Optional

from app.core.ctp import evaluate_ctp
from ipe_shared.auth.rbac import require_roles
from ipe_shared.middleware.tenant_context import tenant_ctx

router = APIRouter(prefix="/ctp", tags=["CTP"])

class CtpRequest(BaseModel):
    so_id: conint(gt=0)                     # Odoo Sale Order ID
    product_id: conint(gt=0)
    requested_qty: conint(gt=0)
    requested_delivery_date: datetime
    customer_priority: Literal["high", "medium", "low"] = "medium"

class CtpResponse(BaseModel):
    is_feasible: bool
    earliest_feasible_date: Optional[datetime] = None
    confidence_score: int = Field(..., ge=0, le=100)
    binding_constraint: Optional[str] = None
    constraint_resource: Optional[str] = None

@router.post(
    "/evaluate",
    response_model=CtpResponse,
    summary="Fast CTP evaluation (<2 s)"
)
async def ctp_evaluate(
    payload: CtpRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")
    try:
        result = await evaluate_ctp(payload, str(tenant_id))
        return CtpResponse(
            is_feasible=result.is_feasible,
            earliest_feasible_date=result.earliest_feasible_date,
            confidence_score=int(result.confidence_score * 100),
            binding_constraint=result.binding_constraint,
            constraint_resource=result.constraint_resource,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
