from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class RoutingOperation(Base, TenantScopedMixin):
    __tablename__ = "cdm_routing_operation"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    bom_id = Column(
        UUID, ForeignKey("cdm_bill_of_material.id", ondelete="CASCADE"), nullable=False
    )
    parent_operation_id = Column(UUID, ForeignKey("cdm_routing_operation.id"))
    bom_level = Column(Integer, server_default="0")
    transfer_time_mins = Column(Integer, server_default="0")
    sequence = Column(SmallInteger, nullable=False)
    work_center_id = Column(UUID, ForeignKey("cdm_work_center.id"), nullable=False)
    operation_name = Column(String(256))
    duration_planned_mins = Column(Numeric(10, 2), nullable=False)
    setup_time_mins = Column(Numeric(10, 2), server_default="0")
    duration_predicted_mins = Column(Numeric(10, 2))
    prediction_confidence = Column(Numeric(5, 4))
    required_skill_tags = Column(JSONB, server_default="[]")
    required_skill_id = Column(UUID, ForeignKey("cdm_skill.id"))
    requires_operator = Column(Boolean, server_default="true")
    min_operators = Column(SmallInteger, server_default="1")
    subcontract_eligible = Column(Boolean, server_default="false")
    subcontract_cost = Column(Numeric(14, 2))
    subcontract_lead_days = Column(Numeric(6, 2))
