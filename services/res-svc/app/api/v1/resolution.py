from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_score import score_scenario
from app.core.strategy import generate_strategies
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.resolution import ResolutionScenario
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/resolution", tags=["resolution"])


class ProposeRequest(BaseModel):
    mo_id: UUID
    constraint_type: str | None = None


class ApproveRequest(BaseModel):
    scenario_id: UUID
    approved_by: str = "system"
    comment: str = ""


@router.post("/scenarios")
async def propose_scenarios(
    req: ProposeRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    mo_result = await session.execute(
        sa_select(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tid,
            ManufacturingOrder.id == req.mo_id,
        )
    )
    mo = mo_result.scalar_one_or_none()
    if not mo:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "MO not found"})

    constraint = req.constraint_type or mo.primary_constraint or "capacity_overload"

    raw_strategies = generate_strategies(
        mo_id=str(mo.id),
        constraint_type=constraint,
        mo_data={"quantity": float(mo.quantity)},
    )

    scenarios = []
    best = None
    best_score = -1
    for s in raw_strategies:
        scored = score_scenario(s)
        if scored["business_score"] > best_score:
            best_score = scored["business_score"]
            best = s
        scenarios.append({**s, **scored, "id": str(uuid4())})

    await kafka_producer.send_event(
        "resolution", "proposed",
        key=str(req.mo_id),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.resolution.proposed",
            source="res-svc",
            tenant_id=tid,
            timestamp=datetime.now(UTC),
            data={
                "mo_id": str(mo.id),
                "constraint_type": constraint,
                "scenario_count": len(scenarios),
                "recommended_strategy": best["strategy"] if best else None,
            },
        ).model_dump(mode="json"),
    )

    return APIResponse(success=True, data={"mo_id": str(mo.id), "constraint": constraint, "scenarios": scenarios}, error=None)


@router.post("/approve")
async def approve_scenario(
    req: ApproveRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    result = await session.execute(
        sa_select(ResolutionScenario).where(
            ResolutionScenario.tenant_id == UUID(tenant_id),
            ResolutionScenario.id == req.scenario_id,
        )
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Scenario not found"})

    scenario.status = "approved"
    scenario.approved_by = req.approved_by
    scenario.approved_at = datetime.now(UTC)
    scenario.comment = req.comment
    await session.commit()

    return APIResponse(success=True, data={
        "scenario_id": str(scenario.id),
        "status": "approved",
        "actions_executed": [
            {"action": "approve_scenario", "target": str(scenario.id), "result": "success"},
        ],
    }, error=None)


@router.get("/scenarios")
async def list_scenarios(
    mo_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    q = sa_select(ResolutionScenario).where(
        ResolutionScenario.tenant_id == UUID(tenant_id)
    )
    if mo_id:
        q = q.where(ResolutionScenario.mo_id == mo_id)
    q = q.order_by(ResolutionScenario.created_at.desc())

    result = await session.execute(q)
    scenarios = result.scalars().all()

    return APIResponse(success=True, data={
        "scenarios": [
            {
                "id": str(s.id),
                "mo_id": str(s.mo_id),
                "strategy": s.strategy,
                "status": s.status,
                "business_score": float(s.business_score) if s.business_score else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in scenarios
        ]
    }, error=None)
