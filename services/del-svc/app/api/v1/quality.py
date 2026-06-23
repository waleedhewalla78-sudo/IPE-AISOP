from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.quality_processor import (
    QualityEventInput,
    process_quality_event,
    QualityEventType,
    Severity,
    DefectCategory,
)
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.quality_event import QualityEvent
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/quality", tags=["quality"])


class QualityEventRequest(BaseModel):
    mo_id: UUID
    work_order_id: UUID | None = None
    work_center_id: UUID | None = None
    product_id: UUID
    event_type: str
    severity: str = "minor"
    defect_category: str | None = None
    defect_count: int = 1
    inspection_method: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    rework_required: bool = False
    rework_cycles: int = 0
    max_rework_cycles: int = 3
    scrap_quantity: int = 0
    cost_impact: float = 0.0


class QualityResolutionRequest(BaseModel):
    quality_event_id: UUID
    action: str
    root_cause: str | None = None
    corrective_action: str | None = None
    scrap_quantity: int = 0


@router.post("/events")
async def create_quality_event(
    req: QualityEventRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    event_input = QualityEventInput(
        event_type=req.event_type,
        severity=req.severity,
        defect_category=req.defect_category,
        defect_count=req.defect_count,
        inspection_method=req.inspection_method,
        root_cause=req.root_cause,
        corrective_action=req.corrective_action,
        rework_required=req.rework_required,
        rework_cycles=req.rework_cycles,
        max_rework_cycles=req.max_rework_cycles,
        scrap_quantity=req.scrap_quantity,
        cost_impact=req.cost_impact,
    )

    decision = process_quality_event(event_input)

    quality_event = QualityEvent(
        id=uuid4(),
        tenant_id=tid,
        mo_id=req.mo_id,
        work_order_id=req.work_order_id,
        work_center_id=req.work_center_id,
        product_id=req.product_id,
        event_type=req.event_type,
        severity=decision.severity,
        defect_category=req.defect_category,
        defect_count=req.defect_count,
        inspection_method=req.inspection_method,
        root_cause=req.root_cause,
        corrective_action=req.corrective_action,
        rework_required=decision.rework_eligible,
        rework_cycles=decision.rework_cycles,
        max_rework_cycles=decision.max_rework_cycles,
        scrap_quantity=decision.scrap_quantity,
        cost_impact=decision.impact_summary.get("cost_impact", 0.0),
        status=decision.status,
        detected_at=datetime.now(UTC),
    )

    session.add(quality_event)
    await session.commit()
    await session.refresh(quality_event)

    envelope = kafka_producer.build_envelope(
        event_type="ipe.quality.event_created",
        tenant_id=tid,
        payload={
            "quality_event_id": str(quality_event.id),
            "mo_id": str(req.mo_id),
            "product_id": str(req.product_id),
            "event_type": req.event_type,
            "severity": decision.severity,
            "action": decision.action,
            "status": decision.status,
            "rework_eligible": decision.rework_eligible,
            "requires_quarantine": decision.requires_quarantine,
            "escalation_level": decision.escalation_level,
            "cost_impact": decision.impact_summary.get("cost_impact", 0.0),
        },
    )
    await kafka_producer.send_avro(
        topic="ipe.quality.event_created",
        key=str(quality_event.id),
        envelope=envelope,
    )

    return APIResponse(success=True, data={
        "quality_event_id": str(quality_event.id),
        "decision": {
            "action": decision.action,
            "severity": decision.severity,
            "status": decision.status,
            "rework_eligible": decision.rework_eligible,
            "rework_cycles": decision.rework_cycles,
            "max_rework_cycles": decision.max_rework_cycles,
            "scrap_quantity": decision.scrap_quantity,
            "requires_quarantine": decision.requires_quarantine,
            "requires_root_cause": decision.requires_root_cause,
            "requires_corrective_action": decision.requires_corrective_action,
            "escalation_level": decision.escalation_level,
            "impact_summary": decision.impact_summary,
        },
    }, error=None)


@router.post("/resolve")
async def resolve_quality_event(
    req: QualityResolutionRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    result = await session.execute(
        sa_select(QualityEvent).where(
            QualityEvent.tenant_id == tid,
            QualityEvent.id == req.quality_event_id,
        )
    )
    quality_event = result.scalar_one_or_none()

    if not quality_event:
        return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Quality event not found"})

    if req.action == "rework" and quality_event.rework_cycles < quality_event.max_rework_cycles:
        quality_event.rework_cycles += 1
        quality_event.rework_required = True
        quality_event.status = "in_rework"
    elif req.action == "scrap":
        quality_event.scrap_quantity = req.scrap_quantity or 1
        quality_event.status = "scapped"
    elif req.action == "close":
        quality_event.status = "closed"
        quality_event.resolved_at = datetime.now(UTC)
    elif req.action == "corrective_action":
        quality_event.corrective_action = req.corrective_action
        quality_event.status = "correcting"

    if req.root_cause:
        quality_event.root_cause = req.root_cause

    await session.commit()

    envelope = kafka_producer.build_envelope(
        event_type="ipe.quality.event_resolved",
        tenant_id=tid,
        payload={
            "quality_event_id": str(quality_event.id),
            "mo_id": str(quality_event.mo_id),
            "action": req.action,
            "status": quality_event.status,
            "rework_cycles": quality_event.rework_cycles,
            "root_cause": req.root_cause,
        },
    )
    await kafka_producer.send_avro(
        topic="ipe.quality.event_resolved",
        key=str(quality_event.id),
        envelope=envelope,
    )

    return APIResponse(success=True, data={
        "quality_event_id": str(quality_event.id),
        "status": quality_event.status,
        "rework_cycles": quality_event.rework_cycles,
        "resolved_at": str(quality_event.resolved_at) if quality_event.resolved_at else None,
    }, error=None)


@router.get("/events")
async def list_quality_events(
    mo_id: UUID | None = None,
    status: str | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    query = sa_select(QualityEvent).where(QualityEvent.tenant_id == tid)
    if mo_id:
        query = query.where(QualityEvent.mo_id == mo_id)
    if status:
        query = query.where(QualityEvent.status == status)

    result = await session.execute(query)
    events = result.scalars().all()

    return APIResponse(success=True, data=[
        {
            "id": str(e.id),
            "mo_id": str(e.mo_id),
            "product_id": str(e.product_id),
            "event_type": e.event_type,
            "severity": e.severity,
            "defect_category": e.defect_category,
            "defect_count": e.defect_count,
            "rework_cycles": e.rework_cycles,
            "scrap_quantity": e.scrap_quantity,
            "cost_impact": e.cost_impact,
            "status": e.status,
            "detected_at": str(e.detected_at),
        }
        for e in events
    ], error=None)
