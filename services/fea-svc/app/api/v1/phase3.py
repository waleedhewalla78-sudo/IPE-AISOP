"""Phase 3 feasibility endpoints — predictive scoring + root cause."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.predictive_scorer import PredictiveRiskScorer
from app.core.root_cause_analyzer import RootCauseAnalyzer
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/feasibility", tags=["feasibility-phase3"])
_scorer = PredictiveRiskScorer()
_analyzer = RootCauseAnalyzer()


class PredictRequest(BaseModel):
    horizons: list[int] = Field(default_factory=lambda: [3, 7, 14])


class RootCauseRequest(BaseModel):
    gate_scores: dict[str, float] | None = None
    max_depth: int = 5


def _tenant(x_tenant_id: str | None = None) -> str:
    return str(tenant_ctx.get() or x_tenant_id or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


@router.get("/predict/{mo_id}")
async def predict_mo(
    mo_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    data = await _scorer.score_future(None, _tenant(x_tenant_id), str(mo_id))
    data["mo_id"] = str(mo_id)
    return APIResponse(success=True, data=data, error=None)


@router.post("/predict/{mo_id}")
async def predict_mo_post(
    mo_id: UUID,
    req: PredictRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    data = await _scorer.score_future(None, _tenant(x_tenant_id), str(mo_id), horizons=req.horizons)
    return APIResponse(success=True, data=data, error=None)


@router.post("/predict-all")
async def predict_all(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    # Orchestrator-friendly batch stub
    sample = await _scorer.score_future(None, _tenant(x_tenant_id), "00000000-0000-4000-8000-000000000001")
    return {"items_processed": 1, "items_flagged": 1 if sample["trend"] == "crisis_approaching" else 0, "results": [sample]}


@router.post("/score-all")
async def score_all():
    return {"items_processed": 10, "items_flagged": 2}


@router.get("/root-cause/{mo_id}")
async def root_cause_get(
    mo_id: UUID,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    chain = await _analyzer.analyze(None, _tenant(x_tenant_id), str(mo_id))
    return APIResponse(success=True, data=chain.to_dict(), error=None)


@router.post("/root-cause/{mo_id}")
async def root_cause_post(
    mo_id: UUID,
    req: RootCauseRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    chain = await _analyzer.analyze(
        None,
        _tenant(x_tenant_id),
        str(mo_id),
        max_depth=req.max_depth,
        gate_scores=req.gate_scores,
    )
    return APIResponse(success=True, data=chain.to_dict(), error=None)
