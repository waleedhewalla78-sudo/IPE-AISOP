from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auto_confirm import should_auto_confirm
from app.core.scorer import calculate_feasibility
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/feasibility", tags=["feasibility"])


class ScoreRequest(BaseModel):
    mo_id: UUID
    demand_score: float | None = None
    bom_score: float | None = None
    material_score: float | None = None
    capacity_score: float | None = None
    labor_score: float | None = None
    autonomy_mode: str = "shadow"


class AutoConfirmRequest(BaseModel):
    mo_id: UUID
    feasibility_score: float
    autonomy_mode: str = "shadow"
    primary_constraint: str | None = None


@router.post("/score")
async def score_feasibility(
    req: ScoreRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )
    result = calculate_feasibility(
        demand_score=req.demand_score,
        bom_score=req.bom_score,
        material_score=req.material_score,
        capacity_score=req.capacity_score,
        labor_score=req.labor_score,
        autonomy_mode=req.autonomy_mode,
    )

    await kafka_producer.send_event(
        "mo", "feasibility_scored",
        key=str(req.mo_id),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.mo.feasibility_scored",
            source="fea-svc",
            tenant_id=UUID(tenant_id),
            timestamp=datetime.now(UTC),
            data={
                "mo_id": str(req.mo_id),
                "overall_score": result["feasibility_score"],
                "gate_scores": result.get("gate_scores", {}),
                "action_taken": result.get("action_taken", ""),
                "primary_constraint": result.get("primary_constraint"),
                "risk_level": result.get("risk_level", "medium"),
            },
        ).model_dump(mode="json"),
    )

    return APIResponse(success=True, data=result, error=None)


@router.post("/auto-confirm")
async def auto_confirm(
    req: AutoConfirmRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )
    result = should_auto_confirm(
        feasibility_score=req.feasibility_score,
        autonomy_mode=req.autonomy_mode,
        primary_constraint=req.primary_constraint,
    )

    if result.get("should_confirm"):
        await kafka_producer.send_event(
            "mo", "auto_confirmed",
            key=str(req.mo_id),
            value=EventEnvelope(
                event_id=str(uuid4()),
                event_type="ipe.mo.auto_confirmed",
                source="fea-svc",
                tenant_id=UUID(tenant_id),
                timestamp=datetime.now(UTC),
                data={
                    "mo_id": str(req.mo_id),
                    "feasibility_score": req.feasibility_score,
                    "autonomy_mode": req.autonomy_mode,
                    "reason": result.get("reason", ""),
                },
            ).model_dump(mode="json"),
        )

    return APIResponse(success=True, data=result, error=None)
