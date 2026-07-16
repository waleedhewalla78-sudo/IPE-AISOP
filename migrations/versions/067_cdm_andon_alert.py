"""Phase 7 §5.3 — Andon alerts (durable persistence for the escalation board).

Revision ID: 067
Revises: 066
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "067"
down_revision = "066"
branch_labels = None
depends_on = None


def _rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation ON {table}
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        """
    )


def upgrade():
    op.create_table(
        "cdm_andon_alert",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_ref", sa.String(40), nullable=True),
        sa.Column("color", sa.String(10), nullable=False),  # red/yellow/blue/white
        sa.Column("work_centre", sa.String(40), nullable=True),
        sa.Column("reported_by", sa.String(80), nullable=True),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("impact", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("response_minutes", sa.Integer, nullable=True),
        sa.Column("escalate_after_minutes", sa.Integer, nullable=True),
        sa.Column("resolution", sa.Text, nullable=True),
        sa.Column("triggered_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_andon_alert_tenant", "cdm_andon_alert", ["tenant_id", "status", "triggered_at"]
    )
    _rls("cdm_andon_alert")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_andon_alert")
    op.drop_table("cdm_andon_alert")
