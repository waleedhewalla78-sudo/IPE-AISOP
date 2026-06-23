from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.iot_health import (
    build_maintenance_block,
    calculate_capacity_degradation,
    calculate_operation_duration_impact,
    should_trigger_replan,
)
from ipe_shared.cache.redis_client import redis_client
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.schemas.common import APIResponse

from uuid import uuid4

router = APIRouter(prefix="/iot", tags=["iot"])

HEALTH_SCORE_CHANGE_THRESHOLD = 5


class TelemetryRequest(BaseModel):
    resource_id: str
    timestamp: str | None = None
    health_score: float
    metrics: dict = {}


@router.post("/telemetry")
async def ingest_telemetry(
    req: TelemetryRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Ingest IoT machine health telemetry.

    Idempotent: ignores updates if health_score hasn't changed by >= 5 points.
    Triggers capacity degradation or maintenance blocks based on health.
    """
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)
    resource_key = f"iot:health:{tenant_id}:{req.resource_id}"

    previous_health_str = await redis_client.get_key(resource_key)
    previous_health = float(previous_health_str) if previous_health_str else None

    if previous_health is not None:
        change = abs(req.health_score - previous_health)
        if change < HEALTH_SCORE_CHANGE_THRESHOLD:
            return APIResponse(
                success=True,
                data={"status": "ignored", "reason": f"Health change {change:.1f} below threshold {HEALTH_SCORE_CHANGE_THRESHOLD}"},
                error=None,
            )

    await redis_client.set_key(resource_key, str(req.health_score), ttl=86400 * 7)

    degradation = calculate_capacity_degradation(req.health_score)

    previous_factor_str = await redis_client.get_key(f"iot:factor:{tenant_id}:{req.resource_id}")
    previous_factor = float(previous_factor_str) if previous_factor_str else None

    replan_info = should_trigger_replan(previous_health, req.health_score, previous_factor)

    await redis_client.set_key(
        f"iot:factor:{tenant_id}:{req.resource_id}",
        str(degradation["capacity_factor"]),
        ttl=86400 * 7,
    )

    wc_result = await session.execute(
        sa_select(WorkCenter).where(
            WorkCenter.tenant_id == tid,
            WorkCenter.erp_source_id == req.resource_id,
        )
    )
    work_center = wc_result.scalar_one_or_none()

    maintenance_block = None
    if degradation["requires_maintenance"] and work_center:
        maintenance_block = build_maintenance_block(
            resource_id=str(work_center.id),
            tenant_id=tenant_id,
            health_score=req.health_score,
        )

    event_data = {
        "resource_id": req.resource_id,
        "health_score": req.health_score,
        "capacity_factor": degradation["capacity_factor"],
        "status": degradation["status"],
        "requires_maintenance": degradation["requires_maintenance"],
        "should_replan": replan_info["should_replan"],
        "replan_reason": replan_info["reason"],
        "metrics": req.metrics,
    }

    if maintenance_block:
        event_data["maintenance_block"] = maintenance_block

    await kafka_producer.send_event(
        "iot", "telemetry",
        key=f"{tenant_id}:{req.resource_id}",
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.iot.telemetry",
            source="cap-svc",
            tenant_id=tid,
            timestamp=datetime.now(UTC),
            data=event_data,
        ).model_dump(mode="json"),
    )

    if replan_info["should_replan"]:
        await kafka_producer.send_event(
            "replan", "triggered",
            key=f"{tenant_id}:{req.resource_id}",
            value=EventEnvelope(
                event_id=str(uuid4()),
                event_type="ipe.replan.triggered",
                source="cap-svc",
                tenant_id=tid,
                timestamp=datetime.now(UTC),
                data={
                    "trigger": "iot_health_degradation",
                    "resource_id": req.resource_id,
                    "health_score": req.health_score,
                    "severity": replan_info["severity"],
                    "reason": replan_info["reason"],
                    "maintenance_block": maintenance_block,
                },
            ).model_dump(mode="json"),
        )

    return APIResponse(
        success=True,
        data={
            "resource_id": req.resource_id,
            "health_score": req.health_score,
            "degradation": degradation,
            "replan": replan_info,
            "maintenance_block_injected": maintenance_block is not None,
        },
        error=None,
    )


@router.get("/health/{resource_id}")
async def get_resource_health(
    resource_id: str,
):
    """Get current cached health score for a resource."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    resource_key = f"iot:health:{tenant_id}:{resource_id}"
    health_str = await redis_client.get_key(resource_key)
    factor_str = await redis_client.get_key(f"iot:factor:{tenant_id}:{resource_id}")

    if health_str is None:
        return APIResponse(success=True, data={"status": "no_data", "resource_id": resource_id}, error=None)

    health_score = float(health_str)
    degradation = calculate_capacity_degradation(health_score)

    return APIResponse(
        success=True,
        data={
            "resource_id": resource_id,
            "health_score": health_score,
            "capacity_factor": degradation["capacity_factor"],
            "status": degradation["status"],
            "requires_maintenance": degradation["requires_maintenance"],
        },
        error=None,
    )
