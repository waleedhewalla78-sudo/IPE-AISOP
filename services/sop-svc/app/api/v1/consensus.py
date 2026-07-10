from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.consensus import ConsensusWeights, calculate_consensus_qty
from app.core.cost_rollup import rollup_costs
from app.schemas.consensus import ConsensusCalculateRequest, ConsensusUpdateRequest
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.planning_intelligence import ConsensusDemand, SopConsensusWeight
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/sop/consensus", tags=["sop-consensus"])
SOP_ROLES = ["admin", "planner", "manager", "executive"]


def _tenant_uuid() -> UUID | None:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return None
    return UUID(str(tenant_id))


def _no_tenant() -> APIResponse:
    return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})


def _row_to_dict(row: ConsensusDemand) -> dict:
    return {
        "id": str(row.id),
        "version_id": str(row.version_id),
        "product_id": str(row.product_id),
        "location_id": str(row.location_id) if row.location_id else None,
        "customer_id": str(row.customer_id) if row.customer_id else None,
        "period_start": row.period_start.isoformat() if row.period_start else None,
        "period_type": row.period_type,
        "sales_forecast_qty": float(row.sales_forecast_qty) if row.sales_forecast_qty is not None else None,
        "marketing_forecast_qty": float(row.marketing_forecast_qty) if row.marketing_forecast_qty is not None else None,
        "statistical_forecast_qty": float(row.statistical_forecast_qty) if row.statistical_forecast_qty is not None else None,
        "finance_plan_qty": float(row.finance_plan_qty) if row.finance_plan_qty is not None else None,
        "consensus_qty": float(row.consensus_qty or 0),
        "planned_price": float(row.planned_price) if row.planned_price is not None else None,
        "consensus_revenue": float(row.consensus_revenue or 0),
        "cost_per_unit": float(row.cost_per_unit) if row.cost_per_unit is not None else None,
        "consensus_cost": float(row.consensus_cost or 0),
        "consensus_profit": float(row.consensus_profit or 0),
        "constrained_demand_qty": float(row.constrained_demand_qty) if row.constrained_demand_qty is not None else None,
        "lost_sales_qty": float(row.lost_sales_qty or 0),
        "lost_sales_value": float(row.lost_sales_value or 0),
    }


async def _weights(session: AsyncSession, tenant_id: UUID) -> ConsensusWeights:
    row = (
        await session.execute(sa_select(SopConsensusWeight).where(SopConsensusWeight.tenant_id == tenant_id))
    ).scalar_one_or_none()
    if not row:
        return ConsensusWeights()
    return ConsensusWeights(
        sales=float(row.weight_sales),
        statistical=float(row.weight_statistical),
        marketing=float(row.weight_marketing),
        finance=float(row.weight_finance),
    )


def _calculate_payload(req: ConsensusCalculateRequest | ConsensusDemand, weights: ConsensusWeights) -> dict:
    consensus_qty = calculate_consensus_qty(
        sales=req.sales_forecast_qty,
        statistical=req.statistical_forecast_qty,
        marketing=req.marketing_forecast_qty,
        finance=req.finance_plan_qty,
        weights=weights,
    )
    costs = rollup_costs(consensus_qty, req.planned_price, req.cost_per_unit)
    return {"consensus_qty": consensus_qty, **costs}


@router.post("/calculate")
async def calculate_consensus(
    req: ConsensusCalculateRequest,
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(SOP_ROLES)),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    weights = await _weights(session, tenant_id)
    calculated = _calculate_payload(req, weights)
    data = {"weights": weights.__dict__, **calculated}

    if req.persist:
        missing = [name for name in ("version_id", "product_id", "period_start") if getattr(req, name) is None]
        if missing:
            return APIResponse(
                success=False,
                data=data,
                error={"code": "MISSING_FIELDS", "message": f"Missing fields for persist: {', '.join(missing)}"},
            )
        row = ConsensusDemand(
            tenant_id=tenant_id,
            version_id=req.version_id,
            product_id=req.product_id,
            location_id=req.location_id,
            customer_id=req.customer_id,
            period_start=req.period_start,
            period_type=req.period_type,
            sales_forecast_qty=req.sales_forecast_qty,
            marketing_forecast_qty=req.marketing_forecast_qty,
            statistical_forecast_qty=req.statistical_forecast_qty,
            finance_plan_qty=req.finance_plan_qty,
            consensus_qty=calculated["consensus_qty"],
            planned_price=req.planned_price,
            consensus_revenue=calculated["revenue"],
            cost_per_unit=req.cost_per_unit,
            consensus_cost=calculated["cost"],
            consensus_profit=calculated["profit"],
        )
        session.add(row)
        await session.flush()
        await session.commit()
        data["row"] = _row_to_dict(row)

    return APIResponse(success=True, data=data, error=None)


@router.get("")
async def list_consensus(
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(SOP_ROLES)),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    rows = (
        await session.execute(
            sa_select(ConsensusDemand).where(ConsensusDemand.tenant_id == tenant_id).order_by(ConsensusDemand.period_start.desc())
        )
    ).scalars().all()
    return APIResponse(success=True, data={"rows": [_row_to_dict(row) for row in rows]}, error=None)


@router.put("/{consensus_id}")
async def update_consensus(
    consensus_id: UUID,
    req: ConsensusUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    row = (
        await session.execute(
            sa_select(ConsensusDemand).where(ConsensusDemand.tenant_id == tenant_id, ConsensusDemand.id == consensus_id)
        )
    ).scalar_one_or_none()
    if not row:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Consensus demand not found"})

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(row, field, value)

    weights = await _weights(session, tenant_id)
    calculated = _calculate_payload(row, weights)
    row.consensus_qty = calculated["consensus_qty"]
    row.consensus_revenue = calculated["revenue"]
    row.consensus_cost = calculated["cost"]
    row.consensus_profit = calculated["profit"]
    if row.constrained_demand_qty is not None:
        row.lost_sales_qty = max(0.0, float(row.consensus_qty or 0) - float(row.constrained_demand_qty or 0))
        row.lost_sales_value = float(row.lost_sales_qty or 0) * float(row.planned_price or 0)
    await session.commit()
    return APIResponse(success=True, data=_row_to_dict(row), error=None)
