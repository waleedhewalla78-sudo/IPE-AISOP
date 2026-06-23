"""Add work order version for optimistic locking on schedule approve

Revision ID: 023
Revises: 022
Create Date: 2026-06-22
"""
from alembic import op
import sqlalchemy as sa

revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "cdm_work_order",
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )


def downgrade():
    op.drop_column("cdm_work_order", "version")
