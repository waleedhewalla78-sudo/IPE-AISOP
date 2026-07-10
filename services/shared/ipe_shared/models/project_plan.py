from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class ProjectPlan(Base, TenantScopedMixin):
    __tablename__ = "cdm_project_plan"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    plan_code = Column(String(64), nullable=False)
    plan_name = Column(String(256), nullable=False)
    description = Column(Text)
    active_version_id = Column(UUID, ForeignKey("cdm_project_plan_version.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class ProjectPlanVersion(Base, TenantScopedMixin):
    __tablename__ = "cdm_project_plan_version"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    plan_id = Column(UUID, ForeignKey("cdm_project_plan.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="false")
    file_name = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    file_sha256 = Column(String(64), nullable=False)
    uploaded_by = Column(UUID)
    upload_notes = Column(Text)
    operations = Column(JSONB, nullable=False, server_default="[]")
    validation_summary = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
