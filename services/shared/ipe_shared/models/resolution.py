from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class ResolutionScenario(Base, TenantScopedMixin):
    __tablename__ = "cdm_resolution_scenario"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    mo_id = Column(
        UUID, ForeignKey("cdm_manufacturing_order.id", ondelete="CASCADE"), nullable=False
    )
    strategy = Column(String(32), nullable=False)
    description = Column(Text, nullable=False)
    delivery_impact_days = Column(Numeric(6, 2))
    cost_impact = Column(Numeric(14, 2))
    business_score = Column(Numeric(8, 4))
    affected_mo_ids = Column("affected_mo_ids", ARRAY(UUID), server_default="{}")
    status = Column(String(16), server_default="proposed")
    approved_by = Column(String(128))
    approved_at = Column(DateTime(timezone=True))
    comment = Column(Text, server_default="")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('proposed','approved','rejected','expired')", name="ck_resolution_status"
        ),
    )
