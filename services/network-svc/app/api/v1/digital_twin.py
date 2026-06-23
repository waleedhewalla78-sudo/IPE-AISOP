from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation

from app.core.digital_twin import DigitalTwinService

router = APIRouter()


class DisruptionRequest(BaseModel):
    disruption_type: str
    source_id: str
    delay_days: float = 7.0


@router.get("/health")
async def health():
    from datetime import UTC, datetime
    return {"status": "ok", "service": "network-svc", "version": "0.1.0", "timestamp": datetime.now(UTC).isoformat()}


@router.get("/digital-twin/bom/{mo_id}")
async def bom_explosion(
    mo_id: str,
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    svc = DigitalTwinService(session)
    nodes = await svc.explode_bom(mo_id)

    return APIResponse(success=True, data={
        "mo_id": mo_id,
        "tenant_id": str(tenant_id),
        "bom_nodes": [
            {
                "component_id": n.component_id,
                "component_name": n.component_name,
                "level": n.level,
                "parent_id": n.parent_id,
                "lead_time_days": n.lead_time_days,
                "quantity_per": n.quantity_per,
                "supplier_id": n.supplier_id,
                "is_leaf": n.is_leaf,
            }
            for n in nodes
        ],
        "total_components": len(nodes),
        "max_depth": max((n.level for n in nodes), default=0),
        "xai_explanation": XAIExplanation(
            constraints=["recursive_bom_explosion", "multi_level_trace"],
            assumptions=["bill_of_materials_current_version"],
            confidence_score=0.90,
            contributing_factors={
                "depth": float(max((n.level for n in nodes), default=0)),
                "components": float(len(nodes)),
            },
        ).model_dump(),
    }, error=None)


@router.get("/digital-twin/supplier/{supplier_id}")
async def supplier_trace(
    supplier_id: str,
    delay_days: float = 7.0,
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    svc = DigitalTwinService(session)
    impact = await svc.trace_supplier(supplier_id, delay_days)

    return APIResponse(success=True, data={
        "supplier_id": impact.supplier_id,
        "supplier_name": impact.supplier_name,
        "tier": impact.tier,
        "affected_components": impact.affected_components,
        "affected_mos": impact.affected_mos,
        "total_delay_days": impact.total_delay_days,
        "propagation_path": impact.propagation_path,
        "xai_explanation": XAIExplanation(
            constraints=["bfs_risk_propagation", "multi_tier_trace"],
            assumptions=["supplier_dependency_graph_current"],
            confidence_score=0.78,
            contributing_factors={
                "tier": float(impact.tier),
                "affected_mos": float(len(impact.affected_mos)),
                "delay_multiplier": 0.7,
            },
        ).model_dump(),
    }, error=None)


@router.post("/digital-twin/disrupt")
async def simulate_disruption(
    req: DisruptionRequest,
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
    session: AsyncSession = Depends(get_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    svc = DigitalTwinService(session)
    result = await svc.simulate_disruption(req.disruption_type, req.source_id, req.delay_days)

    return APIResponse(success=True, data={
        "disruption_type": result.disruption_type,
        "source_id": result.source_id,
        "delay_days": result.delay_days,
        "impacted_mos": result.impacted_mos,
        "impacted_suppliers": result.impacted_suppliers,
        "total_cost_impact": result.total_cost_impact,
        "resolve_time_ms": result.resolve_time_ms,
        "xai_explanation": XAIExplanation(
            constraints=["disruption_simulation", "cascading_delay_model"],
            assumptions=["tier_based_delay_propagation", "linear_cost_impact"],
            confidence_score=0.75,
            contributing_factors={
                "impacted_mo_count": float(len(result.impacted_mos)),
                "cost_impact": result.total_cost_impact,
                "resolve_efficiency": round(1.0 / max(0.001, result.resolve_time_ms / 1000.0), 4),
            },
        ).model_dump(),
    }, error=None)