from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.scorecard import calculate_supplier_scorecard
from app.core.rfq_workflow import (
    RFQState,
    award_rfq,
    cancel_rfq,
    create_rfq,
    evaluate_rfq,
    publish_rfq,
    respond_to_rfq,
)
from app.core.supply_graph import build_supply_graph, propagate_risk
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation

router = APIRouter(prefix="/scn", tags=["supply-chain-network"])


class ScorecardRequest(BaseModel):
    supplier_id: str
    historical_data: dict | None = None


class CreateRFQRequest(BaseModel):
    title: str
    description: str = ""
    items: list[dict] = []
    requirements: dict = {}
    deadline: str | None = None


class RespondRFQRequest(BaseModel):
    rfq_id: str
    supplier_id: str
    price: float = 0.0
    lead_time_days: int = 0
    terms: dict = {}
    notes: str = ""


class AwardRFQRequest(BaseModel):
    rfq_id: str
    winning_supplier_id: str


class CancelRFQRequest(BaseModel):
    rfq_id: str


class VisibilityRequest(BaseModel):
    suppliers: list[dict]
    at_risk_supplier_id: str | None = None
    impact_probability: float | None = None


@router.post("/supplier/score")
async def supplier_score(
    req: ScorecardRequest,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "procurement"])),
):
    tenant_id = tenant_ctx.get()
    result = calculate_supplier_scorecard(str(tenant_id), req.supplier_id, req.historical_data)
    return APIResponse(success=True, data={
        **result,
        "xai_explanation": XAIExplanation(
            constraints=["weighted_multi_dimensional_scoring", "configurable_weights", "historical_trend_analysis"],
            assumptions=["otif_weight_0.35", "quality_weight_0.25", "cost_weight_0.20", "sustainability_weight_0.10", "responsiveness_weight_0.10"],
            confidence_score=0.82,
            contributing_factors={
                "composite_score": result["composite_score"],
                "risk_score": float({"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 0.95}.get(result["risk_tier"], 0.3)),
            },
        ).model_dump(),
    }, error=None)


@router.get("/supplier/{supplier_id}/score")
async def get_supplier_score(
    supplier_id: str,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "procurement"])),
):
    tenant_id = tenant_ctx.get()
    result = calculate_supplier_scorecard(str(tenant_id), supplier_id)
    return APIResponse(success=True, data={
        **result,
        "xai_explanation": XAIExplanation(
            constraints=["weighted_multi_dimensional_scoring"],
            assumptions=["default_historical_data"],
            confidence_score=0.70,
            contributing_factors={
                "composite_score": result["composite_score"],
                "risk_score": float({"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 0.95}.get(result["risk_tier"], 0.3)),
            },
        ).model_dump(),
    }, error=None)


@router.post("/rfq")
async def create_rfq_endpoint(
    req: CreateRFQRequest,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "procurement"])),
):
    tenant_id = tenant_ctx.get()
    result = create_rfq(str(tenant_id), req.model_dump())
    return APIResponse(success=True, data=result, error=None)


@router.post("/rfq/{rfq_id}/publish")
async def publish_rfq_endpoint(
    rfq_id: str,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "procurement"])),
):
    result = publish_rfq(rfq_id)
    return APIResponse(success=True, data=result, error=None)


@router.post("/rfq/{rfq_id}/respond")
async def respond_rfq_endpoint(
    rfq_id: str,
    req: RespondRFQRequest,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "supplier"])),
):
    response = respond_to_rfq(rfq_id, req.supplier_id, {
        "price": req.price,
        "lead_time_days": req.lead_time_days,
        "terms": req.terms,
        "notes": req.notes,
    })
    return APIResponse(success=True, data=response, error=None)


@router.post("/rfq/{rfq_id}/award")
async def award_rfq_endpoint(
    rfq_id: str,
    req: AwardRFQRequest,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "procurement"])),
):
    result = award_rfq(rfq_id, req.winning_supplier_id)
    return APIResponse(success=True, data=result, error=None)


@router.post("/rfq/{rfq_id}/evaluate")
async def evaluate_rfq_endpoint(
    rfq_id: str,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "procurement"])),
):
    result = evaluate_rfq(rfq_id)
    return APIResponse(success=True, data=result, error=None)


@router.post("/rfq/{rfq_id}/cancel")
async def cancel_rfq_endpoint(
    rfq_id: str,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    result = cancel_rfq(rfq_id)
    return APIResponse(success=True, data=result, error=None)


@router.post("/visibility")
async def supply_chain_visibility(
    req: VisibilityRequest,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "procurement"])),
):
    graph = build_supply_graph(req.suppliers)
    result_data = {
        "graph": graph,
        "risk_propagation": None,
    }
    if req.at_risk_supplier_id and req.impact_probability is not None:
        risk_impacts = propagate_risk(graph, req.at_risk_supplier_id, req.impact_probability)
        result_data["risk_propagation"] = risk_impacts
    return APIResponse(success=True, data={
        **result_data,
        "xai_explanation": XAIExplanation(
            constraints=["multi_tier_graph_construction", "risk_propagation_bfs"],
            assumptions=["supplier_dependencies_represent_real_supply_chains"],
            confidence_score=0.78,
            contributing_factors={
                "node_count": float(graph["node_count"]),
                "edge_count": float(graph["edge_count"]),
            },
        ).model_dump(),
    }, error=None)