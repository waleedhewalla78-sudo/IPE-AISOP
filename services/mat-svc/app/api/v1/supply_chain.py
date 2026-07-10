"""Supply chain intelligence API (Sprint S10)."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.supply_chain_intel import (
    compute_inventory_abc,
    compute_reorder_suggestions,
    compute_slow_moving,
    compute_supplier_risk,
)
from ipe_shared.auth.rbac import require_roles
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.supplier_score import SupplierScore
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/supply-chain", tags=["supply-chain"])


@router.get("/supplier-risk")
async def supplier_risk(
    persist: bool = Query(False, description="Write scores to cdm_supplier_score"),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles(["admin", "planner", "manager", "procurement"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)
    suppliers = await compute_supplier_risk(session, tid)

    if persist:
        for row in suppliers:
            session.add(
                SupplierScore(
                    id=uuid4(),
                    tenant_id=tid,
                    supplier_id=UUID(row["supplier_id"]),
                    reliability_score=row["reliability_score"],
                    risk_tier=row["risk_tier"],
                    avg_delay_days=row["avg_delay_days"],
                    sample_size=row["sample_size"],
                    contributing_factors=row["contributing_factors"],
                )
            )
        await session.commit()

    high_risk = [s for s in suppliers if s["risk_tier"] == "high"]
    return APIResponse(
        success=True,
        data={
            "supplier_count": len(suppliers),
            "high_risk_count": len(high_risk),
            "suppliers": suppliers,
        },
        error=None,
    )


@router.get("/inventory-abc")
async def inventory_abc(
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles(["admin", "planner", "manager", "procurement"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    result = await compute_inventory_abc(session, UUID(tenant_id))
    return APIResponse(success=True, data=result, error=None)


@router.get("/slow-moving")
async def slow_moving_inventory(
    stale_days: int = Query(90, ge=30, le=365),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles(["admin", "planner", "manager", "procurement"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    items = await compute_slow_moving(session, UUID(tenant_id), stale_days=stale_days)
    return APIResponse(
        success=True,
        data={"stale_days": stale_days, "count": len(items), "items": items},
        error=None,
    )


@router.get("/reorder-suggestions")
async def reorder_suggestions(
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_roles(["admin", "planner", "manager", "procurement"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    suggestions = await compute_reorder_suggestions(session, UUID(tenant_id))
    return APIResponse(
        success=True,
        data={"count": len(suggestions), "suggestions": suggestions},
        error=None,
    )
