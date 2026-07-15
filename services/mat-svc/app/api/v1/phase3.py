"""Phase 3 material endpoints — predictive stockout + supplier scoring."""

from __future__ import annotations

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.core.predictive_stockout import PredictiveStockout, SupplierReliabilityScorer
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/material", tags=["material-phase3"])
_stockout = PredictiveStockout()
_supplier = SupplierReliabilityScorer()


class StockoutRequest(BaseModel):
    product_code: str
    on_hand: float
    avg_daily_consumption: float
    avg_lead_time_days: float
    lead_time_variability_days: float = 2.0
    expedite_cost: float = 800.0
    stockout_penalty: float = 12400.0


class SupplierScoreRequest(BaseModel):
    supplier_name: str
    on_time_pct: float
    quality_rejection_pct: float = 0
    lead_time_trend: str = "stable"
    concentration_pct: float = 0
    sample_size: int = 0


@router.post("/stockout/predict")
async def predict_stockout(req: StockoutRequest):
    data = _stockout.predict(**req.model_dump())
    return APIResponse(success=True, data=data, error=None)


@router.post("/suppliers/score")
async def score_supplier(req: SupplierScoreRequest | None = None):
    req = req or SupplierScoreRequest(
        supplier_name="Cairo Copper",
        on_time_pct=68,
        quality_rejection_pct=3,
        lead_time_trend="worsening",
        concentration_pct=100,
        sample_size=12,
    )
    data = _supplier.score(**req.model_dump())
    return APIResponse(success=True, data=data, error=None)


@router.get("/suppliers/scorecard")
async def supplier_scorecard():
    samples = [
        _supplier.score("Cairo Copper", 68, 3, "worsening", 100, 12),
        _supplier.score("Shanghai Steel", 91, 1, "stable", 45, 20),
    ]
    return APIResponse(success=True, data={"suppliers": samples}, error=None)
