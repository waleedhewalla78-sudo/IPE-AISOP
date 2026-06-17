"""Initial CDM schema

Revision ID: 001
Revises: None
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create Roles
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ipe_app') THEN
                CREATE ROLE ipe_app LOGIN PASSWORD 'ipe_app_pass';
            END IF;
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ipe_audit_writer') THEN
                CREATE ROLE ipe_audit_writer LOGIN PASSWORD 'ipe_audit_writer_pass' BYPASSRLS;
            END IF;
        END $$;
    """)

    # Dynamic database grants (works in both ipe_dev and ipe_test)
    op.execute("""
        DO $$
        BEGIN
            EXECUTE format('GRANT CONNECT ON DATABASE %I TO ipe_app', current_database());
            EXECUTE format('GRANT CONNECT ON DATABASE %I TO ipe_audit_writer', current_database());
        END $$;
    """)
    op.execute("GRANT USAGE ON SCHEMA public TO ipe_app")
    op.execute("GRANT USAGE ON SCHEMA public TO ipe_audit_writer")

    # 2. Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # 3. Tables (19 total)

    # (1)
    op.create_table(
        "cdm_tenant",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("tier", sa.String(16), nullable=False, server_default="starter"),
        sa.Column("erp_type", sa.String(16), nullable=False),
        sa.Column("autonomy_mode", sa.String(16), nullable=False, server_default="shadow"),
        sa.Column("config", JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # (2)
    op.create_table(
        "cdm_user",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("email", sa.String(256), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="planner"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "email"),
    )

    # (3)
    op.create_table(
        "cdm_product",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("erp_source_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("source_type", sa.String(16), nullable=False),
        sa.Column("lead_time_days", sa.Numeric(6, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "erp_source_id"),
    )

    # (4)
    op.create_table(
        "cdm_bill_of_material",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("product_id", UUID, sa.ForeignKey("cdm_product.id"), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # (5)
    op.create_table(
        "cdm_bom_line",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("bom_id", UUID, sa.ForeignKey("cdm_bill_of_material.id"), nullable=False),
        sa.Column("component_id", UUID, sa.ForeignKey("cdm_product.id"), nullable=False),
        sa.Column("quantity_per", sa.Numeric(14, 6), nullable=False),
        sa.Column("is_critical", sa.Boolean, server_default=sa.text("false")),
    )

    # (6)
    op.create_table(
        "cdm_work_center",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("erp_source_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("capacity_hours_per_day", sa.Numeric(6, 2), nullable=False),
        sa.Column("status", sa.String(16), server_default="operational"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "erp_source_id"),
    )

    # (7)
    op.create_table(
        "cdm_routing_operation",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("bom_id", UUID, sa.ForeignKey("cdm_bill_of_material.id"), nullable=False),
        sa.Column("sequence", sa.SmallInteger, nullable=False),
        sa.Column("work_center_id", UUID, sa.ForeignKey("cdm_work_center.id"), nullable=False),
        sa.Column("duration_planned_mins", sa.Numeric(10, 2), nullable=False),
    )

    # (8)
    op.create_table(
        "cdm_supplier",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("erp_source_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("reliability_score", sa.Numeric(5, 4)),
        sa.Column("delay_distribution_type", sa.String(16), server_default="normal"),
        sa.Column("delay_distribution_params", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "erp_source_id"),
    )

    # (9)
    op.create_table(
        "cdm_supply_order",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("erp_source_id", sa.String(128), nullable=False),
        sa.Column("product_id", UUID, sa.ForeignKey("cdm_product.id"), nullable=False),
        sa.Column("supplier_id", UUID, sa.ForeignKey("cdm_supplier.id")),
        sa.Column("quantity_ordered", sa.Numeric(14, 4), nullable=False),
        sa.Column("expected_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_date", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(24), nullable=False, server_default="confirmed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "erp_source_id"),
    )

    # (10)
    op.create_table(
        "cdm_operator",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("erp_source_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("skill_tags", JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "erp_source_id"),
    )

    # (11) — includes optimistic lock fields + updated_at
    op.create_table(
        "cdm_manufacturing_order",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("erp_mo_id", sa.String(128)),
        sa.Column("product_id", UUID, sa.ForeignKey("cdm_product.id"), nullable=False),
        sa.Column("bom_id", UUID, sa.ForeignKey("cdm_bill_of_material.id"), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("planned_start", sa.DateTime(timezone=True)),
        sa.Column("planned_end", sa.DateTime(timezone=True)),
        sa.Column("feasibility_score", sa.Numeric(5, 2)),
        sa.Column("material_score", sa.Numeric(5, 2)),
        sa.Column("capacity_score", sa.Numeric(5, 2)),
        sa.Column("labor_score", sa.Numeric(5, 2)),
        sa.Column("primary_constraint", sa.String(24)),
        sa.Column("status", sa.String(24), nullable=False, server_default="draft"),
        sa.Column("autonomy_action", sa.String(24)),
        sa.Column("version", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("locked_by", UUID, sa.ForeignKey("cdm_user.id")),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # (12)
    op.create_table(
        "cdm_demand_line",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("erp_source_id", sa.String(128), nullable=False),
        sa.Column("product_id", UUID, sa.ForeignKey("cdm_product.id"), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("required_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("demand_type", sa.String(16), nullable=False),
        sa.Column("priority_score", sa.Numeric(8, 4)),
        sa.Column("status", sa.String(24), nullable=False, server_default="new"),
        sa.Column("mo_id", UUID, sa.ForeignKey("cdm_manufacturing_order.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "erp_source_id"),
    )

    # (13)
    op.create_table(
        "cdm_work_order",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("mo_id", UUID, sa.ForeignKey("cdm_manufacturing_order.id"), nullable=False),
        sa.Column("routing_op_id", UUID, sa.ForeignKey("cdm_routing_operation.id"), nullable=False),
        sa.Column("work_center_id", UUID, sa.ForeignKey("cdm_work_center.id"), nullable=False),
        sa.Column("operator_id", UUID, sa.ForeignKey("cdm_operator.id")),
        sa.Column("sequence", sa.SmallInteger, nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # (14)
    op.create_table(
        "cdm_inventory_position",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("product_id", UUID, sa.ForeignKey("cdm_product.id"), nullable=False),
        sa.Column("qty_on_hand", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("qty_reserved", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # (15)
    op.create_table(
        "cdm_delay_event",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("mo_id", UUID, sa.ForeignKey("cdm_manufacturing_order.id"), nullable=False),
        sa.Column("cause_category", sa.String(32), nullable=False),
        sa.Column("cause_detail", sa.Text),
        sa.Column("delay_minutes", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # (16)
    op.create_table(
        "cdm_resolution_scenario",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("mo_id", UUID, sa.ForeignKey("cdm_manufacturing_order.id"), nullable=False),
        sa.Column("strategy", sa.String(32), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("business_score", sa.Numeric(8, 4)),
        sa.Column("status", sa.String(16), server_default="proposed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # (17) — MDR score history persistence
    op.create_table(
        "cdm_mdr_score",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("bom_completeness_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("lead_time_accuracy_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("passed", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # (18) — ERP push retry queue with backoff
    op.create_table(
        "cdm_export_queue",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("retry_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("next_retry_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # (19) — append-only, protected by RLS with a bypass role
    op.create_table(
        "cdm_audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("actor_type", sa.String(16), nullable=False),
        sa.Column("actor_id", sa.String(128), nullable=False),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", UUID, nullable=False),
        sa.Column("before_state", JSONB),
        sa.Column("after_state", JSONB),
    )

    # 4. Triggers for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_mo_updated_at BEFORE UPDATE ON cdm_manufacturing_order
        FOR EACH ROW EXECUTE FUNCTION update_updated_at()
    """)
    op.execute("""
        CREATE TRIGGER trg_demand_updated_at BEFORE UPDATE ON cdm_demand_line
        FOR EACH ROW EXECUTE FUNCTION update_updated_at()
    """)
    op.execute("""
        CREATE TRIGGER trg_supply_updated_at BEFORE UPDATE ON cdm_supply_order
        FOR EACH ROW EXECUTE FUNCTION update_updated_at()
    """)

    # 5. Row-Level Security (RLS) Application — only on tables with a tenant_id column
    op.execute("""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'cdm_%' LOOP
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = r.tablename AND column_name = 'tenant_id'
                ) THEN
                    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', r.tablename);
                    EXECUTE format(
                        'CREATE POLICY tenant_isolation ON %I USING (tenant_id = NULLIF(current_setting(''app.current_tenant_id'', true), '''')::uuid)',
                        r.tablename
                    );
                END IF;
            END LOOP;
        END $$;
    """)

    # 6. Grants and Revokes
    op.execute("""
        DO $$
        DECLARE
            r RECORD;
        BEGIN
            FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'cdm_%' LOOP
                EXECUTE format('GRANT SELECT, INSERT, UPDATE ON %I TO ipe_app', r.tablename);
            END LOOP;
        END $$;
    """)

    # Audit log specific permissions (append-only for ipe_app, full access for bypass writer)
    op.execute("REVOKE UPDATE, DELETE ON cdm_audit_log FROM ipe_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON cdm_audit_log TO ipe_audit_writer")
    op.execute("GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO ipe_app")
    op.execute("GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO ipe_audit_writer")


def downgrade():
    tables = [
        "cdm_audit_log", "cdm_export_queue", "cdm_mdr_score",
        "cdm_resolution_scenario", "cdm_delay_event",
        "cdm_inventory_position", "cdm_work_order", "cdm_demand_line",
        "cdm_manufacturing_order", "cdm_supply_order",
        "cdm_routing_operation", "cdm_operator", "cdm_work_center",
        "cdm_bom_line", "cdm_bill_of_material", "cdm_supplier",
        "cdm_product", "cdm_user", "cdm_tenant",
    ]
    for table in tables:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at()")
    op.execute("DROP ROLE IF EXISTS ipe_audit_writer")
    op.execute("DROP ROLE IF EXISTS ipe_app")
