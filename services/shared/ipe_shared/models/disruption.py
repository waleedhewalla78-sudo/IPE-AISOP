from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class DisruptionEvent(Base, TenantScopedMixin):
    __tablename__ = "cdm_disruption_event"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    mo_id = Column(UUID, ForeignKey("cdm_manufacturing_order.id"))
    work_order_id = Column(UUID)
    work_center_id = Column(UUID, ForeignKey("cdm_work_center.id"))
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text)
    detected_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    event_metadata = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
