from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class WorkCenter(Base, TenantScopedMixin):
    __tablename__ = "cdm_work_center"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    erp_source_id = Column(String(128), nullable=False)
    name = Column(String(256), nullable=False)
    capacity_hours_per_day = Column(Numeric(6, 2), nullable=False)
    oee = Column(Numeric(5, 4), server_default="0.85")
    cost_per_hour = Column(Numeric(10, 2))
    overtime_cost_multiplier = Column(Numeric(4, 2), server_default="1.5")
    max_overtime_hours_per_week = Column(Numeric(5, 2), server_default="10")
    alternative_wc_ids = Column("alternative_wc_ids", ARRAY(UUID), server_default="{}")
    calendar_id = Column(UUID, ForeignKey("cdm_resource_calendar.id"))
    status = Column(String(16), server_default="operational")
    effective_capacity_hours = Column(Numeric(6, 2))
    avg_setup_time_minutes = Column(Numeric(8, 2))
    energy_kwh_per_hour = Column(Numeric(8, 2), server_default="0.0")
    plant_id = Column(UUID, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('operational','maintenance','breakdown','offline')", name="ck_wc_status"
        ),
    )
