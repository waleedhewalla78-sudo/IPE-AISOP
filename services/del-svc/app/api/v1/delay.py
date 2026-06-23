from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func as sa_func
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.nlp_classifier import classify_by_llm
from app.core.rule_classifier import classify_by_rules
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.delay_root_cause import DelayRootCause
from ipe_shared.models.manufacturing_order import ManufacturingOrder as MOModel
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/delay", tags=["delay"])


class DelayCategory(StrEnum):
    MATERIAL_SHORTAGE = "material_shortage"
    CAPACITY_OVERLOAD = "capacity_overload"
    LABOR_ABSENCE = "labor_absence"
    SUPPLIER_DELAY = "supplier_delay"
    MAINTENANCE = "maintenance"
    QUALITY_ISSUE = "quality_issue"
    PROCESS_VARIANCE = "process_variance"
    OTHER = "other"


VALID_CATEGORIES = {c.value for c in DelayCategory}


class ClassifyRequest(BaseModel):
    mo_id: UUID | None = None
    source_text: str = ""
    mo_status: str = ""
    work_center_status: str = ""


class ChatterIngestRequest(BaseModel):
    mo_id: UUID
    chatter_text: str
    author: str | None = None


class BatchChatterIngestRequest(BaseModel):
    messages: list[ChatterIngestRequest]


@router.post("/chatter/batch")
async def ingest_batch_chatter(
    req: BatchChatterIngestRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    """Batch ingest Odoo chatter texts for Celery processing."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)
    results = []

    for msg in req.messages:
        classification = classify_by_rules({"source_text": msg.chatter_text})

        if classification["cause_category"] not in VALID_CATEGORIES or classification["confidence"] < 0.5:
            try:
                nlp_result = await classify_by_llm(msg.chatter_text)
                if nlp_result["confidence"] > classification["confidence"]:
                    classification = nlp_result
                    classification["extracted_by"] = "llm"
                else:
                    classification["extracted_by"] = "regex"
            except Exception:
                classification["extracted_by"] = "regex"
        else:
            classification["extracted_by"] = "regex"

        if classification["cause_category"] not in VALID_CATEGORIES:
            classification["cause_category"] = DelayCategory.OTHER.value

        root_cause = DelayRootCause(
            tenant_id=tid,
            delay_event_id=None,
            source_text=msg.chatter_text[:2048],
            primary_category=classification["cause_category"],
            secondary_categories=classification.get("secondary_categories", []),
            confidence=classification["confidence"],
            extracted_by=classification.get("extracted_by", "regex"),
        )
        session.add(root_cause)
        await session.flush()

        results.append({
            "mo_id": str(msg.mo_id),
            "root_cause_id": str(root_cause.id),
            "primary_category": classification["cause_category"],
            "confidence": classification["confidence"],
            "extracted_by": classification.get("extracted_by", "regex"),
        })

    await kafka_producer.send_event(
        "delay", "batch_root_cause_extracted",
        key=str(tid),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.delay.batch_root_cause_extracted",
            source="del-svc",
            tenant_id=tid,
            timestamp=datetime.now(UTC),
            data={
                "batch_size": len(results),
                "results": results,
            },
        ).model_dump(mode="json"),
    )

    return APIResponse(
        success=True,
        data={"processed": len(results), "results": results},
        error=None,
    )


@router.post("/classify")
async def classify_delay(
    req: ClassifyRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
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

    if classification["cause_category"] not in VALID_CATEGORIES or classification["confidence"] < 0.5:
        nlp_result = await classify_by_llm(req.source_text)
        if nlp_result["confidence"] > classification["confidence"]:
            classification = nlp_result
            classification["source"] = "nlp"
        else:
            classification["source"] = "rule"
    else:
        classification["source"] = "rule"

    if classification["cause_category"] not in VALID_CATEGORIES:
        classification["cause_category"] = DelayCategory.OTHER.value

    if mo:
        classification["mo_id"] = str(mo.id)
        classification["mo_number"] = mo.erp_mo_id

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


@router.post("/chatter")
async def ingest_chatter(
    req: ChatterIngestRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    """Ingest Odoo chatter text, classify delay cause, write to cdm_delay_root_cause."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    classification = classify_by_rules({"source_text": req.chatter_text})

    if classification["cause_category"] not in VALID_CATEGORIES or classification["confidence"] < 0.5:
        nlp_result = await classify_by_llm(req.chatter_text)
        if nlp_result["confidence"] > classification["confidence"]:
            classification = nlp_result
            classification["extracted_by"] = "llm"
        else:
            classification["extracted_by"] = "regex"
    else:
        classification["extracted_by"] = "regex"

    if classification["cause_category"] not in VALID_CATEGORIES:
        classification["cause_category"] = DelayCategory.OTHER.value

    root_cause = DelayRootCause(
        tenant_id=tid,
        delay_event_id=None,
        source_text=req.chatter_text[:2048],
        primary_category=classification["cause_category"],
        secondary_categories=classification.get("secondary_categories", []),
        confidence=classification["confidence"],
        extracted_by=classification.get("extracted_by", "regex"),
    )
    session.add(root_cause)
    await session.flush()

    await kafka_producer.send_event(
        "delay", "root_cause_extracted",
        key=str(req.mo_id),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.delay.root_cause_extracted",
            source="del-svc",
            tenant_id=tid,
            timestamp=datetime.now(UTC),
            data={
                "root_cause_id": str(root_cause.id),
                "mo_id": str(req.mo_id),
                "primary_category": classification["cause_category"],
                "confidence": classification["confidence"],
                "extracted_by": classification.get("extracted_by", "regex"),
            },
        ).model_dump(mode="json"),
    )

    return APIResponse(
        success=True,
        data={
            "root_cause_id": str(root_cause.id),
            "primary_category": classification["cause_category"],
            "confidence": classification["confidence"],
            "extracted_by": classification.get("extracted_by", "regex"),
        },
        error=None,
    )


@router.get("/pareto")
async def get_pareto(
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_db_session),
):
    """Return delay root cause Pareto chart data (category counts + cumulative %)."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    from datetime import timedelta
    cutoff = datetime.now(UTC) - timedelta(days=days)

    result = await session.execute(
        sa_select(
            DelayRootCause.primary_category,
            sa_func.count(DelayRootCause.id).label("count"),
        ).where(
            DelayRootCause.tenant_id == tid,
            DelayRootCause.created_at >= cutoff,
        ).group_by(
            DelayRootCause.primary_category,
        ).order_by(
            sa_func.count(DelayRootCause.id).desc(),
        )
    )
    rows = result.all()

    total = sum(r.count for r in rows)
    cumulative = 0
    pareto_items = []
    for row in rows:
        cumulative += row.count
        pareto_items.append({
            "category": row.primary_category,
            "count": row.count,
            "pct": round(row.count / max(total, 1) * 100, 2),
            "cumulative_pct": round(cumulative / max(total, 1) * 100, 2),
        })

    return APIResponse(
        success=True,
        data={
            "total_root_causes": total,
            "days": days,
            "pareto": pareto_items,
        },
        error=None,
    )


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
