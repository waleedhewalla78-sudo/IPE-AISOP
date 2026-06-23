"""Add alert_incident table with RLS

Revision ID: 019
Revises: 018
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "alert_incident",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("cdm_tenant.id"), nullable=False, index=True),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("pagerduty_incident_key", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alert_incident_tenant_status", "alert_incident", ["tenant_id", "status"])
    op.create_index("ix_alert_incident_tenant_severity", "alert_incident", ["tenant_id", "severity"])
    op.create_index("ix_alert_incident_pagerduty_key", "alert_incident", ["pagerduty_incident_key"])

    op.execute("ALTER TABLE alert_incident ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON alert_incident "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON alert_incident")
    op.drop_index("ix_alert_incident_pagerduty_key", table_name="alert_incident")
    op.drop_index("ix_alert_incident_tenant_severity", table_name="alert_incident")
    op.drop_index("ix_alert_incident_tenant_status", table_name="alert_incident")
    op.drop_table("alert_incident")