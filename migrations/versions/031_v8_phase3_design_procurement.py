"""v8 Phase 3: engineering materials, design rules, procurement spend/compliance

Revision ID: 031
Revises: 030
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "031"
down_revision = "030"
branch_labels = None
depends_on = None


def _rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation ON {table} "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )


def upgrade():
    op.create_table(
        "cdm_engineering_material",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("grade", sa.String(64)),
        sa.Column("category", sa.String(64), server_default="metal"),
        sa.Column("properties_jsonb", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("cost_per_kg", sa.Numeric(12, 4), server_default="0"),
        sa.Column("sustainability_score", sa.Numeric(5, 2), server_default="50"),
        sa.Column("suppliers_jsonb", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_eng_material_tenant_cat", "cdm_engineering_material", ["tenant_id", "category"])
    _rls("cdm_engineering_material")

    op.create_table(
        "cdm_design_recommendation",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_id", UUID),
        sa.Column("material_id", UUID, sa.ForeignKey("cdm_engineering_material.id")),
        sa.Column("score", sa.Numeric(6, 4), nullable=False),
        sa.Column("rationale", sa.Text),
        sa.Column("alternatives_jsonb", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    _rls("cdm_design_recommendation")

    op.create_table(
        "cdm_design_rule",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("process_type", sa.String(64), nullable=False),
        sa.Column("constraint_type", sa.String(64), nullable=False),
        sa.Column("parameter_key", sa.String(64), nullable=False),
        sa.Column("min_value", sa.Numeric(14, 4)),
        sa.Column("max_value", sa.Numeric(14, 4)),
        sa.Column("unit", sa.String(16)),
    )
    op.create_index("ix_design_rule_process", "cdm_design_rule", ["tenant_id", "process_type"])
    _rls("cdm_design_rule")

    op.create_table(
        "cdm_procurement_spend",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_id", UUID, sa.ForeignKey("cdm_supplier.id")),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(8), server_default="USD"),
        sa.Column("period", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_proc_spend_tenant_period", "cdm_procurement_spend", ["tenant_id", "period"])
    _rls("cdm_procurement_spend")

    op.create_table(
        "cdm_procurement_compliance_check",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("supplier_id", UUID, sa.ForeignKey("cdm_supplier.id"), nullable=False),
        sa.Column("rule_id", sa.String(64), nullable=False),
        sa.Column("result", sa.String(16), nullable=False),
        sa.Column("evidence_jsonb", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_proc_compliance_supplier", "cdm_procurement_compliance_check", ["tenant_id", "supplier_id"])
    _rls("cdm_procurement_compliance_check")

    op.add_column("cdm_supplier", sa.Column("esg_score", sa.Numeric(5, 2), server_default="70"))
    op.add_column("cdm_supplier", sa.Column("risk_tier", sa.String(16), server_default="medium"))
    op.add_column("cdm_supplier", sa.Column("category", sa.String(64)))


def downgrade():
    op.drop_column("cdm_supplier", "category")
    op.drop_column("cdm_supplier", "risk_tier")
    op.drop_column("cdm_supplier", "esg_score")
    op.drop_table("cdm_procurement_compliance_check")
    op.drop_table("cdm_procurement_spend")
    op.drop_table("cdm_design_rule")
    op.drop_table("cdm_design_recommendation")
    op.drop_table("cdm_engineering_material")
