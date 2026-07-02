from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.procurement_intel import (
    DEFAULT_SPEND,
    aggregate_spend,
    check_supplier_compliance,
    score_supplier_risk,
)
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.supplier import Supplier
from ipe_shared.models.v8_phase3 import ProcurementComplianceCheck, ProcurementSpend
from ipe_shared.schemas.common import APIResponse

router = APIRouter(tags=["procurement"])


class ComplianceCheckRequest(BaseModel):
    supplier_id: UUID | None = None


async def _ensure_spend(session: AsyncSession, tenant_id: str) -> list[ProcurementSpend]:
    existing = (await session.execute(select(ProcurementSpend).where(ProcurementSpend.tenant_id == tenant_id))).scalars().all()
    if existing:
        return list(existing)
    created = []
    for item in DEFAULT_SPEND:
        row = ProcurementSpend(tenant_id=tenant_id, **item)
        session.add(row)
        created.append(row)
    await session.flush()
    return created


@router.get("/suppliers")
async def list_suppliers(
    category: str | None = Query(default=None),
    risk_tier: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive", "procurement"])),
):
    tenant_id = tenant_ctx.get()
    q = select(Supplier).where(Supplier.tenant_id == tenant_id)
    if category:
        q = q.where(Supplier.category == category)
    if risk_tier:
        q = q.where(Supplier.risk_tier == risk_tier)
    rows = (await session.execute(q)).scalars().all()
    out = []
    for s in rows:
        sup = {
            "id": str(s.id),
            "name": s.name,
            "category": s.category,
            "esg_score": float(s.esg_score or 70),
            "risk_tier": s.risk_tier or "medium",
            "reliability_score": float(s.reliability_score or 0.7),
        }
        out.append({**sup, "risk": score_supplier_risk(sup)})
    return APIResponse(success=True, data={"suppliers": out, "count": len(out)}, error=None)


@router.get("/procurement/spend")
async def procurement_spend(
    period: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "procurement"])),
):
    tenant_id = tenant_ctx.get()
    rows = await _ensure_spend(session, tenant_id)
    await session.commit()
    spend_rows = [
        {"category": r.category, "amount": float(r.amount), "period": r.period, "supplier_id": str(r.supplier_id) if r.supplier_id else None}
        for r in rows
        if period is None or r.period == period
    ]
    summary = aggregate_spend(spend_rows)
    return APIResponse(success=True, data={"spend": spend_rows, "summary": summary}, error=None)


@router.post("/procurement/compliance/check")
async def procurement_compliance_check(
    req: ComplianceCheckRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "procurement"])),
):
    tenant_id = tenant_ctx.get()
    q = select(Supplier).where(Supplier.tenant_id == tenant_id)
    if req.supplier_id:
        q = q.where(Supplier.id == req.supplier_id)
    suppliers = (await session.execute(q)).scalars().all()
    if not suppliers:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "No suppliers found"})

    all_checks = []
    for s in suppliers:
        sup = {
            "id": str(s.id),
            "name": s.name,
            "esg_score": float(s.esg_score or 70),
            "risk_tier": s.risk_tier or "medium",
            "reliability_score": float(s.reliability_score or 0.7),
        }
        checks = check_supplier_compliance(sup)
        for chk in checks:
            session.add(
                ProcurementComplianceCheck(
                    tenant_id=tenant_id,
                    supplier_id=s.id,
                    rule_id=chk["rule_id"],
                    result=chk["result"],
                    evidence_jsonb={"value": chk.get("value"), "message": chk.get("message")},
                )
            )
        passed = all(c["result"] in ("pass", "skip") for c in checks)
        all_checks.append({"supplier_id": str(s.id), "supplier_name": s.name, "compliant": passed, "checks": checks})
    await session.commit()
    overall = all(c["compliant"] for c in all_checks)
    return APIResponse(success=True, data={"compliant": overall, "suppliers": all_checks}, error=None)
