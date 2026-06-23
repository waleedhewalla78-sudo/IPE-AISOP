from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.tenant import Tenant
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/admin", tags=["admin"])


class ConfigUpdate(BaseModel):
    priority_weights: dict[str, float] | None = None
    strategic_product_ids: list[str] | None = None
    feasibility_thresholds: dict[str, float] | None = None
    autonomy_mode: str | None = None


@router.put("/config")
async def update_config(
    req: ConfigUpdate,
    current_user=Depends(require_roles(["admin"])),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    result = await session.execute(
        sa_select(Tenant).where(Tenant.id == UUID(tenant_id))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "Tenant not found"},
        )

    current_config = dict(tenant.config or {})

    if req.priority_weights is not None:
        priority_config = current_config.get("priority_weights", {})
        priority_config.update(req.priority_weights)
        current_config["priority_weights"] = priority_config

    if req.strategic_product_ids is not None:
        current_config["strategic_product_ids"] = req.strategic_product_ids

    if req.feasibility_thresholds is not None:
        thresholds = current_config.get("feasibility_thresholds", {})
        thresholds.update(req.feasibility_thresholds)
        current_config["feasibility_thresholds"] = thresholds

    tenant.config = current_config

    if req.autonomy_mode is not None:
        tenant.autonomy_mode = req.autonomy_mode

    await session.commit()

    return APIResponse(
        success=True,
        data={
            "config": current_config,
            "autonomy_mode": tenant.autonomy_mode,
        },
        error=None,
    )


@router.get("/config")
async def get_config(
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    result = await session.execute(
        sa_select(Tenant).where(Tenant.id == UUID(tenant_id))
    )
    tenant = result.scalar_one_or_none()
    if not tenant:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "Tenant not found"},
        )

    return APIResponse(
        success=True,
        data={
            "config": tenant.config or {},
            "autonomy_mode": tenant.autonomy_mode,
        },
        error=None,
    )


@router.get("/data-quality")
async def get_data_quality(
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    tid = UUID(tenant_id)

    total_boms_query = await session.execute(
        text("SELECT COUNT(*) FROM cdm_bill_of_material WHERE tenant_id = :tid"),
        {"tid": tid},
    )
    total_boms = total_boms_query.scalar() or 0

    complete_boms_query = await session.execute(
        text("""
            SELECT COUNT(*) FROM cdm_bill_of_material b
            WHERE b.tenant_id = :tid
            AND EXISTS (
                SELECT 1 FROM cdm_bom_line bl
                WHERE bl.bom_id = b.id
            )
        """),
        {"tid": tid},
    )
    complete_boms = complete_boms_query.scalar() or 0
    bom_completeness_pct = round(
        (complete_boms / total_boms) * 100, 1
    ) if total_boms > 0 else 100.0

    wo_query = await session.execute(
        text("""
            SELECT COUNT(*),
                   COUNT(*) FILTER (
                       WHERE duration_actual_mins IS NOT NULL
                       AND ABS(duration_actual_mins - duration_planned_mins)
                       / NULLIF(duration_planned_mins, 0) <= 0.15
                   ) AS accurate_count
            FROM cdm_work_order
            WHERE tenant_id = :tid
        """),
        {"tid": tid},
    )
    wo_row = wo_query.one()
    total_wos = wo_row[0] or 0
    accurate_wos = wo_row[1] or 0
    lead_time_accuracy_pct = round(
        (accurate_wos / total_wos) * 100, 1
    ) if total_wos > 0 else 100.0

    inv_query = await session.execute(
        text("""
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (
                       WHERE safety_stock IS NOT NULL AND safety_stock > 0
                   ) AS with_stock
            FROM cdm_product
            WHERE tenant_id = :tid AND source_type = 'manufactured'
        """),
        {"tid": tid},
    )
    inv_row = inv_query.one()
    total_products = inv_row[0] or 0
    products_with_stock = inv_row[1] or 0
    inventory_record_accuracy_pct = round(
        (products_with_stock / total_products) * 100, 1
    ) if total_products > 0 else 100.0

    return APIResponse(
        success=True,
        data={
            "bom_completeness_pct": bom_completeness_pct,
            "lead_time_accuracy_pct": lead_time_accuracy_pct,
            "inventory_record_accuracy_pct": inventory_record_accuracy_pct,
        },
        error=None,
    )
