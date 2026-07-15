"""Phase 3 — Exception lifecycle with SLA.

Revision ID: 052
Revises: 051
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "052"
down_revision = "051"
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
        "cdm_exception_sla",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("ack_sla_minutes", sa.Integer, nullable=False),
        sa.Column("resolve_sla_minutes", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "severity", name="uq_exception_sla_tenant_severity"),
    )
    _rls("cdm_exception_sla")

    op.create_table(
        "cdm_agent_exception",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(20), nullable=False),
        sa.Column("exception_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", UUID, nullable=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(30), server_default="open"),
        sa.Column("root_cause_chain_id", UUID, nullable=True),
        sa.Column("resolution_options", JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("selected_option", JSONB, nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", UUID, nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", UUID, nullable=True),
        sa.Column("ack_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolve_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalation_level", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_agent_exception_tenant_status", "cdm_agent_exception", ["tenant_id", "status"])
    op.create_index("ix_agent_exception_severity", "cdm_agent_exception", ["tenant_id", "severity"])
    _rls("cdm_agent_exception")

    # Default SLAs for common severities (applied per tenant at runtime if missing)
    op.execute(
        """
        INSERT INTO cdm_exception_sla (tenant_id, severity, ack_sla_minutes, resolve_sla_minutes)
        SELECT t.id, s.severity, s.ack_m, s.res_m
        FROM cdm_tenant t
        CROSS JOIN (VALUES
            ('critical', 15, 60),
            ('high', 30, 240),
            ('medium', 120, 1440),
            ('low', 480, 4320)
        ) AS s(severity, ack_m, res_m)
        ON CONFLICT DO NOTHING
        """
    )


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_agent_exception")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_exception_sla")
    op.drop_table("cdm_agent_exception")
    op.drop_table("cdm_exception_sla")
