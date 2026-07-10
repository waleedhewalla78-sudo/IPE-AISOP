from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class EdgeSyncBatch(Base, TenantScopedMixin):
    __tablename__ = "cdm_edge_sync_batch"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    batch_id = Column(String(255), nullable=False, unique=True, index=True)
    gateway_id = Column(String(255), nullable=False, index=True)
    batch_type = Column(String(50), nullable=False)
    record_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="pending")
    conflict_count = Column(Integer, nullable=False, default=0)
    local_timestamp = Column(DateTime(timezone=True), nullable=False)
    cloud_received_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EdgeSyncRecord(Base, TenantScopedMixin):
    __tablename__ = "cdm_edge_sync_record"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    batch_id = Column(String(255), nullable=False, index=True)
    gateway_id = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(255), nullable=False)
    operation = Column(String(20), nullable=False)
    payload = Column(JSON, nullable=False)
    local_timestamp = Column(DateTime(timezone=True), nullable=False)
    cloud_processed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    conflict_status = Column(String(50), nullable=True)
    conflict_details = Column(JSON, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EdgeScheduleDelta(Base, TenantScopedMixin):
    __tablename__ = "cdm_edge_schedule_delta"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    gateway_id = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(255), nullable=False)
    delta_type = Column(String(20), nullable=False)
    payload = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    checksum = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    synced_at = Column(DateTime(timezone=True), nullable=True)


class EdgeGateway(Base, TenantScopedMixin):
    __tablename__ = "cdm_edge_gateway"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    gateway_id = Column(String(255), nullable=False, unique=True, index=True)
    gateway_name = Column(String(255), nullable=False)
    gateway_type = Column(String(50), nullable=False, default="standard")
    plant_id = Column(UUID, nullable=True)
    location = Column(String(255), nullable=True)
    api_key_hash = Column(String(255), nullable=True)
    mtls_cert_serial = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_status = Column(String(20), nullable=True)
    sync_interval_seconds = Column(Integer, nullable=False, default=60)
    max_batch_size = Column(Integer, nullable=False, default=100)
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
