"""Phase 4 Premium APIs — intelligence pulse, A8/A11, autonomous overnight."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.core.phase4 import (
    AutonomousRuleEngine,
    CustomerIntelligence,
    FinanceIntelligence,
    build_intelligence_pulse,
)
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/intelligence", tags=["phase4-premium"])
_customer = CustomerIntelligence()
_finance = FinanceIntelligence()
_auto = AutonomousRuleEngine()


def _tenant(x_tenant_id: str | None = None) -> str:
    return str(tenant_ctx.get() or x_tenant_id or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


class CustomerHealthRequest(BaseModel):
    customer_id: str = "CUST-001"
    customer_name: str = "Saudi Electricity Company"
    order_frequency_score: float = 90
    payment_reliability_pct: float = 95
    order_growth_yoy_pct: float = 12
    complaint_count_12m: int = 1
    delivery_otd_pct: float = 88
    sla_otd_pct: float = 95
    annual_revenue: float = 2_500_000


class DelayNoticeRequest(BaseModel):
    customer_name: str
    order_number: str
    product_desc: str
    original_date: str
    revised_date: str
    reason: str = "Production scheduling adjustment"
    contact_name: str = "Ahmed"
    contact_email: str = "planner@startrans.com"


class MOMarginRequest(BaseModel):
    mo_id: str
    revenue: float
    material_cost: float
    labour_cost: float
    overhead: float = 0
    standard_material: float | None = None
    standard_labour: float | None = None
    target_margin_pct: float = 25.0


class DecisionPnLRequest(BaseModel):
    decision: str
    direct_cost: float
    revenue_protected: float = 0
    penalty_avoided: float = 0
    mtd_revenue: float = 0
    mtd_direct_costs: float = 0


class CashFlowRequest(BaseModel):
    opening_balance: float = 342_000
    threshold: float = 250_000
    weeks: list[dict[str, Any]] = Field(default_factory=list)


class AutonomousRequest(BaseModel):
    resolutions: list[dict[str, Any]] = Field(default_factory=list)
    reorder_candidates: list[dict[str, Any]] = Field(default_factory=list)
    batch_candidates: list[dict[str, Any]] = Field(default_factory=list)
    quality_risks: list[dict[str, Any]] = Field(default_factory=list)


class PulseRequest(BaseModel):
    planner_name: str = "Ahmed"
    auto_actions_overnight: int = 3


PHASE4_AGENTS = [
    {"agent_id": "A8", "name": "Customer Intelligence", "module": "M6", "status": "healthy"},
    {"agent_id": "A9", "name": "Procurement Intelligence", "module": "M3", "status": "healthy"},
    {"agent_id": "A10", "name": "Quality Intelligence", "module": "M4", "status": "healthy"},
    {"agent_id": "A11", "name": "Finance Intelligence", "module": "M5", "status": "healthy"},
    {"agent_id": "A12", "name": "Sustainability Intelligence", "module": "M3+M5", "status": "healthy"},
]


@router.get("/pulse")
async def intelligence_pulse(
    planner_name: str = "Ahmed",
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    data = build_intelligence_pulse(tenant_id=_tenant(x_tenant_id), planner_name=planner_name)
    return APIResponse(success=True, data=data, error=None)


@router.get("/agents")
async def phase4_agents():
    return APIResponse(success=True, data={"agents": PHASE4_AGENTS}, error=None)


@router.post("/customer/health")
async def customer_health(req: CustomerHealthRequest):
    return APIResponse(success=True, data=_customer.health(**req.model_dump()), error=None)


@router.post("/customer/delay-notice")
async def customer_delay_notice(req: DelayNoticeRequest):
    return APIResponse(success=True, data=_customer.delay_notice(**req.model_dump()), error=None)


@router.post("/finance/mo-margin")
async def finance_mo_margin(req: MOMarginRequest):
    return APIResponse(success=True, data=_finance.mo_margin(**req.model_dump()), error=None)


@router.post("/finance/decision-pnl")
async def finance_decision_pnl(req: DecisionPnLRequest):
    return APIResponse(success=True, data=_finance.decision_pnl(**req.model_dump()), error=None)


@router.post("/finance/cash-flow")
async def finance_cash_flow(req: CashFlowRequest):
    return APIResponse(
        success=True,
        data=_finance.cash_flow(req.weeks, opening_balance=req.opening_balance, threshold=req.threshold),
        error=None,
    )


@router.post("/autonomous/overnight")
async def autonomous_overnight(req: AutonomousRequest):
    data = _auto.evaluate_overnight(req.model_dump())
    return APIResponse(success=True, data=data, error=None)


@router.get("/modules")
async def list_modules(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID")):
    pulse = build_intelligence_pulse(tenant_id=_tenant(x_tenant_id))
    return APIResponse(success=True, data={"modules": pulse["modules"]}, error=None)
