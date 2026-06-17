from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.nlp_classifier import classify_by_llm
from app.core.rule_classifier import classify_by_rules
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.manufacturing_order import ManufacturingOrder as MOModel
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/delay", tags=["delay"])


class ClassifyRequest(BaseModel):
    mo_id: UUID | None = None
    source_text: str = ""
    mo_status: str = ""
    work_center_status: str = ""


@router.post("/classify")
async def classify_delay(
    req: ClassifyRequest,
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)
    mo = None
    if req.mo_id:
        result = await session.execute(
            sa_select(MOModel).where(
                MOModel.tenant_id == tid,
                MOModel.id == req.mo_id,
            )
        )
        mo = result.scalar_one_or_none()

    delay_data = req.model_dump()
    classification = classify_by_rules(delay_data)

    if classification["cause_category"] == "other" or classification["confidence"] < 0.5:
        nlp_result = await classify_by_llm(req.source_text)
        if nlp_result["confidence"] > classification["confidence"]:
            classification = nlp_result
            classification["source"] = "nlp"
        else:
            classification["source"] = "rule"
    else:
        classification["source"] = "rule"

    if mo:
        classification["mo_id"] = str(mo.id)
        classification["mo_number"] = mo.mo_number

    await kafka_producer.send_event(
        "delay", "logged",
        key=str(req.mo_id or "unknown"),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.delay.logged",
            source="del-svc",
            tenant_id=tid,
            timestamp=datetime.now(UTC),
            data={
                "mo_id": str(req.mo_id) if req.mo_id else "",
                "source_text": req.source_text,
                "cause_category": classification["cause_category"],
                "confidence": classification["confidence"],
            },
        ).model_dump(mode="json"),
    )

    return APIResponse(success=True, data=classification, error=None)


@router.get("/report")
async def get_delay_report(
    mo_id: UUID | None = Query(None),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    q = sa_select(MOModel).where(MOModel.tenant_id == UUID(tenant_id))
    if mo_id:
        q = q.where(MOModel.id == mo_id)
    result = await session.execute(q)
    mos = result.scalars().all()

    delayed_mos = [mo for mo in mos if mo.status in ("delayed", "at_risk")]
    report = {
        "total_mos": len(mos),
        "delayed_count": len(delayed_mos),
        "delay_rate": round(len(delayed_mos) / max(len(mos), 1), 4),
        "delayed_mos": [
            {
                "id": str(mo.id),
                "mo_number": mo.mo_number,
                "status": mo.status,
                "progress_pct": getattr(mo, "progress_pct", 0),
            }
            for mo in delayed_mos
        ],
    }
    return APIResponse(success=True, data=report, error=None)
