from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.design_intel import (
    DEFAULT_CATALOG,
    DEFAULT_RULES,
    check_design_compliance,
    recommend_materials,
)
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.v8_phase3 import DesignRecommendation, DesignRule, EngineeringMaterial
from ipe_shared.schemas.common import APIResponse

router = APIRouter(tags=["material-design"])


class RecommendRequest(BaseModel):
    required_tensile_mpa: float = Field(gt=0)
    max_cost_per_kg: float | None = None
    analysis_id: UUID | None = None


class ComplianceRequest(BaseModel):
    process_type: str
    parameters: dict[str, float]


async def _ensure_catalog(session: AsyncSession, tenant_id: str) -> list[EngineeringMaterial]:
    existing = (await session.execute(select(EngineeringMaterial).where(EngineeringMaterial.tenant_id == tenant_id))).scalars().all()
    if existing:
        return list(existing)
    created = []
    for item in DEFAULT_CATALOG:
        row = EngineeringMaterial(tenant_id=tenant_id, **item)
        session.add(row)
        created.append(row)
    for rule in DEFAULT_RULES:
        session.add(DesignRule(tenant_id=tenant_id, **rule))
    await session.flush()
    return created


@router.get("/materials")
async def list_materials(
    category: str | None = Query(default=None),
    min_strength: float | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "executive"])),
):
    tenant_id = tenant_ctx.get()
    rows = await _ensure_catalog(session, tenant_id)
    await session.commit()
    out = []
    for m in rows:
        if category and m.category != category:
            continue
        tensile = float((m.properties_jsonb or {}).get("tensile_mpa", 0))
        if min_strength is not None and tensile < min_strength:
            continue
        out.append(
            {
                "id": str(m.id),
                "name": m.name,
                "grade": m.grade,
                "category": m.category,
                "properties": m.properties_jsonb,
                "cost_per_kg": float(m.cost_per_kg or 0),
                "sustainability_score": float(m.sustainability_score or 0),
            }
        )
    return APIResponse(success=True, data={"materials": out, "count": len(out)}, error=None)


@router.get("/materials/{material_id}/alternatives")
async def material_alternatives(
    material_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    base = await session.get(EngineeringMaterial, material_id)
    if not base or str(base.tenant_id) != tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Material not found"})
    tensile = float((base.properties_jsonb or {}).get("tensile_mpa", 200))
    rows = await _ensure_catalog(session, tenant_id)
    mats = [{"id": str(m.id), "name": m.name, "grade": m.grade, "category": m.category, "properties_jsonb": m.properties_jsonb, "cost_per_kg": float(m.cost_per_kg or 0), "sustainability_score": float(m.sustainability_score or 0)} for m in rows if m.id != material_id]
    alts = recommend_materials(mats, required_tensile_mpa=tensile * 0.9, max_cost_per_kg=float(base.cost_per_kg or 999) * 1.2)
    return APIResponse(success=True, data={"base_material": base.name, "alternatives": alts}, error=None)


@router.post("/design/recommend")
async def design_recommend(
    req: RecommendRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    rows = await _ensure_catalog(session, tenant_id)
    mats = [{"id": str(m.id), "name": m.name, "grade": m.grade, "category": m.category, "properties_jsonb": m.properties_jsonb, "cost_per_kg": float(m.cost_per_kg or 0), "sustainability_score": float(m.sustainability_score or 0)} for m in rows]
    ranked = recommend_materials(mats, required_tensile_mpa=req.required_tensile_mpa, max_cost_per_kg=req.max_cost_per_kg)
    for item in ranked[:3]:
        mat_id = UUID(item["id"])
        session.add(
            DesignRecommendation(
                tenant_id=tenant_id,
                analysis_id=req.analysis_id,
                material_id=mat_id,
                score=item["score"],
                rationale=item.get("rationale"),
                alternatives_jsonb=[{"id": x["id"], "name": x["name"], "score": x["score"]} for x in ranked],
            )
        )
    await session.commit()
    return APIResponse(success=True, data={"recommendations": ranked}, error=None)


@router.post("/design/check-compliance")
async def design_check_compliance(
    req: ComplianceRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    await _ensure_catalog(session, tenant_id)
    rules = (await session.execute(select(DesignRule).where(DesignRule.tenant_id == tenant_id))).scalars().all()
    rule_dicts = [
        {
            "process_type": r.process_type,
            "constraint_type": r.constraint_type,
            "parameter_key": r.parameter_key,
            "min_value": float(r.min_value) if r.min_value is not None else None,
            "max_value": float(r.max_value) if r.max_value is not None else None,
            "unit": r.unit,
        }
        for r in rules
    ]
    results = check_design_compliance(rule_dicts, req.process_type, req.parameters)
    passed = all(r["result"] in ("pass", "skip") for r in results)
    await session.commit()
    return APIResponse(success=True, data={"compliant": passed, "checks": results}, error=None)
