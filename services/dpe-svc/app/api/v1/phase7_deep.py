"""Phase 7 Deep Planning & Operations Intelligence APIs.

Deepens 5 disciplines on the A1-A17 platform under the existing planning-command
umbrella. Live-integration-dependent capabilities (IoT/MES shop-floor telemetry)
are SCAFFOLD/STUB and clearly flagged (PH1-02 OPEN).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header
from pydantic import BaseModel

from app.core.phase7 import (
    AndonBoard,
    analyze_make_or_buy,
    build_consensus,
    build_demand_shaping,
    build_financial_sop,
    build_gemba,
    build_horizons,
    build_kpi_tree,
    build_oee_programme,
    build_planning_calendar,
    build_standard_work,
    cascade_plan,
    decompose_demand,
    forecast_npi,
    optimize_portfolio,
    optimize_setup_sequence,
    plan_campaign,
    plan_labour,
    recalc_rolling_sop,
    schedule_multi_resource,
)
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/planning-command", tags=["phase7-deep-planning"])

_andon = AndonBoard()


def _tenant(x_tenant_id: str | None = None) -> str:
    return str(tenant_ctx.get() or x_tenant_id or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


def _ok(data: Any) -> APIResponse:
    return APIResponse(success=True, data=data, error=None)


PHASE7_DISCIPLINES = [
    {"id": "horizons", "section": "1", "name": "Multi-Horizon Planning"},
    {"id": "sop", "section": "2", "name": "S&OP Deep"},
    {"id": "demand", "section": "3", "name": "Demand Intelligence Deep"},
    {"id": "production", "section": "4", "name": "Production Intelligence Deep"},
    {"id": "operations", "section": "5", "name": "Operations Intelligence Deep"},
    {"id": "calendar", "section": "6", "name": "Integrated Planning Calendar"},
]


# ---- §1 Multi-Horizon Planning ---------------------------------------------


class CascadeRequest(BaseModel):
    direction: str = "down"
    driver: str = "We will grow DT250 revenue by 20% in 2027"
    growth_pct: float = 20.0
    product: str = "DT250"
    constraint_work_centre: str = "Winding"
    capacity_gap_hours: float = 800.0
    capex_usd: float = 180_000.0
    roi_months: float = 14.0


@router.get("/phase7/disciplines")
async def phase7_disciplines():
    return _ok({"phase": "7", "disciplines": PHASE7_DISCIPLINES})


@router.get("/horizons")
async def horizons(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    _tenant(x_tenant_id)
    return _ok(build_horizons())


@router.post("/horizons/cascade")
async def horizons_cascade(req: CascadeRequest):
    return _ok(cascade_plan(**req.model_dump()))


# ---- §2 S&OP Deep -----------------------------------------------------------


class FinancialSopRequest(BaseModel):
    product: str = "DT250"
    unit_price: float = 85_000.0
    material_cost_per_unit: float = 58_000.0
    labour_cost_per_unit: float = 5_040.0
    overhead_per_unit: float = 3_360.0
    periods: list[dict[str, Any]] | None = None
    margin_floor_pct: float = 20.0


class RollingSopRequest(BaseModel):
    events: list[dict[str, Any]] | None = None
    baseline_consensus: float = 24.0


class DemandShapingRequest(BaseModel):
    constraint_work_centre: str = "Winding"
    constrained_month: str = "October"
    shortfall_units: int = 2
    lost_revenue_usd: float = 170_000.0
    high_product: str = "DT250"
    high_wc_hours: float = 6.0
    alt_product: str = "DT100"
    alt_wc_hours: float = 4.0


class PortfolioRequest(BaseModel):
    constraint_work_centre: str = "Winding"
    products: list[dict[str, Any]] | None = None
    horizon: str = "Q4 2026"


@router.post("/sop/financial")
async def sop_financial(req: FinancialSopRequest):
    return _ok(build_financial_sop(**req.model_dump()))


@router.post("/sop/rolling")
async def sop_rolling(req: RollingSopRequest):
    return _ok(recalc_rolling_sop(**req.model_dump()))


@router.post("/sop/demand-shaping")
async def sop_demand_shaping(req: DemandShapingRequest):
    return _ok(build_demand_shaping(**req.model_dump()))


@router.post("/sop/portfolio")
async def sop_portfolio(req: PortfolioRequest):
    return _ok(optimize_portfolio(**req.model_dump()))


# ---- §3 Demand Deep ---------------------------------------------------------


class DecompRequest(BaseModel):
    product: str = "FG-DT100"
    month: int = 10
    base: float = 20.0
    trend_per_month: float = 2.0
    months_from_base: float = 1.0
    promo_active: bool = False
    promo_price_change_pct: float = -3.0
    price_elasticity: float = -1.3
    event_units: float = 0.0
    noise_sigma: float = 3.0


class CollaborationRequest(BaseModel):
    product: str = "FG-DT100"
    period: str = "October"
    statistical: float = 23.0
    inputs: list[dict[str, Any]] | None = None
    weights: dict[str, float] | None = None
    disagreement_threshold_pct: float = 15.0


class NpiRequest(BaseModel):
    product: str = "DT100-V2"
    reference_product: str = "DT100"
    reference_ramp: list[float] | None = None
    mature_demand: float = 15.0
    cannibalization_pct: float = 30.0
    reference_current_demand: float = 24.0
    net_new_units: float = 5.0
    market_total_annual: float = 500.0
    market_share_pct: float = 15.0
    addressable_pct: float = 60.0
    months: int = 12


@router.post("/demand/decompose")
async def demand_decompose(req: DecompRequest):
    return _ok(decompose_demand(**req.model_dump()))


@router.post("/demand/collaborate")
async def demand_collaborate(req: CollaborationRequest):
    return _ok(build_consensus(**req.model_dump()))


@router.post("/demand/npi")
async def demand_npi(req: NpiRequest):
    return _ok(forecast_npi(**req.model_dump()))


# ---- §4 Production Deep -----------------------------------------------------


class SetupSequenceRequest(BaseModel):
    jobs: list[str] | None = None
    setup_matrix: dict[str, dict[str, int]] | None = None


class MultiResourceRequest(BaseModel):
    mo_id: str = "MO-ST-004"
    product: str = "DT250"
    resources: list[dict[str, Any]] | None = None


class CampaignRequest(BaseModel):
    work_centre: str = "Winding"
    families: list[dict[str, Any]] | None = None


class LabourRequest(BaseModel):
    week: str = "W31"
    operators: list[dict[str, Any]] | None = None
    critical_skill: str = "Winding"
    critical_cert: str = "PT500"


class MakeOrBuyRequest(BaseModel):
    part: str = "SA-HVW"
    make_material_usd: float = 3_200.0
    make_labour_usd: float = 850.0
    make_overhead_usd: float = 420.0
    make_hours: float = 6.0
    buy_price_usd: float = 5_100.0
    current_utilisation_pct: float = 84.0
    bottleneck_threshold_pct: float = 90.0
    displaced_product: str = "DT100"
    displaced_margin_usd: float = 12_600.0


@router.post("/production/setup-sequence")
async def production_setup_sequence(req: SetupSequenceRequest):
    return _ok(optimize_setup_sequence(**req.model_dump()))


@router.post("/production/multi-resource")
async def production_multi_resource(req: MultiResourceRequest):
    return _ok(schedule_multi_resource(**req.model_dump()))


@router.post("/production/campaign")
async def production_campaign(req: CampaignRequest):
    return _ok(plan_campaign(**req.model_dump()))


@router.post("/production/labour")
async def production_labour(req: LabourRequest):
    return _ok(plan_labour(**req.model_dump()))


@router.post("/production/make-or-buy")
async def production_make_or_buy(req: MakeOrBuyRequest):
    return _ok(analyze_make_or_buy(**req.model_dump()))


# ---- §5 Operations Deep -----------------------------------------------------


class OeeRequest(BaseModel):
    work_centre: str = "Winding"
    availability_pct: float = 88.0
    performance_pct: float = 92.0
    quality_pct: float = 94.0
    target_availability_pct: float = 90.0
    target_performance_pct: float = 94.0
    target_quality_pct: float = 96.0


class AndonTriggerRequest(BaseModel):
    color: str = "yellow"
    work_centre: str = "WC-WND"
    reported_by: str = "Mohamed"
    message: str = "Wire tensioner needs adjustment"
    impact: str | None = None


class AndonResolveRequest(BaseModel):
    resolution: str


class StandardWorkRequest(BaseModel):
    operation: str = "DT250 Winding Operation"
    steps: list[dict[str, Any]] | None = None
    actuals: dict[int, float] | None = None


@router.post("/operations/oee-programme")
async def operations_oee(req: OeeRequest):
    return _ok(build_oee_programme(**req.model_dump()))


@router.get("/operations/gemba")
async def operations_gemba():
    return _ok(build_gemba())


@router.get("/operations/andon")
async def operations_andon_board():
    return _ok(_andon.board())


@router.post("/operations/andon")
async def operations_andon_trigger(req: AndonTriggerRequest):
    return _ok(_andon.trigger(**req.model_dump()))


@router.post("/operations/andon/{alert_id}/resolve")
async def operations_andon_resolve(alert_id: str, req: AndonResolveRequest):
    item = _andon.resolve(alert_id, req.resolution)
    if not item:
        return APIResponse(success=False, data=None, error="andon_alert_not_found")
    return _ok(item)


@router.get("/operations/kpi-tree")
async def operations_kpi_tree():
    return _ok(build_kpi_tree())


@router.post("/operations/standard-work")
async def operations_standard_work(req: StandardWorkRequest):
    return _ok(build_standard_work(**req.model_dump()))


# ---- §6 Integrated Planning Calendar ---------------------------------------


@router.get("/calendar")
async def planning_calendar(cadence: str | None = None):
    return _ok(build_planning_calendar(cadence=cadence))
