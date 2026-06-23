"""Add GDPR DSAR and consent tables

Revision ID: 018
Revises: 017
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gdpr_dsar_request",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("cdm_tenant.id"), nullable=False, index=True),
        sa.Column("subject_email", sa.String(320), nullable=False, index=True),
        sa.Column("request_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="received"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("denial_reason", sa.Text, nullable=True),
        sa.Column("artifacts", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_gdpr_dsar_tenant_status", "gdpr_dsar_request", ["tenant_id", "status"])
    op.create_index("ix_gdpr_dsar_tenant_type", "gdpr_dsar_request", ["tenant_id", "request_type"])

    op.create_table(
        "gdpr_consent",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("cdm_tenant.id"), nullable=False, index=True),
        sa.Column("subject_email", sa.String(320), nullable=False, index=True),
        sa.Column("consent_type", sa.String(100), nullable=False),
        sa.Column("granted", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_gdpr_consent_tenant_type", "gdpr_consent", ["tenant_id", "consent_type"])
    op.create_index("ix_gdpr_consent_subject_type", "gdpr_consent", ["subject_email", "consent_type"])

    op.execute("ALTER TABLE gdpr_dsar_request ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON gdpr_dsar_request "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )
    op.execute("ALTER TABLE gdpr_consent ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON gdpr_consent "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON gdpr_consent")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON gdpr_dsar_request")
    op.drop_index("ix_gdpr_consent_subject_type", table_name="gdpr_consent")
    op.drop_index("ix_gdpr_consent_tenant_type", table_name="gdpr_consent")
    op.drop_index("ix_gdpr_dsar_tenant_type", table_name="gdpr_dsar_request")
    op.drop_index("ix_gdpr_dsar_tenant_status", table_name="gdpr_dsar_request")
    op.drop_table("gdpr_consent")
    op.drop_table("gdpr_dsar_request")