"""Add cdm_model_registry table

Revision ID: 002
Revises: 001
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cdm_model_registry",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("tenant_id", UUID, sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_name", sa.String(64), nullable=False),
        sa.Column("model_version", sa.String(32), nullable=False),
        sa.Column("model_type", sa.String(32), nullable=False),
        sa.Column("metrics", JSONB, nullable=False),
        sa.Column("baseline_metrics", JSONB),
        sa.Column("is_production", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_better_than_baseline", sa.Boolean),
        sa.Column("artifact_path", sa.String(512)),
        sa.Column("training_rows", sa.Integer),
        sa.Column("training_duration_seconds", sa.Numeric(10, 2)),
        sa.Column("trained_by", sa.String(64)),
        sa.Column("promoted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "model_name", "model_version", name="uq_model_registry_version"),
    )
    op.create_index("idx_model_registry_prod", "cdm_model_registry", ["tenant_id", "model_name", "is_production"])


def downgrade():
    op.drop_table("cdm_model_registry")
