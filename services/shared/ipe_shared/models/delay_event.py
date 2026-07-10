from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class DelayEvent(Base, TenantScopedMixin):
    __tablename__ = "cdm_delay_event"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    mo_id = Column(
        UUID, ForeignKey("cdm_manufacturing_order.id", ondelete="CASCADE"), nullable=False
    )
    work_order_id = Column(UUID, ForeignKey("cdm_work_order.id"))
    cause_category = Column(String(32), nullable=False)
    cause_detail = Column(Text)
    classification_method = Column(String(16), nullable=False)
    classification_confidence = Column(Numeric(5, 4))
    delay_minutes = Column(Integer, nullable=False)
    cost_impact = Column(Numeric(14, 2))
    linked_po_id = Column(UUID, ForeignKey("cdm_supply_order.id"))
    linked_wc_id = Column(UUID, ForeignKey("cdm_work_center.id"))
    linked_operator_id = Column(UUID, ForeignKey("cdm_operator.id"))
    source_text = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
