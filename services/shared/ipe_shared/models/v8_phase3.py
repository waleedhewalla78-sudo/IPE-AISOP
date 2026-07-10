from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class EngineeringMaterial(Base, TenantScopedMixin):
    __tablename__ = "cdm_engineering_material"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(128), nullable=False)
    grade = Column(String(64))
    category = Column(String(64), server_default="metal")
    properties_jsonb = Column(JSONB, server_default="{}")
    cost_per_kg = Column(Numeric(12, 4), server_default="0")
    sustainability_score = Column(Numeric(5, 2), server_default="50")
    suppliers_jsonb = Column(JSONB, server_default="[]")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DesignRecommendation(Base, TenantScopedMixin):
    __tablename__ = "cdm_design_recommendation"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    analysis_id = Column(UUID)
    material_id = Column(UUID, ForeignKey("cdm_engineering_material.id"))
    score = Column(Numeric(6, 4), nullable=False)
    rationale = Column(Text)
    alternatives_jsonb = Column(JSONB, server_default="[]")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DesignRule(Base, TenantScopedMixin):
    __tablename__ = "cdm_design_rule"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    process_type = Column(String(64), nullable=False)
    constraint_type = Column(String(64), nullable=False)
    parameter_key = Column(String(64), nullable=False)
    min_value = Column(Numeric(14, 4))
    max_value = Column(Numeric(14, 4))
    unit = Column(String(16))


class ProcurementSpend(Base, TenantScopedMixin):
    __tablename__ = "cdm_procurement_spend"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    supplier_id = Column(UUID, ForeignKey("cdm_supplier.id"))
    category = Column(String(64), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(8), server_default="USD")
    period = Column(String(16), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ProcurementComplianceCheck(Base, TenantScopedMixin):
    __tablename__ = "cdm_procurement_compliance_check"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    supplier_id = Column(UUID, ForeignKey("cdm_supplier.id"), nullable=False)
    rule_id = Column(String(64), nullable=False)
    result = Column(String(16), nullable=False)
    evidence_jsonb = Column(JSONB, server_default="{}")
    checked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
