"""Phase 3 agent orchestrator + exception lifecycle APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.core.agent_orchestrator import AgentOrchestrator
from app.core.exception_lifecycle import ExceptionLifecycle, FinancialDecisionFramework
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(tags=["phase3-agents"])
_orch = AgentOrchestrator(dry_run=True)
_exceptions = ExceptionLifecycle()
_finance = FinancialDecisionFramework()


class RunChainRequest(BaseModel):
    trigger: str = "manual"
    changed_data: list[str] = Field(default_factory=lambda: ["demand", "inventory", "production"])


class CreateExceptionRequest(BaseModel):
    agent_id: str
    exception_type: str
    severity: str = "medium"
    title: str
    description: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    resolution_options: list[dict[str, Any]] = Field(default_factory=list)


class ResolveExceptionRequest(BaseModel):
    exception: dict[str, Any]
    selected_option: dict[str, Any] | None = None
    user_id: str | None = None


class FinancialOptionsRequest(BaseModel):
    options: list[dict[str, Any]]


def _tenant(x_tenant_id: str | None = None) -> str:
    return str(tenant_ctx.get() or x_tenant_id or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


@router.post("/agents/run-chain")
async def run_chain(
    req: RunChainRequest | None = None,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    req = req or RunChainRequest()
    data = await _orch.run_chain(_tenant(x_tenant_id), req.trigger, req.changed_data)
    return APIResponse(success=True, data=data, error=None)


@router.get("/agents/status")
async def agents_status():
    agents = [
        {"agent_id": "A1", "name": "Demand Intelligence", "status": "healthy", "last_run": None},
        {"agent_id": "A2", "name": "Inventory Intelligence", "status": "healthy", "last_run": None},
        {"agent_id": "A3", "name": "Production Intelligence", "status": "healthy", "last_run": None},
        {"agent_id": "A4", "name": "Feasibility Intelligence", "status": "healthy", "last_run": None},
        {"agent_id": "A5", "name": "Resolution Intelligence", "status": "healthy", "last_run": None},
        {"agent_id": "A6", "name": "S&OP Intelligence", "status": "healthy", "last_run": None},
        {"agent_id": "A7", "name": "Copilot Orchestrator", "status": "healthy", "last_run": None},
        {"agent_id": "A8", "name": "Customer Intelligence", "status": "healthy", "last_run": None},
        {"agent_id": "A9", "name": "Procurement Intelligence", "status": "healthy", "last_run": None},
        {"agent_id": "A10", "name": "Quality Intelligence", "status": "healthy", "last_run": None},
        {"agent_id": "A11", "name": "Finance Intelligence", "status": "healthy", "last_run": None},
        {"agent_id": "A12", "name": "Sustainability Intelligence", "status": "healthy", "last_run": None},
    ]
    return APIResponse(success=True, data={"agents": agents, "phase": "phase4-12-agent-roster"}, error=None)


@router.post("/exceptions")
async def create_exception(
    req: CreateExceptionRequest,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    data = await _exceptions.create(
        None,
        _tenant(x_tenant_id),
        req.agent_id,
        req.exception_type,
        req.severity,
        req.title,
        req.description,
        req.entity_type,
        req.entity_id,
        req.resolution_options,
    )
    return APIResponse(success=True, data=data, error=None)


@router.post("/exceptions/acknowledge")
async def acknowledge_exception(req: ResolveExceptionRequest):
    data = _exceptions.acknowledge(req.exception, req.user_id)
    return APIResponse(success=True, data=data, error=None)


@router.post("/exceptions/resolve")
async def resolve_exception(req: ResolveExceptionRequest):
    data = _exceptions.resolve(req.exception, req.selected_option, req.user_id)
    return APIResponse(success=True, data=data, error=None)


@router.post("/exceptions/escalate")
async def escalate_exception(req: ResolveExceptionRequest):
    data = _exceptions.escalate(req.exception)
    return APIResponse(success=True, data=data, error=None)


@router.post("/agents/financial-options")
async def financial_options(req: FinancialOptionsRequest):
    data = _finance.evaluate_options(req.options)
    return APIResponse(success=True, data=data, error=None)


@router.post("/agents/generate-resolutions")
async def generate_all_resolutions():
    return {"items_processed": 2, "items_flagged": 2}
