from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class WorkOrder(Base, TenantScopedMixin):
    __tablename__ = "cdm_work_order"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    mo_id = Column(
        UUID, ForeignKey("cdm_manufacturing_order.id", ondelete="CASCADE"), nullable=False
    )
    routing_op_id = Column(UUID, ForeignKey("cdm_routing_operation.id"), nullable=False)
    work_center_id = Column(UUID, ForeignKey("cdm_work_center.id"), nullable=False)
    operator_id = Column(UUID, ForeignKey("cdm_operator.id"))
    sequence = Column(SmallInteger, nullable=False)
    planned_start = Column(DateTime(timezone=True))
    planned_end = Column(DateTime(timezone=True))
    actual_start = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))
    duration_planned_mins = Column(Numeric(10, 2))
    duration_actual_mins = Column(Numeric(10, 2))
    status = Column(String(24), nullable=False, server_default="pending")
    version = Column(SmallInteger, nullable=False, server_default="1")
    is_frozen = Column(Boolean, nullable=False, server_default="false")
    frozen_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
