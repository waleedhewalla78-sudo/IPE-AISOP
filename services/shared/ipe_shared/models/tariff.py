from sqlalchemy import Column, DateTime, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class TariffSchedule(Base, TenantScopedMixin):
    __tablename__ = "udm_tariff_schedule"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    day_of_week = Column(Integer, nullable=False)
    hour_start = Column(Integer, nullable=False)
    hour_end = Column(Integer, nullable=False)
    rate_per_kwh = Column(Numeric(10, 4), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
