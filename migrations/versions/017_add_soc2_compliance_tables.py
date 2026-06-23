"""Add SOC 2 compliance tables

Revision ID: 017
Revises: 016
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "soc2_control",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("control_id", sa.String(20), nullable=False, index=True),
        sa.Column("trust_principle", sa.String(30), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="not_implemented"),
        sa.Column("evidence", JSONB, nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_soc2_control_tenant_principle", "soc2_control", ["tenant_id", "trust_principle"])

    op.create_table(
        "soc2_assessment",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("principle", sa.String(30), nullable=False, index=True),
        sa.Column("score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("assessed_by", sa.String(200), nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_soc2_assessment_tenant_principle", "soc2_assessment", ["tenant_id", "principle"])

    op.execute(
        "ALTER TABLE soc2_control ENABLE ROW LEVEL SECURITY"
    )
    op.execute(
        "CREATE POLICY tenant_isolation ON soc2_control "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )
    op.execute(
        "ALTER TABLE soc2_assessment ENABLE ROW LEVEL SECURITY"
    )
    op.execute(
        "CREATE POLICY tenant_isolation ON soc2_assessment "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON soc2_assessment")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON soc2_control")
    op.drop_index("ix_soc2_assessment_tenant_principle", table_name="soc2_assessment")
    op.drop_index("ix_soc2_control_tenant_principle", table_name="soc2_control")
    op.drop_table("soc2_assessment")
    op.drop_table("soc2_control")