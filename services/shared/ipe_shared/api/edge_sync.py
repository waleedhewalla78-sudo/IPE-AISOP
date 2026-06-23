"""Cloud-side Edge Sync API endpoints.

This module provides the FastAPI endpoints for receiving batched payloads
from Edge Gateways, validating them, applying to live UDM, and returning
schedule deltas.
"""
import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.database.session import get_session as get_db_session
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.models.edge_sync import EdgeSyncBatch, EdgeSyncRecord, EdgeScheduleDelta
from ipe_shared.schemas.common import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/edge", tags=["edge"])


class EdgeSyncPayloadRecord(BaseModel):
    entity_type: str
    entity_id: str
    operation: str = Field(..., pattern="^(create|update|delete)$")
    payload: dict[str, Any]
    local_timestamp: str
    version: int = 1


class EdgeSyncBatchRequest(BaseModel):
    batch_id: str
    gateway_id: str
    batch_type: str = "operations"
    records: list[EdgeSyncPayloadRecord]
    local_timestamp: str
    metadata: dict[str, Any] | None = None


class EdgeConflictInfo(BaseModel):
    entity_type: str
    entity_id: str
    conflict_type: str
    cloud_version: dict[str, Any]
    edge_version: dict[str, Any]
    resolution: str
    requires_manual: bool


class EdgeSchedulePullRequest(BaseModel):
    gateway_id: str
    last_sync_token: str | None = None
    hours_ahead: int = 24
    entity_types: list[str] = ["manufacturing_order", "work_order"]


def _compute_checksum(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _detect_conflict(
    edge_record: dict[str, Any],
    cloud_record: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if cloud_record is None:
        return None

    edge_ts = edge_record.get("local_timestamp", "")
    cloud_ts = str(cloud_record.get("updated_at", cloud_record.get("created_at", "")))

    edge_version = edge_record.get("version", 1)
    cloud_version = cloud_record.get("version", 1)

    if edge_version < cloud_version:
        edge_payload = edge_record.get("payload", {})
        cloud_payload = {k: v for k, v in cloud_record.items() if k not in ("id", "tenant_id", "created_at", "updated_at")}

        is_simple_update = _is_simple_update(edge_payload, cloud_payload)

        if is_simple_update and edge_ts > cloud_ts:
            return {
                "conflict_type": "last_write_wins",
                "resolution": "edge_wins",
                "requires_manual": False,
            }
        elif is_simple_update:
            return {
                "conflict_type": "last_write_wins",
                "resolution": "cloud_wins",
                "requires_manual": False,
            }
        else:
            return {
                "conflict_type": "complex_conflict",
                "resolution": "requires_manual_resolution",
                "requires_manual": True,
            }

    return None


def _is_simple_update(edge_payload: dict[str, Any], cloud_payload: dict[str, Any]) -> bool:
    simple_fields = {
        "actual_qty", "actual_duration_mins", "scrap_qty", "reject_qty",
        "status", "quantity", "duration_mins",
    }
    edge_keys = set(edge_payload.keys()) - {"id", "mo_id", "work_order_id", "version"}
    cloud_keys = set(cloud_payload.keys()) - {"id", "tenant_id", "created_at", "updated_at", "version"}

    changed_keys = edge_keys | cloud_keys
    return changed_keys.issubset(simple_fields)


async def _apply_record(
    record: EdgeSyncPayloadRecord,
    tenant_id: UUID,
    session: AsyncSession,
    gateway_id: str,
    batch_id: str,
    local_timestamp: str,
) -> tuple[str, dict[str, Any] | None]:
    entity_type = record.entity_type
    entity_id = record.entity_id
    operation = record.operation
    payload = record.payload

    cloud_record = await _fetch_cloud_record(session, tenant_id, entity_type, entity_id)

    conflict = _detect_conflict(
        {"payload": payload, "local_timestamp": local_timestamp, "version": record.version},
        cloud_record,
    )

    if conflict and conflict.get("requires_manual"):
        return "conflict", conflict

    if operation == "create":
        if cloud_record:
            return "skipped", {"reason": "already_exists"}
        await _create_entity(session, tenant_id, entity_type, entity_id, payload)
        return "accepted", None

    elif operation == "update":
        if cloud_record:
            if conflict and conflict.get("resolution") == "cloud_wins":
                return "conflict", conflict
            await _update_entity(session, tenant_id, entity_type, entity_id, payload)
            return "accepted", None
        else:
            await _create_entity(session, tenant_id, entity_type, entity_id, payload)
            return "accepted", None

    elif operation == "delete":
        await _delete_entity(session, tenant_id, entity_type, entity_id)
        return "accepted", None

    return "rejected", {"reason": "unknown_operation"}


async def _fetch_cloud_record(
    session: AsyncSession,
    tenant_id: UUID,
    entity_type: str,
    entity_id: str,
) -> dict[str, Any] | None:
    from ipe_shared.models.manufacturing_order import ManufacturingOrder
    from ipe_shared.models.work_order import WorkOrder

    if entity_type in ("manufacturing_order", "edge_operations"):
        result = await session.execute(
            sa_select(ManufacturingOrder).where(
                ManufacturingOrder.tenant_id == tenant_id,
                ManufacturingOrder.id == entity_id,
            )
        )
        record = result.scalar_one_or_none()
        if record:
            return {
                "id": str(record.id),
                "status": record.status,
                "version": getattr(record, "version", 1),
                "updated_at": str(record.updated_at) if hasattr(record, "updated_at") else None,
            }

    elif entity_type == "work_order":
        result = await session.execute(
            sa_select(WorkOrder).where(
                WorkOrder.tenant_id == tenant_id,
                WorkOrder.id == entity_id,
            )
        )
        record = result.scalar_one_or_none()
        if record:
            return {
                "id": str(record.id),
                "status": record.status,
                "version": getattr(record, "version", 1),
            }

    return None


async def _create_entity(
    session: AsyncSession,
    tenant_id: UUID,
    entity_type: str,
    entity_id: str,
    payload: dict[str, Any],
) -> None:
    from ipe_shared.models.manufacturing_order import ManufacturingOrder
    from ipe_shared.models.work_order import WorkOrder

    if entity_type in ("manufacturing_order", "edge_operations"):
        mo = ManufacturingOrder(
            id=UUID(entity_id) if len(entity_id) == 36 else uuid4(),
            tenant_id=tenant_id,
            product_id=UUID(payload["product_id"]) if payload.get("product_id") else uuid4(),
            bom_id=UUID(payload["bom_id"]) if payload.get("bom_id") else uuid4(),
            quantity=payload.get("quantity", 1),
            status=payload.get("status", "planned"),
        )
        session.add(mo)
        await session.commit()

    elif entity_type == "work_order":
        wo = WorkOrder(
            id=UUID(entity_id) if len(entity_id) == 36 else uuid4(),
            tenant_id=tenant_id,
            mo_id=UUID(payload["mo_id"]) if payload.get("mo_id") else uuid4(),
            routing_op_id=UUID(payload["routing_op_id"]) if payload.get("routing_op_id") else uuid4(),
            work_center_id=UUID(payload["work_center_id"]) if payload.get("work_center_id") else uuid4(),
            status=payload.get("status", "pending"),
        )
        session.add(wo)
        await session.commit()


async def _update_entity(
    session: AsyncSession,
    tenant_id: UUID,
    entity_type: str,
    entity_id: str,
    payload: dict[str, Any],
) -> None:
    from ipe_shared.models.manufacturing_order import ManufacturingOrder
    from ipe_shared.models.work_order import WorkOrder

    if entity_type in ("manufacturing_order", "edge_operations"):
        result = await session.execute(
            sa_select(ManufacturingOrder).where(
                ManufacturingOrder.tenant_id == tenant_id,
                ManufacturingOrder.id == entity_id,
            )
        )
        mo = result.scalar_one_or_none()
        if mo:
            for key, value in payload.items():
                if hasattr(mo, key) and key not in ("id", "tenant_id", "created_at"):
                    setattr(mo, key, value)
            mo.version = getattr(mo, "version", 0) + 1
            await session.commit()

    elif entity_type == "work_order":
        result = await session.execute(
            sa_select(WorkOrder).where(
                WorkOrder.tenant_id == tenant_id,
                WorkOrder.id == entity_id,
            )
        )
        wo = result.scalar_one_or_none()
        if wo:
            for key, value in payload.items():
                if hasattr(wo, key) and key not in ("id", "tenant_id", "created_at"):
                    setattr(wo, key, value)
            await session.commit()


async def _delete_entity(
    session: AsyncSession,
    tenant_id: UUID,
    entity_type: str,
    entity_id: str,
) -> None:
    entity_map = {
        "demand_line": "cdm_demand_line",
        "manufacturing_order": "cdm_manufacturing_order",
        "supply_order": "cdm_supply_order",
        "work_order": "cdm_work_order",
    }
    table_name = entity_map.get(entity_type)
    if not table_name:
        logger.warning("Edge sync delete: unknown entity_type=%s", entity_type)
        return

    from sqlalchemy import text

    await session.execute(
        text(
            f"DELETE FROM {table_name} WHERE id = :eid AND tenant_id = :tid"
        ),
        {"eid": entity_id, "tid": str(tenant_id)},
    )
    await session.commit()


@router.post("/sync")
async def edge_sync(
    req: EdgeSyncBatchRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Accept batched payloads from Edge Gateway, validate, and apply to live UDM."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    tid = UUID(tenant_id)

    batch_record = EdgeSyncBatch(
        id=uuid4(),
        tenant_id=tid,
        batch_id=req.batch_id,
        gateway_id=req.gateway_id,
        batch_type=req.batch_type,
        record_count=len(req.records),
        status="processing",
        local_timestamp=datetime.fromisoformat(req.local_timestamp),
        metadata_json=req.metadata,
    )
    session.add(batch_record)
    await session.commit()

    records_accepted = 0
    records_rejected = 0
    conflicts = []
    sync_records = []

    for record_req in req.records:
        sync_record = EdgeSyncRecord(
            id=uuid4(),
            tenant_id=tid,
            batch_id=req.batch_id,
            gateway_id=req.gateway_id,
            entity_type=record_req.entity_type,
            entity_id=record_req.entity_id,
            operation=record_req.operation,
            payload=record_req.payload,
            local_timestamp=datetime.fromisoformat(record_req.local_timestamp),
            version=record_req.version,
        )
        sync_records.append(sync_record)

        status, conflict_info = await _apply_record(
            record_req, tid, session, req.gateway_id, req.batch_id, req.local_timestamp
        )

        if status == "accepted":
            records_accepted += 1
            sync_record.status = "accepted"
            sync_record.cloud_processed_at = datetime.now(UTC)
        elif status == "conflict":
            records_rejected += 1
            sync_record.status = "conflict"
            sync_record.conflict_status = conflict_info.get("resolution", "unknown")
            sync_record.conflict_details = conflict_info
            conflicts.append(EdgeConflictInfo(
                entity_type=record_req.entity_type,
                entity_id=record_req.entity_id,
                conflict_type=conflict_info.get("conflict_type", "unknown"),
                cloud_version={},
                edge_version=record_req.payload,
                resolution=conflict_info.get("resolution", "unknown"),
                requires_manual=conflict_info.get("requires_manual", False),
            ))
        else:
            records_rejected += 1
            sync_record.status = "rejected"

        session.add(sync_record)

    batch_record.status = "completed"
    batch_record.conflict_count = len(conflicts)
    batch_record.processed_at = datetime.now(UTC)
    await session.commit()

    return APIResponse(success=True, data={
        "batch_id": req.batch_id,
        "status": "completed",
        "records_processed": len(req.records),
        "records_accepted": records_accepted,
        "records_rejected": records_rejected,
        "conflicts": [c.model_dump() for c in conflicts],
    }, error=None)


@router.get("/schedule/pull")
async def edge_schedule_pull(
    gateway_id: str,
    last_sync_token: str | None = None,
    hours_ahead: int = 24,
    session: AsyncSession = Depends(get_db_session),
):
    """Pull latest schedule deltas for Edge Gateway."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    tid = UUID(tenant_id)

    from ipe_shared.models.manufacturing_order import ManufacturingOrder
    from datetime import timedelta

    now = datetime.now(UTC)
    future = now + timedelta(hours=hours_ahead)

    result = await session.execute(
        sa_select(ManufacturingOrder).where(
            ManufacturingOrder.tenant_id == tid,
            ManufacturingOrder.planned_start >= now,
            ManufacturingOrder.planned_start <= future,
        )
    )
    mos = result.scalars().all()

    deltas = []
    for mo in mos:
        delta = {
            "entity_type": "manufacturing_order",
            "entity_id": str(mo.id),
            "delta_type": "update",
            "payload": {
                "id": str(mo.id),
                "product_id": str(mo.product_id),
                "quantity": mo.quantity,
                "status": mo.status,
                "planned_start": str(mo.planned_start) if mo.planned_start else None,
                "planned_end": str(mo.planned_end) if mo.planned_end else None,
                "feasibility_score": mo.feasibility_score,
            },
            "version": getattr(mo, "version", 1),
        }
        deltas.append(delta)

    sync_token = f"{gateway_id}_{now.isoformat()}"

    return APIResponse(success=True, data={
        "deltas": deltas,
        "sync_token": sync_token,
        "has_more": len(deltas) >= 100,
        "delta_count": len(deltas),
    }, error=None)


@router.post("/gateway/register")
async def register_gateway(
    gateway_id: str,
    gateway_name: str,
    api_key: str,
    plant_id: str | None = None,
    location: str | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    """Register a new Edge Gateway."""
    tenant_id = tenant_ctx.get()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant context")

    tid = UUID(tenant_id)

    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    from ipe_shared.models.edge_sync import EdgeGateway
    gateway = EdgeGateway(
        id=uuid4(),
        tenant_id=tid,
        gateway_id=gateway_id,
        gateway_name=gateway_name,
        gateway_type="standard",
        plant_id=UUID(plant_id) if plant_id else None,
        location=location,
        api_key_hash=api_key_hash,
        is_active=True,
    )
    session.add(gateway)
    await session.commit()

    return APIResponse(success=True, data={
        "gateway_id": gateway_id,
        "status": "registered",
    }, error=None)
