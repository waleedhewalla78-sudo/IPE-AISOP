from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class CustomerOrder(Base, TenantScopedMixin):
    __tablename__ = "cdm_customer_order"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    customer_id = Column(UUID, ForeignKey("cdm_customer.id"))
    order_number = Column(String(64), nullable=False)
    order_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    requested_date = Column(DateTime(timezone=True))
    promised_date = Column(DateTime(timezone=True))
    status = Column(String(24), server_default="open")
    priority = Column(Integer, server_default="3")
    total_value = Column(Numeric(14, 2), server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CustomerOrderLine(Base, TenantScopedMixin):
    __tablename__ = "cdm_customer_order_line"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    order_id = Column(UUID, ForeignKey("cdm_customer_order.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    quantity = Column(Numeric(14, 4), nullable=False)
    promised_quantity = Column(Numeric(14, 4))
    unit_price = Column(Numeric(14, 4), server_default="0")
    line_status = Column(String(24), server_default="open")


class OrderPromise(Base, TenantScopedMixin):
    __tablename__ = "cdm_order_promise"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    order_line_id = Column(UUID, ForeignKey("cdm_customer_order_line.id", ondelete="CASCADE"), nullable=False)
    facility_id = Column(UUID)
    promise_type = Column(String(8), nullable=False)
    promise_date = Column(DateTime(timezone=True), nullable=False)
    confidence_score = Column(Numeric(5, 4), server_default="0.85")
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SupplyPlan(Base, TenantScopedMixin):
    __tablename__ = "cdm_supply_plan"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    name = Column(String(128), nullable=False)
    horizon_days = Column(Integer, server_default="30")
    status = Column(String(24), server_default="draft")
    plan_jsonb = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EquipmentAsset(Base, TenantScopedMixin):
    __tablename__ = "cdm_equipment_asset"

    id = Column(UUID, primary_key=True, server_default=func.uuid_generate_v4())
    work_center_id = Column(UUID, ForeignKey("cdm_work_center.id"))
    name = Column(String(128), nullable=False)
    asset_type = Column(String(64), server_default="machine")
    location = Column(String(128))
    install_date = Column(DateTime(timezone=True))
    specs_jsonb = Column(JSONB, server_default="{}")
    health_score = Column(Numeric(5, 2), server_default="100")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
