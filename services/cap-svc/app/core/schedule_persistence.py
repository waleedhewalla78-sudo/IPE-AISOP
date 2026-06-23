"""Persist solver output to CDM and approve with optimistic locking."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.events.producer import kafka_producer
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.routing import RoutingOperation
from ipe_shared.models.work_center import WorkCenter
from ipe_shared.models.work_order import WorkOrder


class SchedulePersistenceError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _minute_to_dt(base: datetime, minute: float) -> datetime:
    return base + timedelta(minutes=float(minute))


async def _get_or_create_work_order(
    session: AsyncSession,
    tenant_id: UUID,
    mo_id: UUID,
    routing_op_id: UUID,
    work_center_id: UUID,
    sequence: int,
    duration_mins: float,
) -> WorkOrder:
    result = await session.execute(
        select(WorkOrder).where(
            WorkOrder.tenant_id == tenant_id,
            WorkOrder.mo_id == mo_id,
            WorkOrder.routing_op_id == routing_op_id,
        )
    )
    wo = result.scalar_one_or_none()
    if wo:
        return wo

    wo = WorkOrder(
        tenant_id=tenant_id,
        mo_id=mo_id,
        routing_op_id=routing_op_id,
        work_center_id=work_center_id,
        sequence=sequence,
        duration_planned_mins=duration_mins,
        status="pending",
        version=1,
    )
    session.add(wo)
    await session.flush()
    return wo


async def persist_schedule_proposal(
    session: AsyncSession,
    tenant_id: UUID,
    assignments: list[dict[str, Any]],
    *,
    horizon_start: datetime | None = None,
) -> dict[str, Any]:
    """Write solver assignments as proposal on work orders and MO ai_suggested_*."""
    if not assignments:
        return {"updated_mos": 0, "updated_work_orders": 0}

    base = horizon_start or datetime.now(UTC)
    mo_bounds: dict[str, dict[str, datetime]] = {}
    updated_wos = 0

    for item in assignments:
        mo_id = UUID(str(item["mo_id"]))
        routing_op_id = UUID(str(item["operation_id"]))
        wc_id = UUID(str(item["work_center_id"]))
        start_dt = _minute_to_dt(base, item["start_minute"])
        end_dt = _minute_to_dt(base, item["end_minute"])
        duration = float(item.get("duration") or (item["end_minute"] - item["start_minute"]))

        wo = await _get_or_create_work_order(
            session,
            tenant_id,
            mo_id,
            routing_op_id,
            wc_id,
            int(item.get("sequence") or 0),
            duration,
        )
        wo.planned_start = start_dt
        wo.planned_end = end_dt
        wo.duration_planned_mins = duration
        wo.updated_at = datetime.now(UTC)
        updated_wos += 1

        key = str(mo_id)
        if key not in mo_bounds:
            mo_bounds[key] = {"start": start_dt, "end": end_dt}
        else:
            mo_bounds[key]["start"] = min(mo_bounds[key]["start"], start_dt)
            mo_bounds[key]["end"] = max(mo_bounds[key]["end"], end_dt)

    updated_mos = 0
    for mo_key, bounds in mo_bounds.items():
        mo_result = await session.execute(
            select(ManufacturingOrder).where(
                ManufacturingOrder.tenant_id == tenant_id,
                ManufacturingOrder.id == UUID(mo_key),
            )
        )
        mo = mo_result.scalar_one_or_none()
        if not mo:
            continue
        mo.ai_suggested_start = bounds["start"]
        mo.ai_suggested_end = bounds["end"]
        mo.updated_at = datetime.now(UTC)
        updated_mos += 1

    await session.commit()
    return {"updated_mos": updated_mos, "updated_work_orders": updated_wos}


async def approve_schedule_mos(
    session: AsyncSession,
    tenant_id: UUID,
    mo_ids: list[UUID],
    *,
    expected_versions: dict[str, int | float] | None = None,
    approved_by: str = "planner",
) -> dict[str, Any]:
    """Promote AI proposal to approved plan with optimistic locking on MO.version."""
    activated: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    for mo_id in mo_ids:
        result = await session.execute(
            select(ManufacturingOrder).where(
                ManufacturingOrder.tenant_id == tenant_id,
                ManufacturingOrder.id == mo_id,
            )
        )
        mo = result.scalar_one_or_none()
        if not mo:
            failed.append({"mo_id": str(mo_id), "reason": "NOT_FOUND"})
            continue

        current_version = int(float(mo.version or 1))
        if expected_versions and str(mo_id) in expected_versions:
            expected = int(float(expected_versions[str(mo_id)]))
            if expected != current_version:
                failed.append({
                    "mo_id": str(mo_id),
                    "reason": "VERSION_CONFLICT",
                    "expected_version": expected,
                    "current_version": current_version,
                })
                continue

        if not mo.ai_suggested_start or not mo.ai_suggested_end:
            failed.append({"mo_id": str(mo_id), "reason": "NO_AI_PROPOSAL"})
            continue

        mo.planned_start = mo.ai_suggested_start
        mo.planned_end = mo.ai_suggested_end
        mo.ai_suggested_start = None
        mo.ai_suggested_end = None
        mo.version = current_version + 1
        mo.ai_schedule_version = (mo.ai_schedule_version or 0) + 1
        mo.status = "planned" if mo.status == "draft" else mo.status
        mo.updated_at = datetime.now(UTC)

        wo_result = await session.execute(
            select(WorkOrder).where(
                WorkOrder.tenant_id == tenant_id,
                WorkOrder.mo_id == mo_id,
            )
        )
        for wo in wo_result.scalars().all():
            if wo.planned_start and wo.planned_end:
                wo.status = "planned"
                wo.version = int(wo.version or 1) + 1
                wo.updated_at = datetime.now(UTC)

        activated.append({
            "mo_id": str(mo_id),
            "erp_mo_id": mo.erp_mo_id,
            "new_planned_start": mo.planned_start.isoformat() if mo.planned_start else None,
            "new_planned_end": mo.planned_end.isoformat() if mo.planned_end else None,
            "version": int(float(mo.version)),
            "ai_schedule_version": mo.ai_schedule_version,
        })

    if activated:
        await session.commit()
        envelope = kafka_producer.build_envelope(
            event_type="ipe.schedule.approved",
            tenant_id=str(tenant_id),
            payload={
                "approved_by": approved_by,
                "mo_ids": [a["mo_id"] for a in activated],
                "activated": activated,
            },
        )
        try:
            await kafka_producer.send_avro(
                topic="ipe.schedule.approved",
                key=str(tenant_id),
                envelope=envelope,
            )
        except Exception:
            pass
    elif failed:
        await session.rollback()
    else:
        await session.commit()

    return {
        "activated": activated,
        "failed": failed,
        "total": len(mo_ids),
        "activated_count": len(activated),
        "failed_count": len(failed),
    }


async def load_active_schedule(
    session: AsyncSession,
    tenant_id: UUID,
    *,
    mo_ids: list[UUID] | None = None,
) -> list[dict[str, Any]]:
    """Build Gantt rows from persisted work orders."""
    query = (
        select(WorkOrder, ManufacturingOrder, RoutingOperation, WorkCenter)
        .join(ManufacturingOrder, WorkOrder.mo_id == ManufacturingOrder.id)
        .join(RoutingOperation, WorkOrder.routing_op_id == RoutingOperation.id)
        .join(WorkCenter, WorkOrder.work_center_id == WorkCenter.id)
        .where(
            WorkOrder.tenant_id == tenant_id,
            WorkOrder.planned_start.isnot(None),
            WorkOrder.planned_end.isnot(None),
        )
    )
    if mo_ids:
        query = query.where(WorkOrder.mo_id.in_(mo_ids))

    result = await session.execute(query.order_by(WorkOrder.mo_id, WorkOrder.sequence))
    rows: dict[str, dict[str, Any]] = {}
    base = datetime.now(UTC)

    for wo, mo, routing, wc in result.all():
        mo_key = str(mo.id)
        if mo_key not in rows:
            label = mo.erp_mo_id or mo_key[:8]
            rows[mo_key] = {
                "mo_id": mo_key,
                "mo_name": f"MO-{label}",
                "mo_version": int(float(mo.version or 1)),
                "approved": mo.planned_start is not None and mo.ai_suggested_start is None,
                "operations": [],
            }

        start_min = (wo.planned_start - base).total_seconds() / 60.0 if wo.planned_start else 0
        end_min = (wo.planned_end - base).total_seconds() / 60.0 if wo.planned_end else 0
        rows[mo_key]["operations"].append({
            "id": str(wo.id),
            "operation_id": str(routing.id),
            "mo_id": mo_key,
            "mo_name": rows[mo_key]["mo_name"],
            "sequence": int(wo.sequence),
            "work_center_id": str(wc.id),
            "work_center_name": wc.name or str(wc.id),
            "planned_start": round(start_min, 2),
            "planned_end": round(end_min, 2),
            "duration": float(wo.duration_planned_mins or max(0, end_min - start_min)),
            "status": wo.status,
            "work_order_version": int(wo.version or 1),
        })

    return list(rows.values())
