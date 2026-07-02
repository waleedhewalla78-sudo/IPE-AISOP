"""Planner Copilot Lite — structured intent responses without Ollama."""

from __future__ import annotations

import os
import re
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select, text, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.planner_intent import PlannerIntent, detect_intent, extract_mo_ref
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.product import Product
from ipe_shared.models.resolution import ResolutionScenario
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/planner-assist", tags=["planner-assist"])

RISK_THRESHOLD = 70.0


class PlannerQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class PlannerQueryResponse(BaseModel):
    intent: str
    answer_markdown: str
    citations: list[dict]
    source: str = "structured"


async def _maybe_nlp_passthrough(query: str, headers: dict) -> dict | None:
    nlp_url = os.getenv("NLP_SVC_URL", "").rstrip("/")
    if not nlp_url:
        return None
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                f"{nlp_url}/api/v1/copilot/query",
                json={"query": query},
                headers=headers,
            )
            if resp.status_code == 200:
                body = resp.json()
                if body.get("success") and body.get("data"):
                    return body["data"]
    except Exception:
        pass
    return None


async def _at_risk_mos(session: AsyncSession, tid: UUID) -> tuple[str, list[dict]]:
    stmt = (
        select(ManufacturingOrder, Product)
        .join(Product, ManufacturingOrder.product_id == Product.id)
        .where(
            ManufacturingOrder.tenant_id == tid,
            ManufacturingOrder.feasibility_score.isnot(None),
            ManufacturingOrder.feasibility_score < RISK_THRESHOLD,
        )
        .order_by(ManufacturingOrder.feasibility_score.asc())
        .limit(10)
    )
    rows = (await session.execute(stmt)).all()
    if not rows:
        return "No manufacturing orders are currently below the 70% feasibility threshold.", []

    lines = ["**At-risk manufacturing orders** (feasibility < 70%):\n"]
    citations = []
    for mo, product in rows:
        score = float(mo.feasibility_score or 0)
        ref = mo.erp_mo_id or str(mo.id)[:8]
        constraint = mo.primary_constraint or "unknown"
        lines.append(f"- **{ref}** — {product.name}: **{score:.0f}%** ({constraint})")
        citations.append({"mo_id": str(mo.id), "erp_mo_id": mo.erp_mo_id, "feasibility_score": score})
    return "\n".join(lines), citations


async def _mo_detail(session: AsyncSession, tid: UUID, query: str) -> tuple[str, list[dict]]:
    ref = extract_mo_ref(query)
    filters = [ManufacturingOrder.tenant_id == tid]
    if ref:
        if re.match(r"^[0-9a-f-]{36}$", ref, re.I):
            filters.append(ManufacturingOrder.id == UUID(ref))
        else:
            filters.append(
                or_(
                    ManufacturingOrder.erp_mo_id.ilike(f"%{ref}%"),
                    func.cast(ManufacturingOrder.id, String).ilike(f"%{ref}%"),
                )
            )
    stmt = (
        select(ManufacturingOrder, Product)
        .join(Product, ManufacturingOrder.product_id == Product.id)
        .where(*filters)
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    if not row:
        return f"No manufacturing order found matching `{ref or query}`.", []

    mo, product = row
    score = float(mo.feasibility_score) if mo.feasibility_score is not None else None
    lines = [
        f"**MO {mo.erp_mo_id or mo.id}** — {product.name}",
        f"- Feasibility: **{score:.0f}%**" if score is not None else "- Feasibility: pending",
        f"- Primary constraint: **{mo.primary_constraint or 'none'}**",
        f"- Status: {mo.status}",
        f"- Planned end: {mo.planned_end.isoformat() if mo.planned_end else 'n/a'}",
    ]
    return "\n".join(lines), [{"mo_id": str(mo.id), "erp_mo_id": mo.erp_mo_id, "feasibility_score": score}]


async def _scenario_list(session: AsyncSession, tid: UUID, query: str) -> tuple[str, list[dict]]:
    ref = extract_mo_ref(query)
    mo_filter = [ResolutionScenario.tenant_id == tid, ResolutionScenario.status == "proposed"]
    if ref:
        mo_stmt = select(ManufacturingOrder.id).where(
            ManufacturingOrder.tenant_id == tid,
            or_(
                ManufacturingOrder.erp_mo_id.ilike(f"%{ref}%"),
                func.cast(ManufacturingOrder.id, String).ilike(f"%{ref}%"),
            ),
        ).limit(1)
        mo_id = (await session.execute(mo_stmt)).scalar_one_or_none()
        if mo_id:
            mo_filter.append(ResolutionScenario.mo_id == mo_id)

    stmt = (
        select(ResolutionScenario, ManufacturingOrder)
        .join(ManufacturingOrder, ResolutionScenario.mo_id == ManufacturingOrder.id)
        .where(*mo_filter)
        .order_by(ResolutionScenario.business_score.desc())
        .limit(8)
    )
    rows = (await session.execute(stmt)).all()
    if not rows:
        return "No proposed resolution scenarios found.", []

    lines = ["**Proposed resolution scenarios:**\n"]
    citations = []
    for scenario, mo in rows:
        ref = mo.erp_mo_id or str(mo.id)[:8]
        score = float(scenario.business_score or 0)
        lines.append(f"- **{scenario.strategy}** on {ref} — score {score:.2f}")
        citations.append({
            "scenario_id": str(scenario.id),
            "mo_id": str(mo.id),
            "strategy": scenario.strategy,
            "business_score": score,
        })
    return "\n".join(lines), citations


async def _sync_status(session: AsyncSession, tid: UUID) -> tuple[str, list[dict]]:
    row = await session.execute(
        text("""
            SELECT started_at, finished_at, status, entity_counts, error_summary
            FROM cdm_sync_run
            WHERE tenant_id = :tid
            ORDER BY started_at DESC
            LIMIT 1
        """),
        {"tid": tid},
    )
    last = row.fetchone()
    if not last:
        return "No Odoo sync runs recorded for this tenant yet.", []

    started, finished, status, counts, err = last
    lines = [
        "**Last Odoo sync**",
        f"- Status: **{status}**",
        f"- Started: {started.isoformat() if started else 'n/a'}",
        f"- Finished: {finished.isoformat() if finished else 'in progress'}",
    ]
    if counts:
        lines.append(f"- Entities: `{counts}`")
    if err:
        lines.append(f"- Errors: {err}")
    return "\n".join(lines), [{"sync_status": status, "started_at": started.isoformat() if started else None}]


async def _schedule_summary(session: AsyncSession, tid: UUID) -> tuple[str, list[dict]]:
    stmt = (
        select(WorkCenter)
        .where(WorkCenter.tenant_id == tid)
        .order_by(WorkCenter.oee.desc().nullslast())
        .limit(6)
    )
    centers = (await session.execute(stmt)).scalars().all()
    if not centers:
        return "No work center capacity data available.", []

    lines = ["**Schedule / capacity summary** (by OEE proxy):\n"]
    citations = []
    for wc in centers:
        util = round(float(wc.oee or 0.85) * 100, 1)
        flag = " ⚠️" if util > 85 else ""
        lines.append(f"- **{wc.name}**: {util:.0f}% load proxy{flag}")
        citations.append({"work_center_id": str(wc.id), "utilization_pct": util})
    return "\n".join(lines), citations


@router.post("/query")
async def planner_query(
    req: PlannerQueryRequest,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(require_roles(["admin", "planner", "manager", "viewer"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)
    intent = detect_intent(req.query)

    # Optional hybrid passthrough
    nlp_headers = {"X-Tenant-ID": tenant_id}
    nlp_data = await _maybe_nlp_passthrough(req.query, nlp_headers)
    if nlp_data:
        return APIResponse(
            success=True,
            data={
                "intent": nlp_data.get("intent", intent.value),
                "answer_markdown": nlp_data.get("answer", nlp_data.get("answer_markdown", "")),
                "citations": nlp_data.get("citations", []),
                "source": "nlp-svc",
            },
            error=None,
        )

    if intent == PlannerIntent.MO_DETAIL:
        answer, citations = await _mo_detail(session, tid, req.query)
    elif intent == PlannerIntent.SCENARIO_LIST:
        answer, citations = await _scenario_list(session, tid, req.query)
    elif intent == PlannerIntent.SYNC_STATUS:
        answer, citations = await _sync_status(session, tid)
    elif intent == PlannerIntent.SCHEDULE_SUMMARY:
        answer, citations = await _schedule_summary(session, tid)
    else:
        answer, citations = await _at_risk_mos(session, tid)

    return APIResponse(
        success=True,
        data={
            "intent": intent.value,
            "answer_markdown": answer,
            "citations": citations,
            "source": "structured",
        },
        error=None,
    )
