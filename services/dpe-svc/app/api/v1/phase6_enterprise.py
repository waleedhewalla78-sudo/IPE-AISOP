"""Phase 6 Enterprise Agentic Platform APIs — agents A13-A17, modules M7-M9.

Live-integration-dependent capabilities (Odoo Accounting, market data, IoT,
Odoo write-back) are SCAFFOLD/MOCK and clearly flagged in responses — PH1-02
remains OPEN.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.phase6 import (
    AnalyticsIntelligence,
    CommercialIntelligence,
    CrossFunctionalOrchestrator,
    OdooAccountingConnector,
    ProcurementExecution,
    ShopFloorIntelligence,
)
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/enterprise", tags=["phase6-enterprise"])

_commercial = CommercialIntelligence()
_analytics = AnalyticsIntelligence()
_procurement = ProcurementExecution()
_shopfloor = ShopFloorIntelligence()
_orchestrator = CrossFunctionalOrchestrator()
_accounting = OdooAccountingConnector()


def _tenant(x_tenant_id: str | None = None) -> str:
    return str(tenant_ctx.get() or x_tenant_id or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


PHASE6_AGENTS = [
    {
        "agent_id": "A13",
        "name": "Commercial Intelligence",
        "module": "M8",
        "phase": "6A",
        "status": "healthy",
    },
    {
        "agent_id": "A14",
        "name": "Analytics Intelligence",
        "module": "M7",
        "phase": "6A",
        "status": "healthy",
    },
    {
        "agent_id": "A15",
        "name": "Procurement Execution",
        "module": "M9",
        "phase": "6B",
        "status": "healthy",
    },
    {
        "agent_id": "A16",
        "name": "Shop Floor Intelligence",
        "module": "M9",
        "phase": "6B",
        "status": "healthy",
    },
    {
        "agent_id": "A17",
        "name": "Cross-Functional Orchestrator",
        "module": "meta",
        "phase": "6C",
        "status": "healthy",
    },
]


# ---- Request models ---------------------------------------------------------


class PricingRequest(BaseModel):
    product_id: str = "DT250"
    customer_id: str = "CUST-SEC"
    customer_tier: str = "A"
    list_price: float = 85_000.0
    unit_cost: float = 64_400.0
    quantity: int = 10
    competitive_pressure: str = "medium"
    margin_floor_pct: float = 20.0
    planner_discount_authority_pct: float = 10.0
    last_order_price: float | None = 79_500.0


class DealRequest(BaseModel):
    order_id: str = "SO-2026-0289"
    revenue: float = 782_000.0
    material_cost: float = 498_000.0
    labour_cost: float = 62_000.0
    overhead: float = 41_000.0
    logistics_cost: float = 18_000.0
    sales_cost: float = 15_000.0
    target_margin_pct: float = 25.0
    strategic_customer: bool = True


class ContractRequest(BaseModel):
    contract_id: str = "SEC-FRAMEWORK-2026"
    customer_name: str = "Saudi Electricity"
    annual_volume_commitment: int = 40
    ytd_delivered: int = 28
    agreed_price: float = 79_500.0
    current_quote_price: float = 78_200.0
    delivery_sla_pct: float = 95.0
    ytd_otd_pct: float = 88.0


class SeriesRequest(BaseModel):
    """Optional named series for analytics; empty → representative demo data."""

    demand_series: list[float] | None = None
    copper_cost_series: list[float] | None = None
    oee_series: list[float] | None = None
    throughput_series: list[float] | None = None
    cash_cycle_series: list[float] | None = None
    demand_by_sku: dict[str, list[float]] | None = None
    margin_series: list[float] | None = None


class TrendRequest(BaseModel):
    series: list[float] = Field(default_factory=lambda: [175, 181, 186, 190, 193, 196])
    label: str = "series"
    z_threshold: float = 2.0


class ThreeWayMatchRequest(BaseModel):
    po_id: str = "PO-2026-0451"
    invoice_id: str = "INV-CAIRO-8842"
    lines: list[dict[str, Any]] | None = None
    qty_tolerance_pct: float = 2.0
    price_tolerance_pct: float = 3.0
    auto_approve_ceiling: float = 50_000.0


class ReceiptRequest(BaseModel):
    po_id: str = "PO-2026-0451"
    material_id: str = "RM-CW25"
    ordered_qty: float = 200
    received_qty: float = 200
    inspection_passed: bool = True


class WorkInstructionsRequest(BaseModel):
    mo_id: str = "MO-ST-004"
    product_id: str = "FG-DT250"
    routing: list[dict[str, Any]] | None = None


class TimeTrackRequest(BaseModel):
    mo_id: str = "MO-ST-004"
    operation_seq: int = 20
    operator: str = "Mohamed"
    std_minutes: float = 180.0
    actual_minutes: float = 205.0


class ProgressRequest(BaseModel):
    mo_id: str = "MO-ST-004"
    operations: list[dict[str, Any]] | None = None


class ConflictRecommendation(BaseModel):
    agent_id: str
    action: str
    impacts: dict[str, float] = Field(default_factory=dict)
    direct_cost: float = 0.0
    requires_human_approval: bool = False
    approval_role: str | None = None


class ConflictRequest(BaseModel):
    recommendations: list[ConflictRecommendation] = Field(default_factory=list)
    reversal_window_hours: int = 4


class PolicyRequest(BaseModel):
    customer_tier: str = "A"
    order_margin_pct: float = 24.0
    capacity_conflict: bool = False
    committed_po_value: float = 300_000.0
    cash_reserves: float = 1_240_000.0
    max_supplier_share_pct: float = 60.0
    margin_floor_pct: float = 15.0
    strategic_customer: bool = True
    board_approved: bool = False
    carbon_delta_pct: float = -6.0
    defect_probability_pct: float = 5.0


class CascadeRequest(BaseModel):
    type: str = "demand_change"
    product_id: str = "FG-DT100"
    delta_units: float = 38


class OrchestrateATPRequest(BaseModel):
    order_id: str = "SO-2026-0289"
    product_id: str = "FG-DT250"
    customer_id: str = "CUST-SEC"
    customer_tier: str = "A"
    qty: float = 50
    requested_date: str = "2026-08-10"
    inventory_available: float = 12
    capacity_available_hrs: float = 95
    hours_per_unit: float = 2.5
    unit_cost: float = 64_400.0
    list_price: float = 85_000.0
    material_lead_days: int = 8
    expedite_cost: float = 2_400.0
    penalty_avoided: float = 6_000.0
    margin_floor_pct: float = 15.0
    defect_probability_pct: float = 5.0
    strategic_customer: bool = True


# ---- Roster + integration status --------------------------------------------


@router.get("/agents")
async def enterprise_agents():
    return APIResponse(success=True, data={"agents": PHASE6_AGENTS}, error=None)


@router.get("/integrations/status")
async def integrations_status():
    return APIResponse(
        success=True,
        data={
            "odoo_accounting": _accounting.status(),
            "market_data": {"integration": "market_data", "live": False, "blocker": "PH1-02 OPEN"},
            "iot_shop_floor": {
                "integration": "iot_shop_floor",
                "live": False,
                "blocker": "IoT STUB",
            },
        },
        error=None,
    )


# ---- M8 Commercial Command (A13) --------------------------------------------


@router.post("/commercial/pricing")
async def commercial_pricing(req: PricingRequest):
    return APIResponse(success=True, data=_commercial.price(**req.model_dump()), error=None)


@router.post("/commercial/deal-profitability")
async def commercial_deal(req: DealRequest):
    return APIResponse(success=True, data=_commercial.deal(**req.model_dump()), error=None)


@router.post("/commercial/contract-compliance")
async def commercial_contract(req: ContractRequest):
    return APIResponse(success=True, data=_commercial.contract(**req.model_dump()), error=None)


# ---- M7 Analytics Command (A14) ---------------------------------------------


@router.post("/analytics/insights")
async def analytics_insights(req: SeriesRequest | None = None):
    payload = {k: v for k, v in (req.model_dump() if req else {}).items() if v is not None}
    return APIResponse(success=True, data=_analytics.insights(payload), error=None)


@router.post("/analytics/predictions")
async def analytics_predictions(req: SeriesRequest | None = None):
    payload = {k: v for k, v in (req.model_dump() if req else {}).items() if v is not None}
    return APIResponse(success=True, data=_analytics.predictions(payload), error=None)


@router.post("/analytics/trend")
async def analytics_trend(req: TrendRequest):
    return APIResponse(
        success=True, data=_analytics.trend(req.series, label=req.label), error=None
    )


@router.post("/analytics/anomaly")
async def analytics_anomaly(req: TrendRequest):
    return APIResponse(
        success=True,
        data=_analytics.anomaly(req.series, label=req.label, z_threshold=req.z_threshold),
        error=None,
    )


# ---- M9 Procurement + Shop Floor (A15/A16) ----------------------------------


@router.post("/procurement/three-way-match")
async def procurement_match(req: ThreeWayMatchRequest):
    return APIResponse(success=True, data=_procurement.match(**req.model_dump()), error=None)


@router.post("/procurement/receipt")
async def procurement_receipt(req: ReceiptRequest):
    return APIResponse(success=True, data=_procurement.receipt(**req.model_dump()), error=None)


@router.post("/shop-floor/work-instructions")
async def shop_floor_instructions(req: WorkInstructionsRequest):
    return APIResponse(success=True, data=_shopfloor.instructions(**req.model_dump()), error=None)


@router.post("/shop-floor/time-track")
async def shop_floor_time(req: TimeTrackRequest):
    return APIResponse(success=True, data=_shopfloor.time(**req.model_dump()), error=None)


@router.post("/shop-floor/progress")
async def shop_floor_progress(req: ProgressRequest):
    return APIResponse(success=True, data=_shopfloor.progress(**req.model_dump()), error=None)


# ---- A17 Cross-Functional Orchestrator (6C) ---------------------------------


@router.post("/orchestrator/resolve-conflict")
async def orchestrator_resolve(req: ConflictRequest):
    from app.core.phase6 import AgentRecommendation

    recs = [AgentRecommendation(**r.model_dump()) for r in req.recommendations]
    data = _orchestrator.resolve_conflict(recs, reversal_window_hours=req.reversal_window_hours)
    return APIResponse(success=True, data=data, error=None)


@router.post("/orchestrator/enforce-policies")
async def orchestrator_policies(req: PolicyRequest):
    return APIResponse(
        success=True, data=_orchestrator.enforce_policies(req.model_dump()), error=None
    )


@router.post("/orchestrator/cascade")
async def orchestrator_cascade(req: CascadeRequest):
    return APIResponse(
        success=True, data=_orchestrator.cascade_event(req.model_dump()), error=None
    )


@router.post("/orchestrator/atp")
async def orchestrator_atp(req: OrchestrateATPRequest):
    return APIResponse(
        success=True, data=_orchestrator.orchestrate_atp(**req.model_dump()), error=None
    )
