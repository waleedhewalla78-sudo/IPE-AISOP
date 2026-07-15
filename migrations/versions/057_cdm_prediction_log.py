"""Phase 3 — Predictive risk score snapshots.

Revision ID: 057
Revises: 056
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "057"
down_revision = "056"
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
        "cdm_prediction_log",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mo_id", UUID, nullable=False),
        sa.Column("prediction_date", sa.Date, nullable=False),
        sa.Column("horizon_days", sa.Integer, nullable=False),
        sa.Column("target_date", sa.Date, nullable=False),
        sa.Column("predicted_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("predicted_color", sa.String(10), nullable=True),
        sa.Column("primary_risk_gate", sa.String(20), nullable=True),
        sa.Column("risk_explanation", sa.Text, nullable=True),
        sa.Column("actual_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("prediction_accuracy", sa.Numeric(6, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_prediction_log_tenant_mo_date",
        "cdm_prediction_log",
        ["tenant_id", "mo_id", "prediction_date"],
    )
    _rls("cdm_prediction_log")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_prediction_log")
    op.drop_table("cdm_prediction_log")
