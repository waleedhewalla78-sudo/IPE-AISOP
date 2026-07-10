from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class MaintenanceWindow(Base, TenantScopedMixin):
    __tablename__ = "cdm_maintenance_window"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    work_center_id = Column(
        UUID, ForeignKey("cdm_work_center.id", ondelete="CASCADE"), nullable=False
    )
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    type = Column(String(16), nullable=False)
    erp_source_id = Column(String(128))

    __table_args__ = (
        CheckConstraint("type IN ('preventive','corrective','breakdown')", name="ck_maint_type"),
    )
