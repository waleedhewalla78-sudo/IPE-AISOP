from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cycle import advance_status, validate_transition
from app.schemas.sop import (
    SopCycleAdvanceRequest,
    SopCycleCreateRequest,
    SopWeightsRequest,
    StageApprovalRequest,
)
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.planning_intelligence import (
    ConsensusDemand,
    SopConsensusWeight,
    SopCycle,
    SopStageGate,
    SopVersion,
)
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/sop", tags=["sales-operations-planning"])


SOP_ROLES = ["admin", "planner", "manager", "executive"]


def _tenant_uuid() -> UUID | None:
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return None
    return UUID(str(tenant_id))


def _user_uuid(user: TokenPayload) -> UUID | None:
    try:
        return UUID(str(user.sub))
    except Exception:
        return None


def _no_tenant() -> APIResponse:
    return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})


def _cycle_to_dict(cycle: SopCycle) -> dict:
    return {
        "id": str(cycle.id),
        "cycle_name": cycle.cycle_name,
        "cycle_month": cycle.cycle_month.isoformat() if cycle.cycle_month else None,
        "status": cycle.status,
        "demand_review_deadline": cycle.demand_review_deadline.isoformat() if cycle.demand_review_deadline else None,
        "supply_review_deadline": cycle.supply_review_deadline.isoformat() if cycle.supply_review_deadline else None,
        "reconciliation_deadline": cycle.reconciliation_deadline.isoformat() if cycle.reconciliation_deadline else None,
        "management_review_deadline": cycle.management_review_deadline.isoformat() if cycle.management_review_deadline else None,
        "created_by": str(cycle.created_by) if cycle.created_by else None,
        "created_at": cycle.created_at.isoformat() if cycle.created_at else None,
        "closed_at": cycle.closed_at.isoformat() if cycle.closed_at else None,
    }


def _stage_to_dict(stage: SopStageGate) -> dict:
    return {
        "id": str(stage.id),
        "cycle_id": str(stage.cycle_id),
        "stage": stage.stage,
        "status": stage.status,
        "approved_by": str(stage.approved_by) if stage.approved_by else None,
        "approved_at": stage.approved_at.isoformat() if stage.approved_at else None,
        "notes": stage.notes,
    }


def _version_to_dict(version: SopVersion) -> dict:
    return {
        "id": str(version.id),
        "cycle_id": str(version.cycle_id),
        "version_type": version.version_type,
        "version_name": version.version_name,
        "is_active": bool(version.is_active),
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }


async def _versions_for_cycle(session: AsyncSession, tenant_id: UUID, cycle_id: UUID) -> list[dict]:
    versions = (
        await session.execute(
            sa_select(SopVersion).where(
                SopVersion.tenant_id == tenant_id,
                SopVersion.cycle_id == cycle_id,
            )
        )
    ).scalars().all()
    return [_version_to_dict(v) for v in versions]
    return {
        "weight_sales": float(weights.weight_sales) if weights else 0.30,
        "weight_statistical": float(weights.weight_statistical) if weights else 0.40,
        "weight_marketing": float(weights.weight_marketing) if weights else 0.20,
        "weight_finance": float(weights.weight_finance) if weights else 0.10,
    }


async def _get_weights(session: AsyncSession, tenant_id: UUID) -> SopConsensusWeight | None:
    return (
        await session.execute(sa_select(SopConsensusWeight).where(SopConsensusWeight.tenant_id == tenant_id))
    ).scalar_one_or_none()


async def _consensus_rows(session: AsyncSession, tenant_id: UUID) -> list[ConsensusDemand]:
    return (
        await session.execute(sa_select(ConsensusDemand).where(ConsensusDemand.tenant_id == tenant_id))
    ).scalars().all()


@router.post("/cycle")
async def create_cycle(
    req: SopCycleCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(SOP_ROLES)),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    cycle = SopCycle(
        tenant_id=tenant_id,
        cycle_name=req.cycle_name,
        cycle_month=req.cycle_month,
        demand_review_deadline=req.demand_review_deadline,
        supply_review_deadline=req.supply_review_deadline,
        reconciliation_deadline=req.reconciliation_deadline,
        management_review_deadline=req.management_review_deadline,
        created_by=_user_uuid(current_user),
    )
    session.add(cycle)
    await session.flush()
    baseline = SopVersion(
        tenant_id=tenant_id,
        cycle_id=cycle.id,
        version_type="baseline",
        version_name="Baseline",
        is_active=True,
        created_by=_user_uuid(current_user),
    )
    session.add(baseline)
    await session.flush()
    await session.commit()
    data = _cycle_to_dict(cycle)
    data["versions"] = [_version_to_dict(baseline)]
    return APIResponse(success=True, data=data, error=None)


@router.get("/cycle")
async def list_cycles(
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(SOP_ROLES)),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    cycles = (
        await session.execute(
            sa_select(SopCycle).where(SopCycle.tenant_id == tenant_id).order_by(SopCycle.cycle_month.desc())
        )
    ).scalars().all()
    return APIResponse(success=True, data={"rows": [_cycle_to_dict(cycle) for cycle in cycles]}, error=None)


@router.get("/cycle/{cycle_id}")
async def get_cycle(
    cycle_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(SOP_ROLES)),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    cycle = (
        await session.execute(
            sa_select(SopCycle).where(SopCycle.tenant_id == tenant_id, SopCycle.id == cycle_id)
        )
    ).scalar_one_or_none()
    if not cycle:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "S&OP cycle not found"})
    data = _cycle_to_dict(cycle)
    data["versions"] = await _versions_for_cycle(session, tenant_id, cycle_id)
    return APIResponse(success=True, data=data, error=None)


@router.post("/cycle/{cycle_id}/advance")
async def advance_cycle(
    cycle_id: UUID,
    req: SopCycleAdvanceRequest | None = None,
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(SOP_ROLES)),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    cycle = (
        await session.execute(
            sa_select(SopCycle).where(SopCycle.tenant_id == tenant_id, SopCycle.id == cycle_id)
        )
    ).scalar_one_or_none()
    if not cycle:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "S&OP cycle not found"})

    try:
        next_status = req.target_status if req and req.target_status else advance_status(cycle.status)
        validate_transition(cycle.status, next_status)
    except ValueError as exc:
        return APIResponse(success=False, data=None, error={"code": "INVALID_TRANSITION", "message": str(exc)})

    cycle.status = next_status
    if next_status == "closed":
        cycle.closed_at = datetime.now(UTC)
    await session.commit()
    return APIResponse(success=True, data=_cycle_to_dict(cycle), error=None)


@router.post("/cycle/{cycle_id}/stage/{stage}/approve")
async def approve_stage(
    cycle_id: UUID,
    stage: str,
    req: StageApprovalRequest | None = None,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(SOP_ROLES)),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    cycle = (
        await session.execute(
            sa_select(SopCycle).where(SopCycle.tenant_id == tenant_id, SopCycle.id == cycle_id)
        )
    ).scalar_one_or_none()
    if not cycle:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "S&OP cycle not found"})

    # Only the current cycle stage may be approved (UAT-8 invalid future stage)
    if stage != cycle.status:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve stage '{stage}' while cycle is in '{cycle.status}'",
        )

    stage_gate = (
        await session.execute(
            sa_select(SopStageGate).where(
                SopStageGate.tenant_id == tenant_id,
                SopStageGate.cycle_id == cycle_id,
                SopStageGate.stage == stage,
            )
        )
    ).scalar_one_or_none()
    if stage_gate is None:
        stage_gate = SopStageGate(tenant_id=tenant_id, cycle_id=cycle_id, stage=stage)
        session.add(stage_gate)

    payload = req or StageApprovalRequest()
    stage_gate.status = payload.status
    stage_gate.notes = payload.notes
    if payload.status == "approved":
        stage_gate.approved_by = _user_uuid(current_user)
        stage_gate.approved_at = datetime.now(UTC)
    await session.flush()
    await session.commit()
    return APIResponse(success=True, data=_stage_to_dict(stage_gate), error=None)


@router.get("/config/weights")
async def get_weights(
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(SOP_ROLES)),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    weights = await _get_weights(session, tenant_id)
    return APIResponse(success=True, data=_weights_to_dict(weights), error=None)


@router.put("/config/weights")
async def update_weights(
    req: SopWeightsRequest,
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    weights = await _get_weights(session, tenant_id)
    if weights is None:
        weights = SopConsensusWeight(tenant_id=tenant_id)
        session.add(weights)
    weights.weight_sales = req.weight_sales
    weights.weight_statistical = req.weight_statistical
    weights.weight_marketing = req.weight_marketing
    weights.weight_finance = req.weight_finance
    await session.commit()
    return APIResponse(success=True, data=_weights_to_dict(weights), error=None)


@router.post("/supply-review/run")
async def run_supply_review(
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(SOP_ROLES)),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    rows = await _consensus_rows(session, tenant_id)
    total_demand = sum(float(row.consensus_qty or 0) for row in rows)
    constrained = sum(float(row.constrained_demand_qty or row.consensus_qty or 0) for row in rows)
    return APIResponse(success=True, data={
        "status": "completed",
        "consensus_rows": len(rows),
        "total_consensus_qty": total_demand,
        "total_constrained_qty": constrained,
        "supply_gap_qty": total_demand - constrained,
    }, error=None)


@router.get("/supply-review/results")
async def supply_review_results(
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(SOP_ROLES)),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    rows = await _consensus_rows(session, tenant_id)
    results = [
        {
            "consensus_id": str(row.id),
            "product_id": str(row.product_id),
            "period_start": row.period_start.isoformat() if row.period_start else None,
            "consensus_qty": float(row.consensus_qty or 0),
            "constrained_demand_qty": float(row.constrained_demand_qty or row.consensus_qty or 0),
            "lost_sales_qty": float(row.lost_sales_qty or 0),
            "lost_sales_value": float(row.lost_sales_value or 0),
        }
        for row in rows
    ]
    return APIResponse(success=True, data={"rows": results}, error=None)


@router.get("/reconciliation/dashboard")
async def reconciliation_dashboard(
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(SOP_ROLES)),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    rows = await _consensus_rows(session, tenant_id)
    revenue = sum(float(row.consensus_revenue or 0) for row in rows)
    cost = sum(float(row.consensus_cost or 0) for row in rows)
    lost_sales = sum(float(row.lost_sales_value or 0) for row in rows)
    return APIResponse(success=True, data={
        "consensus_rows": len(rows),
        "consensus_revenue": revenue,
        "consensus_cost": cost,
        "consensus_profit": revenue - cost,
        "lost_sales_value": lost_sales,
        "requires_management_review": lost_sales > 0,
    }, error=None)


@router.get("/management-review/executive-summary")
async def management_review_summary(
    session: AsyncSession = Depends(get_db_session),
    _user: TokenPayload = Depends(require_roles(SOP_ROLES)),
):
    tenant_id = _tenant_uuid()
    if tenant_id is None:
        return _no_tenant()

    rows = await _consensus_rows(session, tenant_id)
    qty = sum(float(row.consensus_qty or 0) for row in rows)
    revenue = sum(float(row.consensus_revenue or 0) for row in rows)
    profit = sum(float(row.consensus_profit or 0) for row in rows)
    return APIResponse(success=True, data={
        "summary": "S&OP executive summary generated from consensus demand.",
        "total_consensus_qty": qty,
        "total_revenue": revenue,
        "total_profit": profit,
        "decision_points": [
            "Approve consensus plan" if rows else "Load consensus demand",
            "Review constrained demand gaps" if any(row.lost_sales_qty for row in rows) else "No open supply gap detected",
        ],
    }, error=None)
