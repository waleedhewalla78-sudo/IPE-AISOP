"""Cross-tool activity feed API (Sprint 7 Tier 1)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ipe_shared.activity.store import list_activity_feed, record_activity_event
from ipe_shared.auth.dependencies import get_current_user
from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.database.session import get_session
from ipe_shared.events.eib import normalize_kafka_message
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

router = APIRouter(prefix="/activity", tags=["activity"])


class ActivityEventOut(BaseModel):
    id: str
    source_tool: str
    event_type: str
    actor_id: str | None
    entity_type: str | None
    entity_id: str | None
    summary: str
    severity: str
    occurred_at: str
    metadata: dict = Field(default_factory=dict)


class ActivityFeedPayload(BaseModel):
    events: list[ActivityEventOut]
    count: int


class ActivityIngestRequest(BaseModel):
    source_tool: str = Field(..., min_length=1, max_length=64)
    event_type: str = Field(..., min_length=1, max_length=128)
    summary: str = Field(..., min_length=1)
    actor_id: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    metadata: dict | None = None
    severity: str = "info"
    occurred_at: datetime | None = None
    idempotency_key: str | None = None


class KafkaIngestRequest(BaseModel):
    topic: str
    envelope: dict


def _serialize_event(row) -> ActivityEventOut:
    return ActivityEventOut(
        id=str(row.id),
        source_tool=row.source_tool,
        event_type=row.event_type,
        actor_id=row.actor_id,
        entity_type=row.entity_type,
        entity_id=str(row.entity_id) if row.entity_id else None,
        summary=row.summary,
        severity=row.severity,
        occurred_at=row.occurred_at.isoformat(),
        metadata=dict(row.metadata_ or {}),
    )


@router.get("/feed", response_model=APIResponse[ActivityFeedPayload])
async def get_activity_feed(
    source_tool: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: TokenPayload = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ActivityFeedPayload]:
    tenant_id = UUID(str(current_user.tenant_id))
    rows = await list_activity_feed(
        session, tenant_id, source_tool=source_tool, limit=limit, offset=offset
    )
    events = [_serialize_event(r) for r in rows]
    return APIResponse(
        data=ActivityFeedPayload(events=events, count=len(events)),
        error=None,
    )


@router.post("/events", response_model=APIResponse[ActivityEventOut])
async def ingest_activity_event(
    body: ActivityIngestRequest,
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
    session: AsyncSession = Depends(get_session),
) -> APIResponse[ActivityEventOut]:
    tenant_id = UUID(str(current_user.tenant_id))
    entity_uuid = UUID(body.entity_id) if body.entity_id else None
    row = await record_activity_event(
        session,
        tenant_id=tenant_id,
        source_tool=body.source_tool,
        event_type=body.event_type,
        summary=body.summary,
        actor_id=body.actor_id or current_user.sub,
        entity_type=body.entity_type,
        entity_id=entity_uuid,
        metadata=body.metadata,
        severity=body.severity,
        occurred_at=body.occurred_at,
        idempotency_key=body.idempotency_key,
    )
    return APIResponse(data=_serialize_event(row), error=None)


@router.post("/ingest/kafka", response_model=APIResponse[ActivityEventOut])
async def ingest_from_kafka_envelope(
    body: KafkaIngestRequest,
    session: AsyncSession = Depends(get_session),
    current_user: TokenPayload = Depends(require_roles(["admin"])),
) -> APIResponse[ActivityEventOut]:
    """Normalize a Kafka envelope into the activity store (EIB path)."""
    normalized = normalize_kafka_message(
        body.topic, body.envelope, tenant_id=current_user.tenant_id
    )
    if not normalized.get("tenant_id"):
        return APIResponse(
            success=False,
            data=None,
            error={"code": "NO_TENANT", "message": "tenant_id required in envelope"},
        )
    entity_uuid = None
    if normalized.get("entity_id"):
        try:
            entity_uuid = UUID(str(normalized["entity_id"]))
        except ValueError:
            entity_uuid = None
    row = await record_activity_event(
        session,
        tenant_id=UUID(str(normalized["tenant_id"])),
        source_tool=normalized["source_tool"],
        event_type=normalized["event_type"],
        summary=normalized["summary"],
        actor_id=normalized.get("actor_id"),
        entity_type=normalized.get("entity_type"),
        entity_id=entity_uuid,
        metadata=normalized.get("metadata"),
        severity=normalized.get("severity", "info"),
        occurred_at=normalized.get("occurred_at"),
        idempotency_key=normalized.get("idempotency_key"),
    )
    return APIResponse(data=_serialize_event(row), error=None)
