"""Phase 8 Wave 1 APIs — Ollama status, write-back safety, A18-A20 stubs, Excel exports."""

from __future__ import annotations

import csv
import io
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.phase8 import (
    PHASE8_AGENT_CATALOG,
    a18_multi_site_split,
    a19_learning_retrain_stub,
    a20_exception_monitor_stub,
    approve_write_back,
    feasibility_explanation,
    list_write_backs,
    propose_write_back,
    resolution_narrative,
)
from ipe_shared.llm.ollama_client import get_ollama_client
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.roles import AgentRoleContext
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/phase8", tags=["phase8-production"])


def _tenant(x_tenant_id: str | None = None) -> str:
    return str(tenant_ctx.get() or x_tenant_id or "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")


class WriteBackRequest(BaseModel):
    entity_type: str = "mrp.production"
    entity_id: str
    field_name: str | None = "date_planned_start"
    old_value: str | None = None
    new_value: str
    action: str = "update"
    requested_by: str = "planner"
    user_role: str = "supervisor"
    financial_impact: float = 0.0
    dry_run: bool = True
    payload: dict[str, Any] = Field(default_factory=dict)


class ApproveWriteBackRequest(BaseModel):
    approved_by: str = "manager"
    user_role: str = "manager"
    execute: bool = False


class RoleCheckRequest(BaseModel):
    user_role: str
    action: str = "approve_resolution"
    financial_impact: float = 0.0
    agent_id: str = "A5"


class NarrativeRequest(BaseModel):
    mo_id: str = "MO-ST-004"
    gate_scores: dict[str, float] = Field(
        default_factory=lambda: {"material": 62.0, "capacity": 48.0, "labor": 80.0}
    )
    scenarios: list[dict[str, Any]] = Field(default_factory=list)
    user_role: str = "supervisor"
    locale: str = "en"


class MultiSiteRequest(BaseModel):
    demand_qty: float = 1000.0
    plant_capacities: dict[str, float] = Field(
        default_factory=lambda: {"PLANT-A": 600.0, "PLANT-B": 400.0}
    )
    user_role: str = "manager"


@router.get("/ai-status")
async def ai_status():
    """Ollama health + amber banner flag for UI."""
    health = get_ollama_client().check_health()
    return APIResponse(success=True, data=health.to_api_flag())


@router.get("/agents")
async def phase8_agents():
    return APIResponse(
        success=True,
        data={
            "catalog": PHASE8_AGENT_CATALOG,
            "platform_agents": "A1-A17 ENG COMPLETE (prior phases)",
            "note": "A18-A20 are Wave 8A stubs; full behaviour in 8B+",
        },
    )


@router.post("/role-check")
async def role_check(body: RoleCheckRequest):
    ctx = AgentRoleContext.get_context(body.user_role, body.agent_id)
    allowed = AgentRoleContext.can_execute(body.user_role, body.action, body.financial_impact)
    return APIResponse(
        success=True,
        data={
            "allowed": allowed,
            "context": ctx,
            "escalation_required": AgentRoleContext.escalation_required(
                body.user_role, body.financial_impact
            ),
        },
    )


@router.post("/write-back")
async def write_back_propose(body: WriteBackRequest):
    entry = propose_write_back(
        tenant_id=_tenant(),
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        field_name=body.field_name,
        old_value=body.old_value,
        new_value=body.new_value,
        action=body.action,
        requested_by=body.requested_by,
        user_role=body.user_role,
        financial_impact=body.financial_impact,
        dry_run=body.dry_run,
        payload=body.payload,
    )
    return APIResponse(success=True, data=entry)


@router.post("/write-back/{entry_id}/approve")
async def write_back_approve(entry_id: str, body: ApproveWriteBackRequest):
    result = approve_write_back(
        entry_id,
        approved_by=body.approved_by,
        user_role=body.user_role,
        execute=body.execute,
    )
    ok = "error" not in result
    return APIResponse(success=ok, data=result)


@router.get("/write-back")
async def write_back_list():
    return APIResponse(success=True, data={"items": list_write_backs(_tenant())})


@router.post("/narratives/feasibility")
async def narrative_feasibility(body: NarrativeRequest):
    return APIResponse(
        success=True,
        data=feasibility_explanation(
            body.mo_id,
            body.gate_scores,
            user_role=body.user_role,
            locale=body.locale,
        ),
    )


@router.post("/narratives/resolution")
async def narrative_resolution(body: NarrativeRequest):
    scenarios = body.scenarios or [
        {"option": "A", "cost_impact": 0, "margin": 28.0},
        {"option": "B", "cost_impact": 1800, "margin": 27.4},
    ]
    return APIResponse(
        success=True,
        data=resolution_narrative(
            body.mo_id,
            scenarios,
            user_role=body.user_role,
            locale=body.locale,
        ),
    )


@router.post("/agents/a18/split")
async def agent_a18(body: MultiSiteRequest):
    return APIResponse(
        success=True,
        data=a18_multi_site_split(
            body.demand_qty, body.plant_capacities, user_role=body.user_role
        ),
    )


@router.post("/agents/a19/retrain")
async def agent_a19(model_name: str = Query(default="feasibility_scorer"), user_role: str = "manager"):
    return APIResponse(success=True, data=a19_learning_retrain_stub(model_name, user_role=user_role))


@router.get("/agents/a20/monitor")
async def agent_a20(open_exceptions: int = 0, user_role: str = "supervisor"):
    return APIResponse(
        success=True,
        data=a20_exception_monitor_stub(open_exceptions, user_role=user_role),
    )


@router.get("/export/risk-queue.csv")
async def export_risk_queue(
    rows: str = Query(
        default="",
        description="Optional JSON-lines omitted; returns template columns when empty",
    ),
):
    """Excel-friendly CSV export for Control Tower risk queue."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "mo_id",
            "product",
            "customer",
            "feasibility_score",
            "primary_constraint",
            "status",
        ]
    )
    # Demo rows when no live queue injected — honest template export
    writer.writerow(["MO-ST-001", "FG-DT100", "CUST-SEC", "72", "capacity", "at_risk"])
    writer.writerow(["MO-ST-004", "FG-DT250", "CUST-SEC", "48", "capacity", "critical"])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="risk_queue.csv"'},
    )


@router.get("/export/mps.csv")
async def export_mps():
    """Excel-friendly CSV export for MPS period schedule."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["product_id", "period", "demand", "supply", "projected_on_hand"])
    writer.writerow(["FG-DT100", "2026-W29", "120", "100", "20"])
    writer.writerow(["FG-DT100", "2026-W30", "110", "130", "40"])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="mps_export.csv"'},
    )
