from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class EdgeSyncPayload(BaseModel):
    entity_type: str
    entity_id: str
    operation: str = Field(..., pattern="^(create|update|delete)$")
    payload: dict[str, Any]
    local_timestamp: datetime
    version: int = 1


class EdgeSyncBatchRequest(BaseModel):
    batch_id: str
    gateway_id: str
    batch_type: str = Field(default="operations", pattern="^(operations|schedule_pull|heartbeat)$")
    records: list[EdgeSyncPayload]
    local_timestamp: datetime
    metadata: dict[str, Any] | None = None


class EdgeSyncConflict(BaseModel):
    entity_type: str
    entity_id: str
    conflict_type: str
    cloud_version: dict[str, Any]
    edge_version: dict[str, Any]
    resolution: str
    requires_manual: bool


class EdgeSyncBatchResponse(BaseModel):
    batch_id: str
    status: str
    records_processed: int
    records_accepted: int
    records_rejected: int
    conflicts: list[EdgeSyncConflict]
    next_sync_token: str | None = None


class EdgeSchedulePullRequest(BaseModel):
    gateway_id: str
    last_sync_token: str | None = None
    hours_ahead: int = Field(default=24, ge=1, le=72)
    entity_types: list[str] = Field(default_factory=lambda: ["manufacturing_order", "work_order"])


class EdgeScheduleDeltaResponse(BaseModel):
    deltas: list[dict[str, Any]]
    sync_token: str
    has_more: bool
    delta_count: int


class EdgeGatewayAuth(BaseModel):
    gateway_id: str
    api_key: str


class EdgeGatewayRegisterRequest(BaseModel):
    gateway_id: str
    gateway_name: str
    gateway_type: str = "standard"
    plant_id: str | None = None
    location: str | None = None
    api_key: str
    sync_interval_seconds: int = 60
    max_batch_size: int = 100
