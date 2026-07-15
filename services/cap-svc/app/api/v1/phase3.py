"""Phase 3 capacity endpoints — smart batching + capacity auction."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.core.capacity_auction import CapacityAuction
from app.core.smart_batcher import SmartBatcher
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/capacity", tags=["capacity-phase3"])
_batcher = SmartBatcher()
_auction = CapacityAuction()


class BatchOptimizeRequest(BaseModel):
    mos: list[dict[str, Any]] = Field(default_factory=list)
    work_centres: list[dict[str, Any]] = Field(default_factory=list)


class AuctionRequest(BaseModel):
    competing_mos: list[dict[str, Any]]
    slot: dict[str, Any] = Field(default_factory=dict)


def _tenant(x_tenant_id: str | None = None) -> str:
    return str(tenant_ctx.get() or x_tenant_id or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


@router.post("/batch/optimize")
async def batch_optimize(
    req: BatchOptimizeRequest | None = None,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    req = req or BatchOptimizeRequest()
    mos = req.mos or [
        {
            "id": "mo-1",
            "product_id": "DT100",
            "product_family": "DT",
            "planned_start": "2026-07-15",
            "planned_end": "2026-07-18",
            "work_centre_id": "wc-1",
        },
        {
            "id": "mo-2",
            "product_id": "DT250",
            "product_family": "DT",
            "planned_start": "2026-07-16",
            "planned_end": "2026-07-19",
            "work_centre_id": "wc-1",
        },
        {
            "id": "mo-3",
            "product_id": "DT100",
            "product_family": "DT",
            "planned_start": "2026-07-17",
            "planned_end": "2026-07-20",
            "work_centre_id": "wc-1",
        },
        {
            "id": "mo-4",
            "product_id": "PT500",
            "product_family": "PT",
            "planned_start": "2026-07-15",
            "planned_end": "2026-07-22",
            "work_centre_id": "wc-1",
        },
    ]
    wcs = req.work_centres or [{"id": "wc-1", "name": "Winding"}]
    batches = await _batcher.optimize_batches(None, _tenant(x_tenant_id), mos, wcs)
    return APIResponse(
        success=True,
        data={"batches": batches, "items_processed": len(mos)},
        error=None,
    )


@router.post("/auction/resolve")
async def auction_resolve(
    req: AuctionRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    result = await _auction.resolve_conflict(
        None, _tenant(x_tenant_id), req.competing_mos, req.slot or {"duration_days": 1}
    )
    return APIResponse(success=True, data=result, error=None)
