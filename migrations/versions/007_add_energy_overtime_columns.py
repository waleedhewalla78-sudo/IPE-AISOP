"""Add energy_kwh_per_hour to work_center and overtime_multiplier to shift

Revision ID: 007
Revises: 006
Create Date: 2026-06-18
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "cdm_work_center",
        sa.Column("energy_kwh_per_hour", sa.Numeric(8, 2), nullable=True),
    )
    op.add_column(
        "cdm_shift",
        sa.Column("overtime_multiplier", sa.Numeric(4, 2), nullable=True),
    )


def downgrade():
    op.drop_column("cdm_shift", "overtime_multiplier")
    op.drop_column("cdm_work_center", "energy_kwh_per_hour")
