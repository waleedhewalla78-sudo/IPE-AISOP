from sqlalchemy import Column, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class MachineHealthTelemetry(Base, TenantScopedMixin):
    __tablename__ = "cdm_machine_health_telemetry"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    machine_id = Column(Text, nullable=False)
    work_center_id = Column(UUID, ForeignKey("cdm_work_center.id"))
    rul_hours = Column(Numeric(10, 2), nullable=False)
    vibration_rms = Column(Numeric(10, 4))
    last_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
