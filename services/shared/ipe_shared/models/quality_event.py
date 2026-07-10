from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class QualityEvent(Base, TenantScopedMixin):
    __tablename__ = "cdm_quality_event"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    mo_id = Column(UUID, nullable=False, index=True)
    work_order_id = Column(UUID, nullable=True)
    work_center_id = Column(UUID, nullable=True)
    product_id = Column(UUID, nullable=False)
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default="minor")
    defect_category = Column(String(100), nullable=True)
    defect_count = Column(Integer, nullable=False, default=1)
    inspection_method = Column(String(50), nullable=True)
    root_cause = Column(String(255), nullable=True)
    corrective_action = Column(String(255), nullable=True)
    rework_required = Column(Boolean, nullable=False, default=False)
    rework_cycles = Column(Integer, nullable=False, default=0)
    max_rework_cycles = Column(Integer, nullable=False, default=3)
    scrap_quantity = Column(Integer, nullable=False, default=0)
    cost_impact = Column(Float, nullable=True, default=0.0)
    status = Column(String(20), nullable=False, default="open")
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
