from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin

DATA_QUALITY_FLAG_CODES = (
    "MISSING_BOM",
    "MISSING_ROUTING",
    "MISSING_WC",
    "SYNC_CONFLICT",
    "MISSING_PRODUCT",
    "INVALID_QUANTITY",
)


class DataQualityFlag(Base, TenantScopedMixin):
    __tablename__ = "cdm_data_quality_flag"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    mo_id = Column(UUID, ForeignKey("cdm_manufacturing_order.id", ondelete="CASCADE"), nullable=False)
    flag_code = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "flag_code IN ('MISSING_BOM', 'MISSING_ROUTING', 'MISSING_WC', "
            "'SYNC_CONFLICT', 'MISSING_PRODUCT', 'INVALID_QUANTITY')",
            name="ck_data_quality_flag_code",
        ),
    )
