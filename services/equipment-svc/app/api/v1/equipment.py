from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.health import predict_failure_date, rul_to_health_score
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.machine_health_telemetry import MachineHealthTelemetry
from ipe_shared.models.maintenance import MaintenanceWindow
from ipe_shared.models.v8_phase2 import EquipmentAsset
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.schemas.common import APIResponse

router = APIRouter(tags=["equipment"])


class SensorIngestRequest(BaseModel):
    machine_id: str
    rul_hours: float = Field(ge=0)
    vibration_rms: float | None = None


@router.get("/equipment")
async def list_equipment(
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "supervisor", "executive"])),
):
    tenant_id = tenant_ctx.get()
    assets = (
        await session.execute(select(EquipmentAsset).where(EquipmentAsset.tenant_id == tenant_id).limit(100))
    ).scalars().all()
    if not assets:
        wcs = (await session.execute(select(WorkCenter).where(WorkCenter.tenant_id == tenant_id).limit(50))).scalars().all()
        return APIResponse(
            success=True,
            data={
                "equipment": [
                    {
                        "id": str(wc.id),
                        "name": wc.name,
                        "health_score": 85.0,
                        "source": "work_center",
                    }
                    for wc in wcs
                ]
            },
            error=None,
        )
    return APIResponse(
        success=True,
        data={
            "equipment": [
                {
                    "id": str(a.id),
                    "name": a.name,
                    "health_score": float(a.health_score or 0),
                    "location": a.location,
                }
                for a in assets
            ]
        },
        error=None,
    )


@router.get("/equipment/{equipment_id}/health")
async def equipment_health(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "supervisor"])),
):
    tenant_id = tenant_ctx.get()
    asset = await session.get(EquipmentAsset, equipment_id)
    if asset and str(asset.tenant_id) == tenant_id:
        name = asset.name
    else:
        wc = await session.get(WorkCenter, equipment_id)
        if not wc or str(wc.tenant_id) != tenant_id:
            return APIResponse(success=False, data=None, error={"code": "NOT_FOUND", "message": "Equipment not found"})
        name = wc.name

    tel = (
        await session.execute(
            select(MachineHealthTelemetry)
            .where(MachineHealthTelemetry.tenant_id == tenant_id, MachineHealthTelemetry.machine_id == name)
            .order_by(MachineHealthTelemetry.last_seen_at.desc())
            .limit(1)
        )
    ).scalars().first()
    rul = float(tel.rul_hours) if tel else 120.0
    score = rul_to_health_score(rul, critical=settings.RUL_CRITICAL_HOURS)
    return APIResponse(
        success=True,
        data={"name": name, "health_score": score, "rul_hours": rul, "telemetry_at": tel.last_seen_at.isoformat() if tel else None},
        error=None,
    )


@router.post("/equipment/{equipment_id}/sensor-data")
async def ingest_sensor(
    equipment_id: UUID,
    req: SensorIngestRequest,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "supervisor"])),
):
    tenant_id = tenant_ctx.get()
    wc = await session.get(WorkCenter, equipment_id)
    work_center_id = wc.id if wc else None
    session.add(
        MachineHealthTelemetry(
            tenant_id=tenant_id,
            machine_id=req.machine_id,
            work_center_id=work_center_id,
            rul_hours=req.rul_hours,
            vibration_rms=req.vibration_rms,
            last_seen_at=datetime.now(UTC),
        )
    )
    asset = await session.get(EquipmentAsset, equipment_id)
    if asset and str(asset.tenant_id) == tenant_id:
        asset.health_score = rul_to_health_score(req.rul_hours, critical=settings.RUL_CRITICAL_HOURS)
    await session.commit()
    return APIResponse(success=True, data={"ingested": True, "health_score": rul_to_health_score(req.rul_hours)}, error=None)


@router.get("/equipment/{equipment_id}/predictions")
async def equipment_predictions(
    equipment_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "supervisor", "executive"])),
):
    tenant_id = tenant_ctx.get()
    asset = await session.get(EquipmentAsset, equipment_id)
    wc = await session.get(WorkCenter, equipment_id)
    name = asset.name if asset else (wc.name if wc else str(equipment_id))
    tel = (
        await session.execute(
            select(MachineHealthTelemetry)
            .where(MachineHealthTelemetry.tenant_id == tenant_id, MachineHealthTelemetry.machine_id == name)
            .order_by(MachineHealthTelemetry.last_seen_at.desc())
            .limit(1)
        )
    ).scalars().first()
    rul = float(tel.rul_hours) if tel else 96.0
    return APIResponse(success=True, data={"equipment_id": str(equipment_id), **predict_failure_date(rul)}, error=None)


@router.get("/maintenance/schedule")
async def maintenance_schedule(
    session: AsyncSession = Depends(get_db_session),
    _user=Depends(require_roles(["planner", "admin", "manager", "supervisor"])),
):
    tenant_id = tenant_ctx.get()
    rows = (
        await session.execute(
            select(MaintenanceWindow).where(MaintenanceWindow.tenant_id == tenant_id).order_by(MaintenanceWindow.start_time)
        )
    ).scalars().all()
    critical = (
        await session.execute(
            select(MachineHealthTelemetry)
            .where(MachineHealthTelemetry.tenant_id == tenant_id, MachineHealthTelemetry.rul_hours < settings.RUL_CRITICAL_HOURS)
            .order_by(MachineHealthTelemetry.rul_hours.asc())
            .limit(20)
        )
    ).scalars().all()
    return APIResponse(
        success=True,
        data={
            "windows": [
                {
                    "work_center_id": str(w.work_center_id),
                    "start": w.start_time.isoformat(),
                    "end": w.end_time.isoformat(),
                    "type": w.type,
                }
                for w in rows
            ],
            "predictive_alerts": [
                {"machine_id": t.machine_id, "rul_hours": float(t.rul_hours)} for t in critical
            ],
        },
        error=None,
    )
