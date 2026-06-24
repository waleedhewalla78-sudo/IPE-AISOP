"""Add cdm_machine_health_telemetry for V6-R4 predictive maintenance

Revision ID: 026
Revises: 024
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "026"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cdm_machine_health_telemetry",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("cdm_tenant.id"), nullable=False),
        sa.Column("machine_id", sa.Text(), nullable=False),
        sa.Column("work_center_id", UUID(as_uuid=True), sa.ForeignKey("cdm_work_center.id"), nullable=True),
        sa.Column("rul_hours", sa.Numeric(10, 2), nullable=False),
        sa.Column("vibration_rms", sa.Numeric(10, 4), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_machine_health_telemetry_tenant_machine",
        "cdm_machine_health_telemetry",
        ["tenant_id", "machine_id"],
    )

    op.execute("ALTER TABLE cdm_machine_health_telemetry ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON cdm_machine_health_telemetry "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_machine_health_telemetry")
    op.execute("ALTER TABLE cdm_machine_health_telemetry DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_machine_health_telemetry_tenant_machine", table_name="cdm_machine_health_telemetry")
    op.drop_table("cdm_machine_health_telemetry")
