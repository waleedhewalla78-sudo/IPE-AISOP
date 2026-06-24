"""IoT predictive maintenance telemetry API (V6-R4)."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import or_, select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.iot_health import (
    build_maintenance_block,
    calculate_capacity_degradation,
    should_trigger_replan,
)
from app.core.maintenance_blocks import (
    RUL_MAINTENANCE_THRESHOLD_HOURS,
    compute_block_window,
    register_maintenance_block,
)
from ipe_shared.cache.redis_client import redis_client
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.machine_health_telemetry import MachineHealthTelemetry
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/iot", tags=["iot"])

HEALTH_SCORE_CHANGE_THRESHOLD = 5


class PredictiveTelemetryRequest(BaseModel):
    machine_id: str
    rul_hours: float = Field(ge=0)
    vibration_rms: float | None = None
    recorded_at: datetime | None = None


class LegacyTelemetryRequest(BaseModel):
    resource_id: str
    timestamp: str | None = None
    health_score: float
    metrics: dict = {}


async def _resolve_work_center(session: AsyncSession, tenant_id: UUID, machine_id: str) -> WorkCenter | None:
    result = await session.execute(
        sa_select(WorkCenter).where(
            WorkCenter.tenant_id == tenant_id,
            or_(
                WorkCenter.erp_source_id == machine_id,
                WorkCenter.name == machine_id,
            ),
        )
    )
    return result.scalar_one_or_none()


class TelemetryRequest(BaseModel):
    """V6-R4 predictive (machine_id + rul_hours) or legacy (resource_id + health_score)."""
    machine_id: str | None = None
    rul_hours: float | None = Field(default=None, ge=0)
    vibration_rms: float | None = None
    recorded_at: datetime | None = None
    resource_id: str | None = None
    timestamp: str | None = None
    health_score: float | None = None
    metrics: dict = Field(default_factory=dict)


@router.post("/telemetry")
async def ingest_telemetry(
    req: TelemetryRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Ingest IoT machine health telemetry (V6-R4 RUL or legacy health score)."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        return APIResponse(success=False, data=None, error={"code": "NO_TENANT", "message": "No tenant context"})

    tid = UUID(tenant_id)

    if req.machine_id is not None and req.rul_hours is not None:
        predictive = PredictiveTelemetryRequest(
            machine_id=req.machine_id,
            rul_hours=req.rul_hours,
            vibration_rms=req.vibration_rms,
            recorded_at=req.recorded_at,
        )
        return await _ingest_predictive_telemetry(predictive, session, tid, tenant_id)

    if req.resource_id is not None and req.health_score is not None:
        legacy = LegacyTelemetryRequest(
            resource_id=req.resource_id,
            timestamp=req.timestamp,
            health_score=req.health_score,
            metrics=req.metrics,
        )
        return await _ingest_legacy_telemetry(legacy, session, tid, tenant_id)

    return APIResponse(
        success=False,
        data=None,
        error={
            "code": "INVALID_PAYLOAD",
            "message": "Provide machine_id+rul_hours (V6-R4) or resource_id+health_score (legacy)",
        },
    )

async def _ingest_predictive_telemetry(
    req: PredictiveTelemetryRequest,
    session: AsyncSession,
    tid: UUID,
    tenant_id: str,
) -> APIResponse:
    recorded_at = req.recorded_at or datetime.now(UTC)
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=UTC)

    work_center = await _resolve_work_center(session, tid, req.machine_id)
    wc_id = work_center.id if work_center else None

    row = MachineHealthTelemetry(
        tenant_id=tid,
        machine_id=req.machine_id,
        work_center_id=wc_id,
        rul_hours=req.rul_hours,
        vibration_rms=req.vibration_rms,
        last_seen_at=recorded_at,
    )
    session.add(row)
    await session.commit()

    maintenance_block_published = False
    block_payload = None

    if req.rul_hours < RUL_MAINTENANCE_THRESHOLD_HOURS and work_center:
        block_start, block_end = compute_block_window(recorded_at, req.rul_hours)
        register_maintenance_block(
            tenant_id=tenant_id,
            machine_id=req.machine_id,
            work_center_id=str(work_center.id),
            block_start=block_start,
            block_end=block_end,
            rul_hours=req.rul_hours,
        )
        block_payload = {
            "machine_id": req.machine_id,
            "work_center_id": str(work_center.id),
            "block_start": block_start.isoformat(),
            "block_end": block_end.isoformat(),
            "rul_hours": float(req.rul_hours),
        }
        envelope = kafka_producer.build_envelope(
            event_type="ipe.maintenance.block_required",
            tenant_id=tenant_id,
            payload=block_payload,
        )
        await kafka_producer.send_avro(
            "ipe.maintenance.block_required",
            key=f"{tenant_id}:{req.machine_id}",
            envelope=envelope,
        )
        maintenance_block_published = True

    return APIResponse(
        success=True,
        data={
            "machine_id": req.machine_id,
            "rul_hours": req.rul_hours,
            "vibration_rms": req.vibration_rms,
            "recorded_at": recorded_at.isoformat(),
            "work_center_id": str(wc_id) if wc_id else None,
            "maintenance_block_published": maintenance_block_published,
            "maintenance_block": block_payload,
            "telemetry_id": str(row.id),
        },
        error=None,
    )


async def _ingest_legacy_telemetry(
    req: LegacyTelemetryRequest,
    session: AsyncSession,
    tid: UUID,
    tenant_id: str,
) -> APIResponse:
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
async def get_resource_health(resource_id: str):
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
