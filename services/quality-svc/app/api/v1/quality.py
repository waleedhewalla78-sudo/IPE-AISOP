from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.spc import calculate_xbar_chart, calculate_p_chart
from app.core.predictor import predict_defect
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation

router = APIRouter(prefix="/quality", tags=["quality"])


class SPCRequest(BaseModel):
    measurements: list[list[float]]
    sigma_multiplier: float = 3.0
    usl: float | None = None
    lsl: float | None = None


class PChartRequest(BaseModel):
    defect_counts: list[int]
    sample_sizes: list[int]
    sigma_multiplier: float = 3.0


class DefectPredictRequest(BaseModel):
    mo_id: str
    operation_type: str | None = None
    work_center_id: str | None = None
    shift: str | None = None
    operator_id: str | None = None
    material_batch: str | None = None
    days_since_maintenance: int | None = None


@router.post("/spc/xbar")
async def spc_xbar(
    req: SPCRequest,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "quality"])),
):
    tenant_id = tenant_ctx.get()
    result = calculate_xbar_chart(req.measurements, req.sigma_multiplier, req.usl, req.lsl)
    return APIResponse(success=True, data={
        "chart_type": "xbar",
        "mean": result.mean,
        "std_dev": result.std_dev,
        "ucl": result.ucl,
        "lcl": result.lcl,
        "points_out_of_control": result.points_out_of_control,
        "runs": result.runs,
        "cp": result.cp,
        "cpk": result.cpk,
        "xai_explanation": XAIExplanation(
            constraints=["control_limits_3sigma", "run_rules", "trend_detection"],
            assumptions=["normal_distribution", "subgroup_size_consistent"],
            confidence_score=0.90,
            contributing_factors={"out_of_control_count": float(len(result.points_out_of_control)), "cpk": result.cpk},
        ).model_dump(),
    }, error=None)


@router.post("/spc/pchart")
async def spc_pchart(
    req: PChartRequest,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "quality"])),
):
    tenant_id = tenant_ctx.get()
    result = calculate_p_chart(req.defect_counts, req.sample_sizes, req.sigma_multiplier)
    return APIResponse(success=True, data={
        "chart_type": "p_chart",
        **result,
        "xai_explanation": XAIExplanation(
            constraints=["binomial_distribution", "control_limits_3sigma"],
            assumptions=["constant_sample_size_approximation"],
            confidence_score=0.88,
            contributing_factors={"p_bar": float(result.get("p_bar", 0)), "out_of_control_count": float(len(result.get("out_of_control", [])))},
        ).model_dump(),
    }, error=None)


@router.post("/predict")
async def predict(
    req: DefectPredictRequest,
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager", "quality"])),
):
    tenant_id = tenant_ctx.get()
    result = predict_defect(
        mo_id=req.mo_id,
        operation_type=req.operation_type,
        work_center_id=req.work_center_id,
        shift=req.shift,
        operator_id=req.operator_id,
        material_batch=req.material_batch,
        days_since_maintenance=req.days_since_maintenance,
    )
    return APIResponse(success=True, data={
        "mo_id": result.mo_id,
        "defect_probability": result.defect_probability,
        "risk_level": result.risk_level,
        "contributing_factors": result.contributing_factors,
        "recommended_actions": result.recommended_actions,
        "xai_explanation": XAIExplanation(
            constraints=["rule_based_defect_factor_multiplication", "risk_threshold_classification"],
            assumptions=["historical_defect_rate_baseline", "independent_factor_multiplication"],
            confidence_score=0.75,
            contributing_factors={"defect_probability": result.defect_probability, "risk_score": {"low": 0.2, "medium": 0.5, "high": 0.8}.get(result.risk_level, 0.0)},
        ).model_dump(),
    }, error=None)