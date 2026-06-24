"""Maintenance calendar blocks for predictive maintenance (V6-R4).

Stores active blocks per tenant and injects them into scheduler context
as fixed-interval operations that consume work-center capacity.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from ipe_shared.solver.interface import OperationInput, SolverContext

RUL_MAINTENANCE_THRESHOLD_HOURS = 48
DEFAULT_BLOCK_DURATION_HOURS = 24

# tenant_id -> list of active maintenance block dicts
_active_blocks: dict[str, list[dict[str, Any]]] = {}


def compute_block_window(
    recorded_at: datetime | None = None,
    rul_hours: float = 36,
) -> tuple[datetime, datetime]:
    """Schedule maintenance block starting next business morning before RUL expires."""
    base = recorded_at or datetime.now(UTC)
    if base.tzinfo is None:
        base = base.replace(tzinfo=UTC)

    lead_hours = max(1.0, min(float(rul_hours), RUL_MAINTENANCE_THRESHOLD_HOURS))
    block_start = base + timedelta(hours=lead_hours)
    block_start = block_start.replace(hour=8, minute=0, second=0, microsecond=0)
    if block_start <= base:
        block_start += timedelta(days=1)
        block_start = block_start.replace(hour=8, minute=0, second=0, microsecond=0)

    block_end = block_start + timedelta(hours=DEFAULT_BLOCK_DURATION_HOURS)
    return block_start, block_end


def register_maintenance_block(
    tenant_id: str,
    machine_id: str,
    work_center_id: str,
    block_start: datetime,
    block_end: datetime,
    rul_hours: float,
) -> dict[str, Any]:
    """Register an active maintenance block for scheduler injection."""
    block = {
        "id": str(uuid4()),
        "tenant_id": tenant_id,
        "machine_id": machine_id,
        "work_center_id": work_center_id,
        "block_start": block_start,
        "block_end": block_end,
        "rul_hours": rul_hours,
    }
    blocks = _active_blocks.setdefault(tenant_id, [])
    blocks = [b for b in blocks if b.get("work_center_id") != work_center_id]
    blocks.append(block)
    _active_blocks[tenant_id] = blocks
    return block


def get_active_maintenance_blocks(tenant_id: str) -> list[dict[str, Any]]:
    """Return non-expired maintenance blocks for a tenant."""
    now = datetime.now(UTC)
    blocks = _active_blocks.get(tenant_id, [])
    active = []
    for block in blocks:
        end = block["block_end"]
        if end.tzinfo is None:
            end = end.replace(tzinfo=UTC)
        if end >= now:
            active.append(block)
    _active_blocks[tenant_id] = active
    return active


def clear_maintenance_blocks(tenant_id: str | None = None) -> None:
    """Clear blocks (primarily for tests)."""
    if tenant_id is None:
        _active_blocks.clear()
    else:
        _active_blocks.pop(tenant_id, None)


def block_to_operation(
    block: dict[str, Any],
    horizon_start: datetime | None = None,
) -> dict[str, Any]:
    """Convert a maintenance block into a scheduler operation dict."""
    base = horizon_start or datetime.now(UTC)
    if base.tzinfo is None:
        base = base.replace(tzinfo=UTC)

    block_start = block["block_start"]
    block_end = block["block_end"]
    if block_start.tzinfo is None:
        block_start = block_start.replace(tzinfo=UTC)
    if block_end.tzinfo is None:
        block_end = block_end.replace(tzinfo=UTC)

    start_minute = max(0, int((block_start - base).total_seconds() / 60))
    duration_mins = max(1, int((block_end - block_start).total_seconds() / 60))

    return {
        "id": f"MAINT_{block['machine_id']}_{block['id'][:8]}",
        "mo_id": f"MAINT_{block['machine_id']}",
        "sequence": 0,
        "work_center_id": block["work_center_id"],
        "duration_planned_mins": duration_mins,
        "fixed_start": start_minute,
        "fixed_end": start_minute + duration_mins,
        "operation_name": f"Predictive Maintenance — {block['machine_id']} (RUL {block['rul_hours']:.0f}h)",
        "due_date_minutes": start_minute + duration_mins,
        "priority_score": 999,
        "material_score": 1.0,
        "requires_operator": False,
        "is_maintenance_block": True,
        "tenant_id": block["tenant_id"],
    }


def inject_maintenance_blocks(
    context: SolverContext,
    tenant_id: str,
    horizon_start: datetime | None = None,
) -> SolverContext:
    """Append maintenance block operations and frozen intervals to solver context."""
    blocks = get_active_maintenance_blocks(tenant_id)
    if not blocks:
        return context

    base = horizon_start or datetime.now(UTC)
    new_ops = list(context.operations)
    new_frozen = list(context.frozen_ops)

    for block in blocks:
        op_dict = block_to_operation(block, base)
        new_ops.append(
            OperationInput(
                id=op_dict["id"],
                mo_id=op_dict["mo_id"],
                sequence=op_dict["sequence"],
                work_center_id=op_dict["work_center_id"],
                duration_planned_mins=op_dict["duration_planned_mins"],
                priority_score=op_dict["priority_score"],
                due_date_minutes=op_dict["due_date_minutes"],
                operation_name=op_dict["operation_name"],
                material_score=op_dict["material_score"],
                requires_operator=False,
            )
        )
        from ipe_shared.solver.interface import FrozenOp

        new_frozen.append(
            FrozenOp(
                operation_id=op_dict["id"],
                fixed_start=op_dict["fixed_start"],
                fixed_end=op_dict["fixed_end"],
            )
        )

    context.operations = new_ops
    context.frozen_ops = new_frozen
    return context


def inject_maintenance_block_operations(
    operations: list[dict],
    frozen_ops: list[dict],
    tenant_id: str,
    horizon_start: datetime | None = None,
) -> tuple[list[dict], list[dict]]:
    """Legacy dict-based injection for direct scheduler calls."""
    blocks = get_active_maintenance_blocks(tenant_id)
    if not blocks:
        return operations, frozen_ops

    ops = list(operations)
    frozen = list(frozen_ops)
    for block in blocks:
        op_dict = block_to_operation(block, horizon_start)
        ops.append(op_dict)
        frozen.append({
            "operation_id": op_dict["id"],
            "fixed_start": op_dict["fixed_start"],
            "fixed_end": op_dict["fixed_end"],
        })
    return ops, frozen


async def partial_reschedule_for_block(
    session,
    tenant_id: UUID,
    work_center_id: str,
    solver_timeout_seconds: int = 30,
) -> dict:
    """Re-solve schedule for MOs affected by a maintenance block on one work center."""
    from datetime import UTC, datetime

    from sqlalchemy import select as sa_select

    from app.core.scheduler import solve_schedule
    from ipe_shared.models.manufacturing_order import ManufacturingOrder
    from ipe_shared.models.work_center import WorkCenter
    from ipe_shared.models.work_order import WorkOrder

    now = datetime.now(UTC)
    wc_result = await session.execute(
        sa_select(WorkCenter).where(WorkCenter.tenant_id == tenant_id)
    )
    work_centers = [
        {"id": str(wc.id), "name": wc.name, "capacity_hours_per_day": float(wc.capacity_hours_per_day or 8)}
        for wc in wc_result.scalars().all()
    ]

    wo_result = await session.execute(
        sa_select(WorkOrder).where(
            WorkOrder.tenant_id == tenant_id,
            WorkOrder.status.in_(["pending", "in_progress"]),
        )
    )
    work_orders = wo_result.scalars().all()
    affected_wos = [wo for wo in work_orders if str(wo.work_center_id) == work_center_id]
    affected_mo_ids = {str(wo.mo_id) for wo in affected_wos}

    if not affected_wos:
        return {
            "solver_status": "NO_AFFECTED_MOS",
            "affected_mo_ids": [],
            "assignments": [],
        }

    mo_result = await session.execute(
        sa_select(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tenant_id,
            ManufacturingOrder.id.in_([wo.mo_id for wo in affected_wos]),
        )
    )
    mo_map = {str(mo.id): mo for mo in mo_result.scalars().all()}

    ops = []
    frozen_ops = []
    for wo in work_orders:
        mo = mo_map.get(str(wo.mo_id))
        due = None
        if mo and mo.planned_end:
            due = max(0, int((mo.planned_end - now).total_seconds() / 60))
        op = {
            "id": str(wo.id),
            "mo_id": str(wo.mo_id),
            "sequence": int(wo.sequence or 0),
            "work_center_id": str(wo.work_center_id),
            "duration_planned_mins": int(wo.duration_planned_mins or 60),
            "due_date_minutes": due,
            "priority_score": float(mo.feasibility_score or 0.5) if mo else 0.5,
        }
        ops.append(op)
        if wo.status == "in_progress" and wo.planned_start and wo.planned_end:
            frozen_ops.append({
                "operation_id": str(wo.id),
                "fixed_start": max(0, int((wo.planned_start - now).total_seconds() / 60)),
                "fixed_end": max(0, int((wo.planned_end - now).total_seconds() / 60)),
            })

    ops, frozen_ops = inject_maintenance_block_operations(
        ops, frozen_ops, str(tenant_id), horizon_start=now,
    )

    horizon = 14 * 24 * 60
    schedule = solve_schedule(
        work_centers,
        ops,
        horizon=horizon,
        solver_timeout_seconds=solver_timeout_seconds,
        frozen_ops=frozen_ops,
    )

    return {
        "solver_status": schedule.get("solver_status", schedule.get("status", "UNKNOWN")),
        "affected_mo_ids": sorted(affected_mo_ids),
        "assignments": schedule.get("assignments", []),
        "mo_tardiness": schedule.get("mo_tardiness", []),
    }
