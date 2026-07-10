from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class ManufacturingOrder(Base, TenantScopedMixin):
    __tablename__ = "cdm_manufacturing_order"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    erp_mo_id = Column(String(128))
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    bom_id = Column(UUID, ForeignKey("cdm_bill_of_material.id"), nullable=False)
    quantity = Column(Numeric(14, 4), nullable=False)
    planned_start = Column(DateTime(timezone=True))
    planned_end = Column(DateTime(timezone=True))
    actual_start = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))
    feasibility_score = Column(Numeric(5, 2))
    material_score = Column(Numeric(5, 2))
    capacity_score = Column(Numeric(5, 2))
    labor_score = Column(Numeric(5, 2))
    primary_constraint = Column(String(24))
    version = Column(Numeric(10), nullable=False, server_default="1")
    status = Column(String(24), nullable=False, server_default="draft")
    autonomy_action = Column(String(24))
    yield_planned = Column(Numeric(14, 4))
    yield_actual = Column(Numeric(14, 4))
    scrap_actual = Column(Numeric(14, 4))
    variance_notes = Column(Text)
    ai_suggested_start = Column(DateTime(timezone=True))
    ai_suggested_end = Column(DateTime(timezone=True))
    ai_schedule_version = Column(Integer, server_default="0")
    active_schedule_id = Column(UUID)
    disruption_status = Column(
        String(20), nullable=False, server_default="none"
    )
    erp_last_update = Column(DateTime(timezone=True))
    erp_synced_at = Column(DateTime(timezone=True))
    sync_conflict = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','planned','confirmed','in_progress','completed','cancelled')",
            name="ck_mo_status",
        ),
        CheckConstraint(
            "disruption_status IN ('none','impacted','resolved')",
            name="ck_mo_disruption_status",
        ),
    )
