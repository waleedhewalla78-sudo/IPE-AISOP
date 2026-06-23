"""Drift detection and ROI validation API endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ipe_shared.ml.drift import compute_ks_test, compute_psi
from ipe_shared.ml.shadow_roi import ScheduleComparison, ShadowROIValidator

router = APIRouter(prefix="/ml", tags=["ml-ops"])


class DriftCheckRequest(BaseModel):
    reference: list[float] = Field(..., min_length=10)
    current: list[float] = Field(..., min_length=10)
    model_id: str = "default"


class DriftCheckResponse(BaseModel):
    psi_value: float
    psi_drift_type: str
    ks_value: float
    ks_drift_type: str
    overall_drift: bool


class ROIRequest(BaseModel):
    manual_otd_pct: float = Field(..., ge=0, le=100)
    ai_otd_pct: float = Field(..., ge=0, le=100)
    manual_cost: float = Field(..., gt=0)
    ai_cost: float = Field(..., gt=0)
    manual_utilization: float = Field(..., ge=0, le=100)
    ai_utilization: float = Field(..., ge=0, le=100)
    mo_count: int = Field(..., gt=0)
    period_days: int = 30


class ROIResponse(BaseModel):
    otd_improvement_pct: float
    cost_savings_pct: float
    utilization_gain_pct: float
    annualized_cost_savings: float
    roi_pct: float
    confidence: float
    recommendations: list[str]


_validator = ShadowROIValidator()


@router.post("/drift/check", response_model=DriftCheckResponse)
async def check_drift(body: DriftCheckRequest) -> DriftCheckResponse:
    psi = compute_psi(body.reference, body.current)
    ks = compute_ks_test(body.reference, body.current)
    return DriftCheckResponse(
        psi_value=psi.value,
        psi_drift_type=psi.drift_type.value,
        ks_value=ks.value,
        ks_drift_type=ks.drift_type.value,
        overall_drift=psi.is_drifted or ks.is_drifted,
    )


@router.post("/roi/validate", response_model=ROIResponse)
async def validate_shadow_roi(body: ROIRequest) -> ROIResponse:
    comparison = ScheduleComparison(
        manual_otd_pct=body.manual_otd_pct,
        ai_otd_pct=body.ai_otd_pct,
        manual_cost=body.manual_cost,
        ai_cost=body.ai_cost,
        manual_utilization=body.manual_utilization,
        ai_utilization=body.ai_utilization,
        mo_count=body.mo_count,
        period_days=body.period_days,
    )
    result = _validator.validate(comparison)
    return ROIResponse(
        otd_improvement_pct=result.otd_delta,
        cost_savings_pct=result.comparison.cost_savings_pct,
        utilization_gain_pct=result.comparison.utilization_gain_pct,
        annualized_cost_savings=result.annualized_cost_savings,
        roi_pct=result.roi_pct,
        confidence=result.confidence,
        recommendations=result.recommendations,
    )


@router.get("/roi/cumulative")
async def get_cumulative_roi() -> dict:
    return _validator.get_cumulative_roi()
