"""Sync ORM models with DB schema — add missing columns and tables

Revision ID: 003
Revises: 002
Create Date: 2026-06-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    # ---- cdm_audit_log ----
    op.add_column("cdm_audit_log", sa.Column("rationale", sa.Text))

    # ---- cdm_bill_of_material ----
    op.add_column("cdm_bill_of_material", sa.Column("version", sa.String(16), nullable=False, server_default="1.0"))
    op.add_column("cdm_bill_of_material", sa.Column("erp_source_id", sa.String(128)))

    # ---- cdm_bom_line ----
    op.add_column("cdm_bom_line", sa.Column("uom", sa.String(16), nullable=False, server_default="unit"))
    op.add_column("cdm_bom_line", sa.Column("scrap_rate_pct", sa.Numeric(5, 2), server_default="0"))
    op.add_column("cdm_bom_line", sa.Column("substitute_ids", ARRAY(UUID)))

    # ---- cdm_delay_event ----
    op.add_column("cdm_delay_event", sa.Column("work_order_id", UUID))
    op.add_column("cdm_delay_event", sa.Column("classification_method", sa.String(16)))
    op.add_column("cdm_delay_event", sa.Column("classification_confidence", sa.Numeric(5, 4)))
    op.add_column("cdm_delay_event", sa.Column("cost_impact", sa.Numeric(14, 2)))
    op.add_column("cdm_delay_event", sa.Column("linked_po_id", UUID))
    op.add_column("cdm_delay_event", sa.Column("linked_wc_id", UUID))
    op.add_column("cdm_delay_event", sa.Column("linked_operator_id", UUID))
    op.add_column("cdm_delay_event", sa.Column("source_text", sa.Text))
    op.create_foreign_key("fk_delay_event_work_order", "cdm_delay_event", "cdm_work_order", ["work_order_id"], ["id"])
    op.create_foreign_key("fk_delay_event_supply_order", "cdm_delay_event", "cdm_supply_order", ["linked_po_id"], ["id"])
    op.create_foreign_key("fk_delay_event_work_center", "cdm_delay_event", "cdm_work_center", ["linked_wc_id"], ["id"])
    op.create_foreign_key("fk_delay_event_operator", "cdm_delay_event", "cdm_operator", ["linked_operator_id"], ["id"])

    # ---- cdm_demand_line (critical for dpe-svc) ----
    op.add_column("cdm_demand_line", sa.Column("erp_source_type", sa.String(32), nullable=False, server_default="manual"))
    op.add_column("cdm_demand_line", sa.Column("uom", sa.String(16), nullable=False, server_default="unit"))
    op.add_column("cdm_demand_line", sa.Column("customer_id", UUID))
    op.add_column("cdm_demand_line", sa.Column("customer_tier", sa.Numeric(2, 0), server_default="3"))
    op.add_column("cdm_demand_line", sa.Column("margin_pct", sa.Numeric(6, 2)))
    op.add_column("cdm_demand_line", sa.Column("penalty_cost", sa.Numeric(14, 2), server_default="0"))

    # ---- cdm_customer (new table) ----
    op.create_table(
        "cdm_customer",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("erp_source_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("tier", sa.Numeric(2, 0), server_default="3"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "erp_source_id", name="uq_customer_tenant_erp"),
    )
    op.create_foreign_key("fk_demand_line_customer", "cdm_demand_line", "cdm_customer", ["customer_id"], ["id"])

    # ---- cdm_inventory_position ----
    op.add_column("cdm_inventory_position", sa.Column("qty_in_transit", sa.Numeric(14, 4), nullable=False, server_default="0"))
    op.add_column("cdm_inventory_position", sa.Column("location_id", UUID))
    op.add_column("cdm_inventory_position", sa.Column("time", sa.DateTime(timezone=True)))

    # ---- cdm_manufacturing_order ----
    op.add_column("cdm_manufacturing_order", sa.Column("actual_start", sa.DateTime(timezone=True)))
    op.add_column("cdm_manufacturing_order", sa.Column("actual_end", sa.DateTime(timezone=True)))
    op.add_column("cdm_manufacturing_order", sa.Column("yield_planned", sa.Numeric(14, 4)))
    op.add_column("cdm_manufacturing_order", sa.Column("yield_actual", sa.Numeric(14, 4)))
    op.add_column("cdm_manufacturing_order", sa.Column("scrap_actual", sa.Numeric(14, 4)))
    op.add_column("cdm_manufacturing_order", sa.Column("variance_notes", sa.Text))

    # ---- cdm_operator ----
    op.add_column("cdm_operator", sa.Column("max_consecutive_hours", sa.Numeric(4, 2), server_default="10"))
    op.add_column("cdm_operator", sa.Column("cost_per_hour", sa.Numeric(10, 2)))
    op.add_column("cdm_operator", sa.Column("overtime_eligible", sa.Boolean, server_default=sa.text("true")))
    op.add_column("cdm_operator", sa.Column("predicted_absence_probability", sa.Numeric(5, 4)))

    # ---- cdm_product (critical for dpe-svc) ----
    op.add_column("cdm_product", sa.Column("erp_source_type", sa.String(32), nullable=False, server_default="manufactured"))
    op.add_column("cdm_product", sa.Column("internal_ref", sa.String(64)))
    op.add_column("cdm_product", sa.Column("uom", sa.String(16), nullable=False, server_default="unit"))
    op.add_column("cdm_product", sa.Column("standard_cost", sa.Numeric(14, 4)))
    op.add_column("cdm_product", sa.Column("safety_stock", sa.Numeric(14, 4), server_default="0"))
    op.add_column("cdm_product", sa.Column("category_tags", JSONB, server_default=sa.text("'[]'::jsonb")))
    op.add_column("cdm_product", sa.Column("demand_cv", sa.Numeric(6, 4)))
    op.add_column("cdm_product", sa.Column("avg_monthly_demand", sa.Numeric(14, 4)))
    op.add_column("cdm_product", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    # ---- cdm_resolution_scenario ----
    op.add_column("cdm_resolution_scenario", sa.Column("delivery_impact_days", sa.Numeric(6, 2)))
    op.add_column("cdm_resolution_scenario", sa.Column("cost_impact", sa.Numeric(14, 2)))
    op.add_column("cdm_resolution_scenario", sa.Column("affected_mo_ids", ARRAY(UUID), server_default=sa.text("'{}'::uuid[]")))
    op.add_column("cdm_resolution_scenario", sa.Column("approved_by", sa.String(128)))
    op.add_column("cdm_resolution_scenario", sa.Column("approved_at", sa.DateTime(timezone=True)))
    op.add_column("cdm_resolution_scenario", sa.Column("comment", sa.Text, server_default=""))

    # ---- cdm_resource_calendar (new table) ----
    op.create_table(
        "cdm_resource_calendar",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("entries", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ---- cdm_routing_operation ----
    op.add_column("cdm_routing_operation", sa.Column("operation_name", sa.String(256)))
    op.add_column("cdm_routing_operation", sa.Column("setup_time_mins", sa.Numeric(10, 2), server_default="0"))
    op.add_column("cdm_routing_operation", sa.Column("duration_predicted_mins", sa.Numeric(10, 2)))
    op.add_column("cdm_routing_operation", sa.Column("prediction_confidence", sa.Numeric(5, 4)))
    op.add_column("cdm_routing_operation", sa.Column("required_skill_tags", JSONB, server_default=sa.text("'[]'::jsonb")))
    op.add_column("cdm_routing_operation", sa.Column("min_operators", sa.SmallInteger, server_default="1"))
    op.add_column("cdm_routing_operation", sa.Column("subcontract_eligible", sa.Boolean, server_default=sa.text("false")))
    op.add_column("cdm_routing_operation", sa.Column("subcontract_cost", sa.Numeric(14, 2)))
    op.add_column("cdm_routing_operation", sa.Column("subcontract_lead_days", sa.Numeric(6, 2)))

    # ---- cdm_supplier ----
    op.add_column("cdm_supplier", sa.Column("avg_delay_days", sa.Numeric(6, 2)))
    op.add_column("cdm_supplier", sa.Column("delay_std_dev_days", sa.Numeric(6, 2)))
    op.add_column("cdm_supplier", sa.Column("sample_size", sa.Integer, server_default="0"))
    op.add_column("cdm_supplier", sa.Column("last_model_update", sa.DateTime(timezone=True)))
    op.add_column("cdm_supplier", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    # ---- cdm_supply_order ----
    op.add_column("cdm_supply_order", sa.Column("erp_source_type", sa.String(32), nullable=False, server_default="manual"))
    op.add_column("cdm_supply_order", sa.Column("quantity_received", sa.Numeric(14, 4), server_default="0"))
    op.add_column("cdm_supply_order", sa.Column("reliability_adjusted_date", sa.DateTime(timezone=True)))

    # ---- cdm_tenant ----
    op.add_column("cdm_tenant", sa.Column("erp_version", sa.String(32)))
    op.add_column("cdm_tenant", sa.Column("erp_base_url", sa.String(512)))
    op.add_column("cdm_tenant", sa.Column("api_secret", sa.String(128)))
    op.add_column("cdm_tenant", sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")))
    op.add_column("cdm_tenant", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    # ---- cdm_work_center ----
    op.add_column("cdm_work_center", sa.Column("oee", sa.Numeric(5, 4), server_default="0.85"))
    op.add_column("cdm_work_center", sa.Column("cost_per_hour", sa.Numeric(10, 2)))
    op.add_column("cdm_work_center", sa.Column("overtime_cost_multiplier", sa.Numeric(4, 2), server_default="1.5"))
    op.add_column("cdm_work_center", sa.Column("max_overtime_hours_per_week", sa.Numeric(5, 2), server_default="10"))
    op.add_column("cdm_work_center", sa.Column("alternative_wc_ids", ARRAY(UUID), server_default=sa.text("'{}'::uuid[]")))
    op.add_column("cdm_work_center", sa.Column("calendar_id", UUID))
    op.add_column("cdm_work_center", sa.Column("effective_capacity_hours", sa.Numeric(6, 2)))
    op.add_column("cdm_work_center", sa.Column("avg_setup_time_minutes", sa.Numeric(8, 2)))
    op.add_column("cdm_work_center", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.create_foreign_key("fk_work_center_calendar", "cdm_work_center", "cdm_resource_calendar", ["calendar_id"], ["id"])

    # ---- cdm_work_order ----
    op.add_column("cdm_work_order", sa.Column("planned_start", sa.DateTime(timezone=True)))
    op.add_column("cdm_work_order", sa.Column("planned_end", sa.DateTime(timezone=True)))
    op.add_column("cdm_work_order", sa.Column("actual_start", sa.DateTime(timezone=True)))
    op.add_column("cdm_work_order", sa.Column("actual_end", sa.DateTime(timezone=True)))
    op.add_column("cdm_work_order", sa.Column("duration_planned_mins", sa.Numeric(10, 2)))
    op.add_column("cdm_work_order", sa.Column("duration_actual_mins", sa.Numeric(10, 2)))
    op.add_column("cdm_work_order", sa.Column("notes", sa.Text))
    op.add_column("cdm_work_order", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    # ---- cdm_maintenance_window (new table) ----
    op.create_table(
        "cdm_maintenance_window",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("work_center_id", UUID, sa.ForeignKey("cdm_work_center.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("erp_source_id", sa.String(128)),
    )

    # ---- cdm_user (extra columns from ORM) ----
    op.add_column("cdm_user", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")))

    # ---- operator FK to resource_calendar ----
    op.add_column("cdm_operator", sa.Column("shift_calendar_id", UUID))
    op.create_foreign_key("fk_operator_calendar", "cdm_operator", "cdm_resource_calendar", ["shift_calendar_id"], ["id"])


def downgrade():
    # Reverse: drop FKs, then columns, then tables
    op.drop_constraint("fk_operator_calendar", "cdm_operator")
    op.drop_column("cdm_operator", "shift_calendar_id")

    op.drop_constraint("fk_demand_line_customer", "cdm_demand_line")
    op.drop_constraint("fk_delay_event_operator", "cdm_delay_event")
    op.drop_constraint("fk_delay_event_work_center", "cdm_delay_event")
    op.drop_constraint("fk_delay_event_supply_order", "cdm_delay_event")
    op.drop_constraint("fk_delay_event_work_order", "cdm_delay_event")
    op.drop_constraint("fk_work_center_calendar", "cdm_work_center")

    columns_to_drop = [
        ("cdm_audit_log", ["rationale"]),
        ("cdm_bill_of_material", ["version", "erp_source_id"]),
        ("cdm_bom_line", ["uom", "scrap_rate_pct", "substitute_ids"]),
        ("cdm_delay_event", ["work_order_id", "classification_method", "classification_confidence", "cost_impact", "linked_po_id", "linked_wc_id", "linked_operator_id", "source_text"]),
        ("cdm_demand_line", ["erp_source_type", "uom", "customer_id", "customer_tier", "margin_pct", "penalty_cost"]),
        ("cdm_inventory_position", ["qty_in_transit", "location_id", "time"]),
        ("cdm_manufacturing_order", ["actual_start", "actual_end", "yield_planned", "yield_actual", "scrap_actual", "variance_notes"]),
        ("cdm_operator", ["max_consecutive_hours", "cost_per_hour", "overtime_eligible", "predicted_absence_probability"]),
        ("cdm_product", ["erp_source_type", "internal_ref", "uom", "standard_cost", "safety_stock", "category_tags", "demand_cv", "avg_monthly_demand", "updated_at"]),
        ("cdm_resolution_scenario", ["delivery_impact_days", "cost_impact", "affected_mo_ids", "approved_by", "approved_at", "comment"]),
        ("cdm_routing_operation", ["operation_name", "setup_time_mins", "duration_predicted_mins", "prediction_confidence", "required_skill_tags", "min_operators", "subcontract_eligible", "subcontract_cost", "subcontract_lead_days"]),
        ("cdm_supplier", ["avg_delay_days", "delay_std_dev_days", "sample_size", "last_model_update", "updated_at"]),
        ("cdm_supply_order", ["erp_source_type", "quantity_received", "reliability_adjusted_date"]),
        ("cdm_tenant", ["erp_version", "erp_base_url", "api_secret", "is_active", "updated_at"]),
        ("cdm_work_center", ["oee", "cost_per_hour", "overtime_cost_multiplier", "max_overtime_hours_per_week", "alternative_wc_ids", "calendar_id", "effective_capacity_hours", "avg_setup_time_minutes", "updated_at"]),
        ("cdm_work_order", ["planned_start", "planned_end", "actual_start", "actual_end", "duration_planned_mins", "duration_actual_mins", "notes", "updated_at"]),
        ("cdm_user", ["updated_at"]),
    ]
    for table, columns in columns_to_drop:
        for col in columns:
            op.drop_column(table, col)

    op.drop_table("cdm_maintenance_window")
    op.drop_table("cdm_resource_calendar")
    op.drop_table("cdm_customer")
