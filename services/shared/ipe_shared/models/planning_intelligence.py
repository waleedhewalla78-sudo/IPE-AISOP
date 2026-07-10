"""Planning intelligence CDM models — segmentation, forecast quality, safety stock, capacity, S&OP."""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ipe_shared.database.base import Base
from ipe_shared.database.tenant import TenantScopedMixin


class ProductSegment(Base, TenantScopedMixin):
    __tablename__ = "cdm_product_segment"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    segmentation_date = Column(Date, nullable=False)
    abc_class = Column(String(1), nullable=False)
    revenue_total = Column(Numeric(18, 2))
    revenue_share_pct = Column(Numeric(8, 4))
    cumulative_revenue_pct = Column(Numeric(8, 4))
    xyz_class = Column(String(1), nullable=False)
    demand_cv = Column(Numeric(8, 4))
    demand_mean = Column(Numeric(18, 4))
    demand_stddev = Column(Numeric(18, 4))
    combined_segment = Column(String(2), nullable=False)
    target_service_level_pct = Column(Numeric(5, 2))
    forecast_model_recommendation = Column(String(50))
    review_frequency = Column(String(20))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SegmentationConfig(Base, TenantScopedMixin):
    __tablename__ = "cdm_segmentation_config"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_segmentation_config_tenant"),)

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    abc_a_threshold_pct = Column(Numeric(5, 2), nullable=False, server_default="80.0")
    abc_b_threshold_pct = Column(Numeric(5, 2), nullable=False, server_default="95.0")
    xyz_x_threshold = Column(Numeric(5, 2), nullable=False, server_default="0.5")
    xyz_y_threshold = Column(Numeric(5, 2), nullable=False, server_default="1.0")
    service_level_ax = Column(Numeric(5, 2), nullable=False, server_default="99.0")
    service_level_ay = Column(Numeric(5, 2), nullable=False, server_default="97.0")
    service_level_az = Column(Numeric(5, 2), nullable=False, server_default="95.0")
    service_level_bx = Column(Numeric(5, 2), nullable=False, server_default="97.0")
    service_level_by = Column(Numeric(5, 2), nullable=False, server_default="95.0")
    service_level_bz = Column(Numeric(5, 2), nullable=False, server_default="90.0")
    service_level_cx = Column(Numeric(5, 2), nullable=False, server_default="95.0")
    service_level_cy = Column(Numeric(5, 2), nullable=False, server_default="90.0")
    service_level_cz = Column(Numeric(5, 2), nullable=False, server_default="85.0")
    history_months = Column(Integer, nullable=False, server_default="12")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ForecastSnapshot(Base, TenantScopedMixin):
    __tablename__ = "cdm_forecast_snapshot"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    location_id = Column(UUID, ForeignKey("cdm_plant.id"))
    snapshot_date = Column(Date, nullable=False)
    target_period_start = Column(Date, nullable=False)
    target_period_type = Column(String(10), nullable=False, server_default="month")
    forecast_qty = Column(Numeric(18, 4), nullable=False)
    forecast_source = Column(String(50), nullable=False)
    model_id = Column(String(100))
    model_version = Column(String(50))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ForecastError(Base, TenantScopedMixin):
    __tablename__ = "cdm_forecast_error"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    location_id = Column(UUID)
    period_start = Column(Date, nullable=False)
    period_type = Column(String(10), nullable=False, server_default="month")
    lag_periods = Column(Integer, nullable=False)
    forecast_source = Column(String(50), nullable=False)
    forecast_qty = Column(Numeric(18, 4))
    actuals_qty = Column(Numeric(18, 4))
    absolute_error = Column(Numeric(18, 4))
    error_pct = Column(Numeric(10, 4))
    bias = Column(Numeric(18, 4))
    bias_pct = Column(Numeric(10, 4))
    mase_component = Column(Numeric(10, 4))
    calculated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ForecastStability(Base, TenantScopedMixin):
    __tablename__ = "cdm_forecast_stability"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    target_period_start = Column(Date, nullable=False)
    cycle_date = Column(Date, nullable=False)
    prior_cycle_date = Column(Date)
    current_forecast_qty = Column(Numeric(18, 4))
    prior_forecast_qty = Column(Numeric(18, 4))
    change_qty = Column(Numeric(18, 4))
    change_pct = Column(Numeric(10, 4))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class LeadTimeHistory(Base, TenantScopedMixin):
    __tablename__ = "cdm_lead_time_history"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    supplier_id = Column(UUID, ForeignKey("cdm_supplier.id"))
    po_erp_id = Column(String(100))
    order_date = Column(Date)
    expected_date = Column(Date)
    actual_receipt_date = Column(Date)
    lead_time_days = Column(Integer)
    lead_time_variance_days = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SafetyStockRecord(Base, TenantScopedMixin):
    __tablename__ = "cdm_safety_stock"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    location_id = Column(UUID, ForeignKey("cdm_plant.id"))
    calculation_date = Column(Date, nullable=False)
    service_level_target_pct = Column(Numeric(5, 2))
    z_score = Column(Numeric(6, 4))
    avg_demand_per_period = Column(Numeric(18, 4))
    demand_stddev = Column(Numeric(18, 4))
    demand_cv = Column(Numeric(8, 4))
    avg_lead_time_periods = Column(Numeric(10, 2))
    lead_time_stddev = Column(Numeric(10, 2))
    lead_time_cv = Column(Numeric(8, 4))
    safety_stock_qty = Column(Numeric(18, 4))
    safety_stock_demand_component = Column(Numeric(18, 4))
    safety_stock_leadtime_component = Column(Numeric(18, 4))
    reorder_point_qty = Column(Numeric(18, 4))
    current_stock_qty = Column(Numeric(18, 4))
    delta_qty = Column(Numeric(18, 4))
    delta_pct = Column(Numeric(10, 4))
    prior_safety_stock_qty = Column(Numeric(18, 4))
    cycle_change_qty = Column(Numeric(18, 4))
    unit_cost = Column(Numeric(18, 4))
    safety_stock_value = Column(Numeric(18, 2))
    delta_value = Column(Numeric(18, 2))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CapacityUtilisation(Base, TenantScopedMixin):
    __tablename__ = "cdm_capacity_utilisation"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    work_center_id = Column(UUID, ForeignKey("cdm_work_center.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_type = Column(String(10), nullable=False, server_default="week")
    capacity_available_hours = Column(Numeric(10, 2))
    capacity_used_hours = Column(Numeric(10, 2))
    utilisation_pct = Column(Numeric(6, 2))
    overload = Column(Boolean, nullable=False, server_default="false")
    overload_hours = Column(Numeric(10, 2), nullable=False, server_default="0")
    calculated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CapacityAlertConfig(Base, TenantScopedMixin):
    __tablename__ = "cdm_capacity_alert_config"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_capacity_alert_config_tenant"),)

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    overload_threshold_pct = Column(Numeric(5, 2), nullable=False, server_default="90.0")
    critical_threshold_pct = Column(Numeric(5, 2), nullable=False, server_default="100.0")
    alert_enabled = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SopCycle(Base, TenantScopedMixin):
    __tablename__ = "cdm_sop_cycle"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    cycle_name = Column(String(100))
    cycle_month = Column(Date, nullable=False)
    status = Column(String(30), nullable=False, server_default="draft")
    demand_review_deadline = Column(DateTime(timezone=True))
    supply_review_deadline = Column(DateTime(timezone=True))
    reconciliation_deadline = Column(DateTime(timezone=True))
    management_review_deadline = Column(DateTime(timezone=True))
    created_by = Column(UUID)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    closed_at = Column(DateTime(timezone=True))


class SopVersion(Base, TenantScopedMixin):
    __tablename__ = "cdm_sop_version"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    cycle_id = Column(UUID, ForeignKey("cdm_sop_cycle.id", ondelete="CASCADE"), nullable=False)
    version_type = Column(String(20), nullable=False)
    version_name = Column(String(100))
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_by = Column(UUID)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ConsensusDemand(Base, TenantScopedMixin):
    __tablename__ = "cdm_consensus_demand"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    version_id = Column(UUID, ForeignKey("cdm_sop_version.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID, ForeignKey("cdm_product.id"), nullable=False)
    location_id = Column(UUID)
    customer_id = Column(UUID)
    period_start = Column(Date, nullable=False)
    period_type = Column(String(10), nullable=False, server_default="month")
    sales_forecast_qty = Column(Numeric(18, 4))
    marketing_forecast_qty = Column(Numeric(18, 4))
    statistical_forecast_qty = Column(Numeric(18, 4))
    finance_plan_qty = Column(Numeric(18, 4))
    consensus_qty = Column(Numeric(18, 4))
    planned_price = Column(Numeric(18, 4))
    consensus_revenue = Column(Numeric(18, 2))
    cost_per_unit = Column(Numeric(18, 4))
    consensus_cost = Column(Numeric(18, 2))
    consensus_profit = Column(Numeric(18, 2))
    constrained_demand_qty = Column(Numeric(18, 4))
    constrained_revenue = Column(Numeric(18, 2))
    lost_sales_qty = Column(Numeric(18, 4))
    lost_sales_value = Column(Numeric(18, 2))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SopStageGate(Base, TenantScopedMixin):
    __tablename__ = "cdm_sop_stage_gate"

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    cycle_id = Column(UUID, ForeignKey("cdm_sop_cycle.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, server_default="pending")
    approved_by = Column(UUID)
    approved_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class SopConsensusWeight(Base, TenantScopedMixin):
    __tablename__ = "cdm_sop_consensus_weight"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_sop_consensus_weight_tenant"),)

    id = Column(UUID, primary_key=True, server_default=func.gen_random_uuid())
    weight_sales = Column(Numeric(5, 2), nullable=False, server_default="0.30")
    weight_statistical = Column(Numeric(5, 2), nullable=False, server_default="0.40")
    weight_marketing = Column(Numeric(5, 2), nullable=False, server_default="0.20")
    weight_finance = Column(Numeric(5, 2), nullable=False, server_default="0.10")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
