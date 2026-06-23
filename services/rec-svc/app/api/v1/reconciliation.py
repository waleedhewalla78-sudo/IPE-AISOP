from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.reconciliation import (
    analyze_mo_completion,
    build_retrain_payload,
    calculate_prediction_drift,
    evaluate_shadow_model,
    should_trigger_retrain,
)
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.duration_prediction import DurationPrediction
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.work_order import WorkOrder
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


class AnalyzeRequest(BaseModel):
    mo_id: UUID


@router.post("/analyze")
async def analyze(
    req: AnalyzeRequest,
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    result = await session.execute(
        sa_select(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == UUID(tenant_id),
            ManufacturingOrder.id == req.mo_id,
        )
    )
    mo = result.scalar_one_or_none()
    if not mo:
        return APIResponse(
            success=False, data=None,
            error={"code": "NOT_FOUND", "message": "MO not found"},
        )

    wo_result = await session.execute(
        sa_select(WorkOrder).where(
            WorkOrder.tenant_id == UUID(tenant_id),
            WorkOrder.mo_id == req.mo_id,
        )
    )
    work_orders = list(wo_result.scalars().all())

    analysis = analyze_mo_completion(mo, work_orders)

    await kafka_producer.send_event(
        "reconciliation", "completed",
        key=str(req.mo_id),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.reconciliation.completed",
            source="rec-svc",
            tenant_id=UUID(tenant_id),
            timestamp=datetime.now(UTC),
            data={
                "mo_id": str(req.mo_id),
                "yield_variance_pct": analysis["yield_variance_pct"],
                "time_variance_pct": analysis["time_variance_pct"],
                "scrap_delta": analysis["scrap_delta"],
                "planned_duration_days": analysis["planned_duration_days"],
                "actual_duration_days": analysis["actual_duration_days"],
                "completed_work_orders": analysis["completed_work_orders"],
                "total_work_orders": analysis["total_work_orders"],
            },
        ).model_dump(mode="json"),
    )

    return APIResponse(success=True, data=analysis, error=None)


@router.post("/daily")
async def daily_reconciliation(
    current_user=Depends(require_roles(["admin", "planner"])),
    session: AsyncSession = Depends(get_db_session),
):
    """Run daily reconciliation: variance calculation, drift detection, auto-retrain.

    Includes shadow evaluation: new model must beat current MAE to be deployed.
    Minimum data threshold: 500 records for production retraining.
    """
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    tid = UUID(tenant_id)

    pred_result = await session.execute(
        sa_select(DurationPrediction).where(
            DurationPrediction.tenant_id == tid,
        ).order_by(DurationPrediction.created_at.desc()).limit(500)
    )
    predictions = list(pred_result.scalars().all())

    drift_result = calculate_prediction_drift(predictions)

    if drift_result["drift_detected"]:
        await session.execute(
            DurationPrediction.__table__.update().where(
                DurationPrediction.tenant_id == tid,
            ).values(drift_detected=True)
        )

    retrain_triggered = False
    retrain_result = None
    shadow_evaluation = None

    if should_trigger_retrain(drift_result, strict=True):
        historical_records = []
        for p in predictions[:500]:
            historical_records.append({
                "product_id": str(p.product_id) if p.product_id else "",
                "work_center_id": str(p.work_center_id) if p.work_center_id else "",
                "batch_size": float(p.batch_size or 1),
                "duration_planned_mins": float(p.duration_planned_mins or 0),
                "duration_actual_mins": float(p.actual_duration_mins or 0),
                "operator_skill_tags": [],
                "hour_of_day": 8,
                "day_of_week": 1,
                "month": 1,
            })

        payload = build_retrain_payload(drift_result, historical_records)

        try:
            async with httpx.AsyncClient(timeout=30.0) as ml_client:
                ml_resp = await ml_client.post(
                    f"{settings.ML_SVC_URL}/api/v1/predict/duration/train",
                    json=payload,
                )
                if ml_resp.status_code == 200:
                    retrain_result = ml_resp.json().get("data", {})

                    current_mae = drift_result.get("baseline_mae") or drift_result["mae"]
                    new_mae = retrain_result.get("mae", current_mae)
                    holdout_size = retrain_result.get("training_records", 0) // 5

                    shadow_evaluation = evaluate_shadow_model(
                        new_mae=new_mae,
                        current_mae=current_mae,
                        holdout_size=holdout_size,
                    )

                    if shadow_evaluation["should_deploy"]:
                        retrain_triggered = True
                        retrain_result["deployment_status"] = "deployed"
                        retrain_result["improvement_pct"] = shadow_evaluation["improvement_pct"]
                    else:
                        retrain_result["deployment_status"] = "rejected"
                        retrain_result["rejection_reason"] = shadow_evaluation["rejection_reason"]
        except Exception:
            retrain_result = {"status": "error", "reason": "ml-svc unreachable"}

    await kafka_producer.send_event(
        "reconciliation", "daily_summary",
        key=str(tid),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.reconciliation.daily_summary",
            source="rec-svc",
            tenant_id=tid,
            timestamp=datetime.now(UTC),
            data={
                "mae": drift_result["mae"],
                "drift_detected": drift_result["drift_detected"],
                "drift_pct": drift_result["drift_pct"],
                "sample_count": drift_result["sample_count"],
                "retrain_triggered": retrain_triggered,
                "retrain_result": retrain_result,
                "shadow_evaluation": shadow_evaluation,
            },
        ).model_dump(mode="json"),
    )

    return APIResponse(
        success=True,
        data={
            "drift": drift_result,
            "retrain_triggered": retrain_triggered,
            "retrain_result": retrain_result,
            "shadow_evaluation": shadow_evaluation,
        },
        error=None,
    )


@router.get("/drift")
async def get_drift_status(
    session: AsyncSession = Depends(get_db_session),
):
    """Get current drift status for the tenant."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(
            success=False, data=None,
            error={"code": "NO_TENANT", "message": "No tenant context"},
        )

    tid = UUID(tenant_id)

    pred_result = await session.execute(
        sa_select(DurationPrediction).where(
            DurationPrediction.tenant_id == tid,
        ).order_by(DurationPrediction.created_at.desc()).limit(500)
    )
    predictions = list(pred_result.scalars().all())

    drift_result = calculate_prediction_drift(predictions)

    return APIResponse(
        success=True,
        data=drift_result,
        error=None,
    )
