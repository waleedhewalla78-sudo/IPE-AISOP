from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select as sa_select

from app.core.scheduler import solve_schedule
from ipe_shared.database.session import get_session
from ipe_shared.events.producer import kafka_producer
from ipe_shared.events.schemas import EventEnvelope
from ipe_shared.models.bom import BillOfMaterial
from ipe_shared.models.manufacturing_order import ManufacturingOrder
from ipe_shared.models.routing import RoutingOperation
from ipe_shared.models.work_order import WorkOrder


async def handle_workcenter_status_changed(event: dict):
    value = event.value if hasattr(event, "value") else event
    if isinstance(value, dict):
        envelope = EventEnvelope(**value)
    else:
        return
    data = envelope.data
    wc_id = data.get("work_center_id", data.get("id", "unknown"))
    await kafka_producer.send_event(
        "workcenter", "bottleneck_detected",
        key=wc_id,
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.workcenter.bottleneck_detected",
            source="cap-svc",
            tenant_id=envelope.tenant_id,
            timestamp=datetime.now(UTC),
            data={
                "work_center_id": wc_id,
                "status": data.get("status", "unknown"),
                "message": f"Work center {wc_id} status changed to {data.get('status', 'unknown')}",
            },
            correlation_id=envelope.correlation_id,
        ).model_dump(mode="json"),
    )


async def handle_disruption_detected(event: dict):
    """Re-solve schedule when a disruption is detected.

    Listens on ipe.disruption.detected, identifies frozen in-progress
    work orders, re-runs solver with frozen horizon, and emits
    ipe.schedule.updated.
    """
    value = event.value if hasattr(event, "value") else event
    if isinstance(value, dict):
        envelope = EventEnvelope(**value)
    else:
        return
    data = envelope.data
    tenant_id = envelope.tenant_id

    async with get_session() as session:
        wo_result = await session.execute(
            sa_select(WorkOrder).where(
                WorkOrder.tenant_id == tenant_id,
                WorkOrder.status.in_(["in_progress", "completed"]),
            )
        )
        frozen_wos = wo_result.scalars().all()

        mo_result = await session.execute(
            sa_select(ManufacturingOrder).where(
                ManufacturingOrder.tenant_id == tenant_id,
                ManufacturingOrder.status.in_(["confirmed", "in_progress"]),
            )
        )
        mos = mo_result.scalars().all()

        routing_result = await session.execute(
            sa_select(RoutingOperation).where(RoutingOperation.tenant_id == tenant_id)
        )
        routing_map = {str(r.id): r for r in routing_result.scalars().all()}

        bom_result = await session.execute(
            sa_select(BillOfMaterial).where(BillOfMaterial.tenant_id == tenant_id)
        )
        bom_map = {str(b.id): b for b in bom_result.scalars().all()}

    now = datetime.now(UTC)
    ops = []
    frozen_ops = []

    for wo in frozen_wos:
        if wo.planned_start and wo.planned_end:
            frozen_ops.append({
                "operation_id": str(wo.id),
                "fixed_start": int((wo.planned_start - now).total_seconds() / 60),
                "fixed_end": int((wo.planned_end - now).total_seconds() / 60),
            })

    for mo in mos:
        for wo in frozen_wos:
            if str(wo.mo_id) == str(mo.id):
                due = None
                if mo.planned_end:
                    due = max(0, int((mo.planned_end - now).total_seconds() / 60))

                routing = routing_map.get(str(wo.id))
                bom = bom_map.get(str(mo.bom_id)) if mo.bom_id else None

                ops.append({
                    "id": str(wo.id),
                    "mo_id": str(mo.id),
                    "sequence": int(wo.sequence),
                    "work_center_id": str(wo.work_center_id),
                    "duration_planned_mins": int(wo.duration_planned_mins or 60),
                    "due_date_minutes": due,
                    "priority_score": float(mo.feasibility_score or 0.5),
                    "parent_operation_id": str(routing.parent_operation_id) if routing and routing.parent_operation_id else None,
                    "bom_level": int(routing.bom_level or 0) if routing and routing.bom_level is not None else int(bom.bom_level or 0) if bom else 0,
                    "transfer_time_mins": int(routing.transfer_time_mins or 0) if routing and routing.transfer_time_mins is not None else 0,
                    "is_phantom": bool(bom.is_phantom) if bom else False,
                })

    if not ops:
        return

    horizon = 14 * 24 * 60
    schedule = solve_schedule(
        [], ops, horizon=horizon,
        solver_timeout_seconds=5,
        frozen_ops=frozen_ops,
    )

    affected_mo_ids = list({op["mo_id"] for op in ops})
    async with get_session() as session:
        for mo in mos:
            mo.ai_schedule_version = (mo.ai_schedule_version or 0) + 1
            mo.disruption_status = "resolved" if schedule.get("status") in ("OPTIMAL", "FEASIBLE") else "impacted"
            session.add(mo)
        await session.commit()

    await kafka_producer.send_event(
        "schedule", "updated",
        key=str(tenant_id),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.schedule.updated",
            source="cap-svc",
            tenant_id=tenant_id,
            timestamp=datetime.now(UTC),
            data={
                "schedule_version": mo.ai_schedule_version if mos else 0,
                "affected_mo_ids": affected_mo_ids,
                "solver_status": schedule.get("status", "UNKNOWN"),
                "replan_reason": data.get("disruption_type", "unknown"),
            },
        ).model_dump(mode="json"),
    )


async def handle_maintenance_block_required(event: dict):
    """Inject maintenance block and trigger partial re-solve for affected MOs."""
    value = event.value if hasattr(event, "value") else event
    payload = value
    if isinstance(value, dict) and "payload" in value:
        payload = value["payload"]
    elif isinstance(value, dict) and "data" in value:
        payload = value["data"]

    if not isinstance(payload, dict):
        return

    tenant_id = payload.get("tenant_id") or (value.get("tenant_id") if isinstance(value, dict) else None)
    if not tenant_id and isinstance(value, dict):
        tenant_id = value.get("tenant_id")
    work_center_id = payload.get("work_center_id")
    machine_id = payload.get("machine_id", "unknown")

    if not tenant_id or not work_center_id:
        return

    from datetime import datetime as dt

    from app.core.maintenance_blocks import (
        compute_block_window,
        partial_reschedule_for_block,
        register_maintenance_block,
    )
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from ipe_shared.database.connection import get_engine

    block_start_raw = payload.get("block_start")
    block_end_raw = payload.get("block_end")
    rul_hours = float(payload.get("rul_hours", 36))

    if block_start_raw and block_end_raw:
        block_start = dt.fromisoformat(str(block_start_raw).replace("Z", "+00:00"))
        block_end = dt.fromisoformat(str(block_end_raw).replace("Z", "+00:00"))
    else:
        block_start, block_end = compute_block_window(rul_hours=rul_hours)

    register_maintenance_block(
        tenant_id=str(tenant_id),
        machine_id=machine_id,
        work_center_id=str(work_center_id),
        block_start=block_start,
        block_end=block_end,
        rul_hours=rul_hours,
    )

    engine = get_engine()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        result = await partial_reschedule_for_block(
            session,
            UUID(str(tenant_id)),
            str(work_center_id),
            solver_timeout_seconds=30,
        )

    await kafka_producer.send_event(
        "schedule", "updated",
        key=str(tenant_id),
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.schedule.updated",
            source="cap-svc",
            tenant_id=UUID(str(tenant_id)),
            timestamp=datetime.now(UTC),
            data={
                "affected_mo_ids": result.get("affected_mo_ids", []),
                "solver_status": result.get("solver_status", "UNKNOWN"),
                "replan_reason": "maintenance_block_required",
                "work_center_id": work_center_id,
                "machine_id": machine_id,
            },
        ).model_dump(mode="json"),
    )


async def handle_operator_absence(event: dict):
    value = event.value if hasattr(event, "value") else event
    if isinstance(value, dict):
        envelope = EventEnvelope(**value)
    else:
        return
    data = envelope.data
    operator_id = data.get("operator_id", "unknown")
    await kafka_producer.send_event(
        "delay", "logged",
        key=operator_id,
        value=EventEnvelope(
            event_id=str(uuid4()),
            event_type="ipe.delay.logged",
            source="cap-svc",
            tenant_id=envelope.tenant_id,
            timestamp=datetime.now(UTC),
            data={
                "source_text": f"Operator absence: {operator_id}",
                "cause_category": "labor_absence",
                "confidence": 0.85,
                "mo_id": data.get("mo_id", ""),
            },
            correlation_id=envelope.correlation_id,
        ).model_dump(mode="json"),
    )
