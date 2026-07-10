from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class OtdSnapshot(Base, TenantScopedMixin):
    __tablename__ = "cdm_otd_snapshot"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    snapshot_date = Column(Date, nullable=False)
    period = Column(String(16), nullable=False)
    supplier_id = Column(UUID, nullable=True)
    work_center_id = Column(UUID, nullable=True)
    plant_id = Column(UUID, nullable=True)
    otd_pct = Column(Numeric(5, 1))
    completed_mos = Column(Integer, nullable=False, server_default="0")
    on_time_mos = Column(Integer, nullable=False, server_default="0")
    orders_at_risk = Column(Integer, nullable=False, server_default="0")
    avg_delay_days = Column(Numeric(8, 2))
    chaos_cost_usd = Column(Numeric(14, 2), nullable=False, server_default="0")
    metadata_json = Column("metadata", JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
