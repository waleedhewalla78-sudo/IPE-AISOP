"""Add tenant_id and RLS to cdm_maintenance_window

Revision ID: 020
Revises: 019
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "cdm_maintenance_window",
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("cdm_tenant.id"),
            nullable=False,
        ),
    )
    op.create_index("ix_maintenance_window_tenant_id", "cdm_maintenance_window", ["tenant_id"])

    op.execute("ALTER TABLE cdm_maintenance_window ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON cdm_maintenance_window "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_maintenance_window")
    op.execute("ALTER TABLE cdm_maintenance_window DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_maintenance_window_tenant_id", table_name="cdm_maintenance_window")
    op.drop_column("cdm_maintenance_window", "tenant_id")