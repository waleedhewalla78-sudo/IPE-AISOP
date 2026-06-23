from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.financial_projection import (
    FinancialProjectionInput,
    BOMComponent,
    RoutingStep,
    generate_financial_projection,
)
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.financial_projection import FinancialProjection
from ipe_shared.models.product import Product
from ipe_shared.models.bom import BillOfMaterial, BomLine
from ipe_shared.models.routing import RoutingOperation
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation

router = APIRouter(prefix="/financial", tags=["financial"])


class ProjectionRequest(BaseModel):
    product_id: UUID
    quantity: int
    selling_price: float = 0.0
    overhead_pct: float = 0.15
    labor_cost_per_hour: float = 50.0


class BatchProjectionRequest(BaseModel):
    projections: list[ProjectionRequest]


async def _generate_projection(req: ProjectionRequest, tid: UUID, session: AsyncSession) -> dict:
    """Core projection logic shared by single and batch endpoints."""
    product_result = await session.execute(
        sa_select(Product).where(Product.tenant_id == tid, Product.id == req.product_id)
    )
    product = product_result.scalar_one_or_none()

    bom_result = await session.execute(
        sa_select(BillOfMaterial).where(BillOfMaterial.tenant_id == tid, BillOfMaterial.product_id == req.product_id)
    )
    bom = bom_result.scalar_one_or_none()

    bom_components = []
    if bom:
        bom_line_result = await session.execute(
            sa_select(BomLine).where(BomLine.tenant_id == tid, BomLine.bom_id == bom.id)
        )
        for line in bom_line_result.scalars().all():
            comp_product_result = await session.execute(
                sa_select(Product).where(Product.tenant_id == tid, Product.id == line.component_id)
            )
            comp_product = comp_product_result.scalar_one_or_none()
            bom_components.append(BOMComponent(
                component_id=str(line.component_id),
                quantity_per=float(line.quantity_per or 1),
                standard_cost=float(comp_product.standard_cost if comp_product else 0),
                scrap_rate_pct=float(line.scrap_rate_pct or 0),
            ))

    routing_steps = []
    if bom:
        routing_result = await session.execute(
            sa_select(RoutingOperation).where(RoutingOperation.tenant_id == tid, RoutingOperation.bom_id == bom.id)
        )
        for routing in routing_result.scalars().all():
            wc_result = await session.execute(
                sa_select(WorkCenter).where(WorkCenter.tenant_id == tid, WorkCenter.id == routing.work_center_id)
            )
            wc = wc_result.scalar_one_or_none()
            routing_steps.append(RoutingStep(
                work_center_id=str(routing.work_center_id),
                duration_mins=float(routing.duration_planned_mins or 60),
                cost_per_hour=float(wc.cost_per_hour if wc else 0),
                energy_kwh_per_hour=float(wc.energy_kwh_per_hour if wc else 0),
                energy_cost_per_kwh=0.1,
            ))

    input_data = FinancialProjectionInput(
        product_id=str(req.product_id),
        quantity=req.quantity,
        selling_price=req.selling_price,
        bom_components=bom_components,
        routing_steps=routing_steps,
        overhead_pct=req.overhead_pct,
        labor_cost_per_hour=req.labor_cost_per_hour,
    )

    result = generate_financial_projection(input_data)

    projection = FinancialProjection(
        id=uuid4(),
        tenant_id=tid,
        product_id=req.product_id,
        projection_type="standard",
        quantity=req.quantity,
        unit_cost=result.unit_cost,
        total_cost=result.total_cost,
        revenue=result.revenue,
        margin=result.margin,
        margin_pct=result.margin_pct,
        labor_cost=result.labor_cost,
        material_cost=result.material_cost,
        energy_cost=result.energy_cost,
        overhead_cost=result.overhead_cost,
        wip_value=result.wip_value,
        projection_date=datetime.now(UTC),
        status="final",
        metadata_json=result.cost_breakdown,
    )

    session.add(projection)
    await session.commit()
    await session.refresh(projection)

    return {
        "projection_id": str(projection.id),
        "product_id": result.product_id,
        "quantity": result.quantity,
        "unit_cost": round(result.unit_cost, 2),
        "total_cost": round(result.total_cost, 2),
        "revenue": round(result.revenue, 2),
        "margin": round(result.margin, 2),
        "margin_pct": round(result.margin_pct, 2),
        "labor_cost": round(result.labor_cost, 2),
        "material_cost": round(result.material_cost, 2),
        "energy_cost": round(result.energy_cost, 2),
        "overhead_cost": round(result.overhead_cost, 2),
        "wip_value": round(result.wip_value, 2),
        "cost_breakdown": {k: round(v, 2) for k, v in result.cost_breakdown.items()},
        "margin_alert": result.margin_alert,
        "xai_explanation": XAIExplanation(
            constraints=["bom_cost_rollup", "routing_step_costs", f"overhead_{req.overhead_pct}_pct"],
            assumptions=["standard_cost_current", f"labor_rate_{req.labor_cost_per_hour}_per_hour"],
            confidence_score=round(min(1.0, max(0.0, result.margin_pct / 100.0)) if result.margin_pct else 0.0, 4),
            contributing_factors={
                "material": round(result.material_cost / max(1, result.total_cost), 4),
                "labor": round(result.labor_cost / max(1, result.total_cost), 4),
                "energy": round(result.energy_cost / max(1, result.total_cost), 4),
                "overhead": round(result.overhead_cost / max(1, result.total_cost), 4),
            },
        ).model_dump(),
    }


@router.post("/project")
async def create_projection(
    req: ProjectionRequest,
    current_user=Depends(require_roles(["admin", "planner", "manager"])),
    session: AsyncSession = Depends(get_db_session),
):
    """Generate financial projection for a product."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)
    data = await _generate_projection(req, tid, session)
    return APIResponse(success=True, data=data, error=None)


@router.post("/project/batch")
async def batch_projection(
    req: BatchProjectionRequest,
    current_user=Depends(require_roles(["admin", "planner", "manager"])),
    session: AsyncSession = Depends(get_db_session),
):
    """Batch generate financial projections."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)
    results = []
    for proj_req in req.projections:
        data = await _generate_projection(proj_req, tid, session)
        results.append(data)

    return APIResponse(success=True, data={
        "projections": results,
        "total_count": len(results),
    }, error=None)


@router.get("/projections")
async def list_projections(
    product_id: UUID | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    """List financial projections."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)
    query = sa_select(FinancialProjection).where(FinancialProjection.tenant_id == tid)
    if product_id:
        query = query.where(FinancialProjection.product_id == product_id)

    result = await session.execute(query)
    projections = result.scalars().all()

    return APIResponse(success=True, data=[
        {
            "id": str(p.id),
            "product_id": str(p.product_id),
            "quantity": p.quantity,
            "unit_cost": round(p.unit_cost, 2),
            "total_cost": round(p.total_cost, 2),
            "revenue": round(p.revenue, 2),
            "margin": round(p.margin, 2),
            "margin_pct": round(p.margin_pct, 2),
            "status": p.status,
            "projection_date": str(p.projection_date),
        }
        for p in projections
    ], error=None)


@router.get("/margin-alerts")
async def margin_alerts(
    threshold_pct: float = 10.0,
    session: AsyncSession = Depends(get_db_session),
):
    """Get products with margin below threshold."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)
    result = await session.execute(
        sa_select(FinancialProjection).where(
            FinancialProjection.tenant_id == tid,
            FinancialProjection.margin_pct < threshold_pct,
        )
    )
    projections = result.scalars().all()

    return APIResponse(success=True, data=[
        {
            "id": str(p.id),
            "product_id": str(p.product_id),
            "quantity": p.quantity,
            "margin_pct": round(p.margin_pct, 2),
            "margin": round(p.margin, 2),
            "alert": "low_margin" if p.margin_pct >= 0 else "negative_margin",
        }
        for p in projections
    ], error=None)
