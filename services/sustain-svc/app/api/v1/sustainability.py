from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.scorer import calculate_circularity_score
from app.core.eol_planner import calculate_eol_plan
from app.core.recyclability import calculate_recyclability_score
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation

router = APIRouter(prefix="/sustainability", tags=["sustainability"])


class CircularityRequest(BaseModel):
    product_id: str
    bom_components: list[dict] = []


class EolPlanRequest(BaseModel):
    product_id: str
    product_lifecycle_months: int | None = None
    regulatory_region: str = "EU"


class RecyclabilityRequest(BaseModel):
    product_id: str
    bom_components: list[dict] = []


@router.post("/circularity-score")
async def circularity_score(
    req: CircularityRequest,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "sustainability"])),
):
    tenant_id = tenant_ctx.get()
    result = calculate_circularity_score(req.product_id, req.bom_components)
    return APIResponse(success=True, data={
        "product_id": req.product_id,
        **result,
        "xai_explanation": XAIExplanation(
            constraints=["material_recovery_calculation", "take_back_eligibility", "disassembly_cost_estimation"],
            assumptions=["industry_average_recycling_rates", "standard_disassembly_costs"],
            confidence_score=0.85,
            contributing_factors={"material_recovery": round(result.get("material_recovery_pct", 0) / 100, 4)},
        ).model_dump(),
    }, error=None)


@router.get("/eol-plan")
async def eol_plan(
    product_id: str,
    regulatory_region: str = "EU",
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "sustainability"])),
):
    tenant_id = tenant_ctx.get()
    result = calculate_eol_plan(product_id, regulatory_region)
    return APIResponse(success=True, data={
        "product_id": product_id,
        **result,
        "xai_explanation": XAIExplanation(
            constraints=["lifecycle_prediction", "obsolescence_scoring", "regulatory_phase_out"],
            assumptions=["average_product_lifecycle", "standard_phase_out_timelines"],
            confidence_score=0.80,
            contributing_factors={"eol_risk": round(result.get("eol_risk_score", 0) / 100, 4)},
        ).model_dump(),
    }, error=None)


@router.post("/recyclability-score")
async def recyclability_score(
    req: RecyclabilityRequest,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "sustainability"])),
):
    tenant_id = tenant_ctx.get()
    result = calculate_recyclability_score(req.product_id, req.bom_components)
    return APIResponse(success=True, data={
        "product_id": req.product_id,
        **result,
        "xai_explanation": XAIExplanation(
            constraints=["material_composition_analysis", "disassembly_complexity", "hazardous_content_check"],
            assumptions=["regional_recycling_infrastructure_availability"],
            confidence_score=0.82,
            contributing_factors={"recyclability": round(result.get("score", 0) / 100, 4)},
        ).model_dump(),
    }, error=None)