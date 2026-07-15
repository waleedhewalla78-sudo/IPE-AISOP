"""Phase 3 demand signal fusion API."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.core.signal_fusion import DemandSignalFusion
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/demand", tags=["demand-phase3"])
_fusion = DemandSignalFusion()


class SignalFusionRequest(BaseModel):
    product_id: str = "FG-DT100"
    horizon_days: int = 28
    statistical_qty: float = 20
    statistical_confidence: float = 0.75
    open_orders_qty: float = 0
    crm_pipeline_qty: float = 0
    customer_pattern_qty: float = 0
    customer_pattern_confidence: float = 0.6
    seasonal_factor: float = 1.0
    seasonal_description: str = "no seasonal adjustment"


def _tenant(x_tenant_id: str | None = None) -> str:
    return str(tenant_ctx.get() or x_tenant_id or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


@router.post("/signal-fusion")
async def signal_fusion(
    req: SignalFusionRequest | None = None,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    req = req or SignalFusionRequest()
    inputs = req.model_dump()
    product_id = inputs.pop("product_id")
    horizon = inputs.pop("horizon_days")
    data = await _fusion.fuse_signals(None, _tenant(x_tenant_id), product_id, horizon, inputs)
    return APIResponse(success=True, data=data, error=None)


@router.get("/signal-fusion/{product_id}")
async def signal_fusion_get(
    product_id: str,
    horizon_days: int = 28,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    data = await _fusion.fuse_signals(None, _tenant(x_tenant_id), product_id, horizon_days)
    return APIResponse(success=True, data=data, error=None)
