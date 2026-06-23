from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cost_accounting import compute_cogm, compute_copq, compute_cost_accounting, get_gl_account_map
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.tenant import Tenant
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation

router = APIRouter(prefix="/cost-accounting", tags=["cost-accounting"])


class COGMRequest(BaseModel):
    material_cost: float
    labor_cost: float
    energy_cost: float
    overhead_cost: float
    quantity: int


class COPQRequest(BaseModel):
    total_quantity: int
    defect_rate_pct: float = 2.0
    rework_rate_pct: float = 1.0
    inspection_cost_per_unit: float = 5.0
    warranty_cost_per_unit: float = 10.0
    standard_cost_per_unit: float = 100.0
    selling_price_per_unit: float = 150.0


class FullCostRequest(BaseModel):
    product_id: str
    quantity: int
    selling_price: float
    material_cost: float
    labor_cost: float
    energy_cost: float
    overhead_cost: float
    actual_costs: dict[str, float] | None = None
    defect_rate_pct: float = 2.0
    rework_rate_pct: float = 1.0
    inspection_cost_per_unit: float = 5.0
    warranty_cost_per_unit: float = 10.0


async def _get_tenant_config(session: AsyncSession, tenant_id: str) -> dict:
    result = await session.execute(sa_select(Tenant.config).where(Tenant.id == tenant_id))
    row = result.fetchone()
    if row and row[0]:
        return dict(row[0])
    return {}


@router.post("/cogm")
async def calculate_cogm(
    req: COGMRequest,
    current_user=Depends(require_roles(["admin", "planner", "manager", "finance"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tenant_config = await _get_tenant_config(session, tenant_id)
    gl_map = get_gl_account_map(tenant_config)

    result = compute_cogm(
        material_cost=req.material_cost,
        labor_cost=req.labor_cost,
        energy_cost=req.energy_cost,
        overhead_cost=req.overhead_cost,
        quantity=req.quantity,
        gl_account_map=gl_map,
    )

    return APIResponse(success=True, data={
        "material_cost": result.material_cost,
        "labor_cost": result.labor_cost,
        "energy_cost": result.energy_cost,
        "overhead_cost": result.overhead_cost,
        "total_cogm": result.total_cogm,
        "cogm_per_unit": result.cogm_per_unit,
        "gl_accounts": result.gl_accounts,
    }, error=None)


@router.post("/copq")
async def calculate_copq(
    req: COPQRequest,
    current_user=Depends(require_roles(["admin", "planner", "manager", "finance"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tenant_config = await _get_tenant_config(session, tenant_id)
    gl_map = get_gl_account_map(tenant_config)

    result = compute_copq(
        total_quantity=req.total_quantity,
        defect_rate_pct=req.defect_rate_pct,
        rework_rate_pct=req.rework_rate_pct,
        inspection_cost_per_unit=req.inspection_cost_per_unit,
        warranty_cost_per_unit=req.warranty_cost_per_unit,
        standard_cost_per_unit=req.standard_cost_per_unit,
        selling_price_per_unit=req.selling_price_per_unit,
        gl_account_map=gl_map,
    )

    return APIResponse(success=True, data={
        "scrap_cost": result.scrap_cost,
        "rework_cost": result.rework_cost,
        "inspection_cost": result.inspection_cost,
        "warranty_cost": result.warranty_cost,
        "total_copq": result.total_copq,
        "copq_as_pct_of_revenue": result.copq_as_pct_of_revenue,
    }, error=None)


@router.post("/full")
async def full_cost_accounting(
    req: FullCostRequest,
    current_user=Depends(require_roles(["admin", "planner", "manager", "finance"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tenant_config = await _get_tenant_config(session, tenant_id)
    gl_map = get_gl_account_map(tenant_config)

    result = compute_cost_accounting(
        product_id=req.product_id,
        quantity=req.quantity,
        selling_price=req.selling_price,
        material_cost=req.material_cost,
        labor_cost=req.labor_cost,
        energy_cost=req.energy_cost,
        overhead_cost=req.overhead_cost,
        actual_costs=req.actual_costs,
        defect_rate_pct=req.defect_rate_pct,
        rework_rate_pct=req.rework_rate_pct,
        inspection_cost_per_unit=req.inspection_cost_per_unit,
        warranty_cost_per_unit=req.warranty_cost_per_unit,
        gl_account_map=gl_map,
    )

    variance_data = [
        {
            "cost_element": v.cost_element,
            "planned": v.planned,
            "actual": v.actual,
            "variance": v.variance,
            "variance_pct": v.variance_pct,
        }
        for v in result.variances
    ]

    return APIResponse(success=True, data={
        "product_id": result.product_id,
        "quantity": result.quantity,
        "selling_price": result.selling_price,
        "revenue": result.revenue,
        "cogm": {
            "material_cost": result.cogm.material_cost,
            "labor_cost": result.cogm.labor_cost,
            "energy_cost": result.cogm.energy_cost,
            "overhead_cost": result.cogm.overhead_cost,
            "total_cogm": result.cogm.total_cogm,
            "cogm_per_unit": result.cogm.cogm_per_unit,
            "gl_accounts": result.cogm.gl_accounts,
        },
        "copq": {
            "scrap_cost": result.copq.scrap_cost,
            "rework_cost": result.copq.rework_cost,
            "inspection_cost": result.copq.inspection_cost,
            "warranty_cost": result.copq.warranty_cost,
            "total_copq": result.copq.total_copq,
            "copq_as_pct_of_revenue": result.copq.copq_as_pct_of_revenue,
        },
        "gross_margin": result.gross_margin,
        "gross_margin_pct": result.gross_margin_pct,
        "net_margin": result.net_margin,
        "net_margin_pct": result.net_margin_pct,
        "variances": variance_data,
        "xai_explanation": XAIExplanation(
            constraints=[
                "cogm_gl_mapping",
                "copq_defect_rates",
                "variance_analysis_planned_vs_actual",
            ],
            assumptions=[
                "rework_cost_is_30_percent_of_standard",
                "warranty_rate_is_5_percent",
            ],
            confidence_score=0.88,
            contributing_factors=result.xai_factors,
        ).model_dump(),
    }, error=None)