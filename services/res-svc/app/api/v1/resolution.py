from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select as sa_select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_score import score_scenario
from app.core.odoo_notify import notify_odoo_resolution
from app.core.strategy import generate_strategies
from ipe_shared.audit.service import log_audit_event
from ipe_shared.activity.emit import record_from_kafka_topic
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.resolution import ResolutionScenario
from ipe_shared.schemas.common import APIResponse
from ipe_shared.schemas.xai import XAIExplanation

router = APIRouter(prefix="/resolution", tags=["resolution"])


class ProposeRequest(BaseModel):
    mo_id: UUID
    constraint_type: str | None = None


class ApproveRequest(BaseModel):
    scenario_id: UUID
    approved_by: str = "system"
    comment: str = ""


@router.post("/scenarios")
async def propose_scenarios(
    req: ProposeRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    mo_result = await session.execute(
        sa_select(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tid,
            ManufacturingOrder.id == req.mo_id,
        )
    )
    mo = mo_result.scalar_one_or_none()
    if not mo:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "MO not found"})

    constraint = req.constraint_type or mo.primary_constraint or "capacity_overload"

    raw_strategies = generate_strategies(
        mo_id=str(mo.id),
        constraint_type=constraint,
        mo_data={"quantity": float(mo.quantity)},
    )

    existing = await session.execute(
        sa_select(ResolutionScenario.strategy).where(
            ResolutionScenario.tenant_id == tid,
            ResolutionScenario.mo_id == req.mo_id,
            ResolutionScenario.status == "proposed",
        )
    )
    existing_strategies = {row[0] for row in existing.fetchall()}

    scenarios = []
    best = None
    best_score = -1
    for s in raw_strategies:
        if s["strategy"] in existing_strategies:
            continue
        scored = score_scenario(s)
        if scored["business_score"] > best_score:
            best_score = scored["business_score"]
            best = s
        scenario_id = uuid4()
        session.add(ResolutionScenario(
            id=scenario_id, tenant_id=tid, mo_id=req.mo_id,
            strategy=s["strategy"], description=s.get("description", ""),
            business_score=scored["business_score"],
            delivery_impact_days=scored.get("delivery_impact_days"),
            cost_impact=scored.get("cost_impact"),
            status="proposed",
        ))
        scenarios.append({
            "id": str(scenario_id), "mo_id": str(req.mo_id),
            **s, **scored,
        })
    await session.commit()

    await kafka_producer.send_event(
        "resolution", "proposed",
        key=str(req.mo_id),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.resolution.proposed",
            source="res-svc",
            tenant_id=tid,
            timestamp=datetime.now(UTC),
            data={
                "mo_id": str(mo.id),
                "constraint_type": constraint,
                "scenario_count": len(scenarios),
                "recommended_strategy": best["strategy"] if best else None,
            },
        ).model_dump(mode="json"),
    )

    return APIResponse(success=True, data={
        "mo_id": str(mo.id),
        "constraint": constraint,
        "scenarios": scenarios,
        "xai_explanation": XAIExplanation(
            constraints=[constraint],
            assumptions=["cost_model_base_1000", "business_score_weights_delivery_0.35_cost_0.25_risk_0.20"],
            confidence_score=round(max(s.get("business_score", 0) for s in scenarios), 4) if scenarios else 0.0,
            contributing_factors={"constraint_severity": round(min(1.0, len(scenarios) / 4.0), 4)},
        ).model_dump(),
    }, error=None)


@router.post("/approve")
async def approve_scenario(
    req: ApproveRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_roles(["planner", "admin", "manager"])),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    # Read scenario and MO with version
    scenario_result = await session.execute(
        sa_select(ResolutionScenario).where(
            ResolutionScenario.tenant_id == tid,
            ResolutionScenario.id == req.scenario_id,
        )
    )
    scenario = scenario_result.scalar_one_or_none()
    if not scenario:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Scenario not found"})

    mo_result = await session.execute(
        sa_select(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tid,
            ManufacturingOrder.id == scenario.mo_id,
        )
    )
    mo = mo_result.scalar_one_or_none()
    if not mo:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "MO not found"})

    # Optimistic lock: UPDATE ... WHERE version = :v
    current_version = mo.version
    update_result = await session.execute(
        text("""
            UPDATE cdm_manufacturing_order
            SET version = version + 1, status = 'approved',
                updated_at = now()
            WHERE id = :mo_id AND version = :v
        """),
        {"mo_id": scenario.mo_id, "v": current_version},
    )
    if update_result.rowcount == 0:
        await session.rollback()
        return APIResponse(success=False, data=None, error={
            "code": "CONFLICT",
            "message": "MO was modified by another request. Reload and retry.",
        })

    scenario.status = "approved"
    scenario.approved_by = req.approved_by
    scenario.approved_at = datetime.now(UTC)
    scenario.comment = req.comment
    await session.commit()

    # Publish ipe.resolution.approved
    envelope = kafka_producer.build_envelope(
        event_type="ipe.resolution.approved",
        tenant_id=tid,
        payload={
            "scenario_id": str(scenario.id),
            "mo_id": str(scenario.mo_id),
            "strategy": scenario.strategy,
            "approved_by": req.approved_by,
            "delivery_impact_days": float(scenario.delivery_impact_days) if scenario.delivery_impact_days else 0.0,
            "cost_impact": float(scenario.cost_impact) if scenario.cost_impact else 0.0,
        },
    )
    await kafka_producer.send_avro(
        topic="ipe.resolution.approved",
        key=str(scenario.mo_id),
        envelope=envelope,
    )

    await record_from_kafka_topic(
        session,
        "ipe.resolution.approved",
        envelope,
        tenant_id=str(tid),
    )

    await log_audit_event(
        tenant_id=tid,
        actor_type="user",
        actor_id=str(current_user.sub),
        action="APPROVE_SCHEDULE",
        entity_type="resolution_scenario",
        entity_id=scenario.id,
        before_state={
            "mo_id": str(scenario.mo_id),
            "status": "proposed",
            "strategy": scenario.strategy,
        },
        after_state={
            "status": "approved",
            "approved_by": req.approved_by,
            "delivery_impact_days": float(scenario.delivery_impact_days) if scenario.delivery_impact_days else 0.0,
            "cost_impact": float(scenario.cost_impact) if scenario.cost_impact else 0.0,
        },
        rationale=req.comment or f"Approved by {current_user.sub}",
    )

    await notify_odoo_resolution(scenario, mo, str(tid))

    return APIResponse(success=True, data={
        "scenario_id": str(scenario.id),
        "status": "approved",
        "actions_executed": [
            {"action": "approve_scenario", "target": str(scenario.id), "result": "success"},
        ],
        "xai_explanation": XAIExplanation(
            constraints=["optimistic_lock_version_check"],
            assumptions=["approver_has_authority"],
            confidence_score=round(float(scenario.business_score or 0), 4),
            contributing_factors={
                "delivery_impact": round(float(scenario.delivery_impact_days or 0) / 7.0, 4),
                "cost_impact": round(min(1.0, abs(float(scenario.cost_impact or 0)) / 10000.0), 4),
            },
        ).model_dump(),
    }, error=None)


@router.get("/scenarios")
async def list_scenarios(
    mo_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    q = sa_select(ResolutionScenario).where(
        ResolutionScenario.tenant_id == UUID(tenant_id)
    )
    if mo_id:
        q = q.where(ResolutionScenario.mo_id == mo_id)
    q = q.order_by(ResolutionScenario.created_at.desc())

    result = await session.execute(q)
    scenarios = result.scalars().all()

    return APIResponse(success=True, data={
        "scenarios": [
            {
                "id": str(s.id),
                "mo_id": str(s.mo_id),
                "strategy": s.strategy,
                "status": s.status,
                "business_score": float(s.business_score) if s.business_score else None,
                "delivery_impact_days": float(s.delivery_impact_days) if s.delivery_impact_days else None,
                "cost_impact": float(s.cost_impact) if s.cost_impact else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in scenarios
        ]
    }, error=None)
