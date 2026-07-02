"""Add user auth columns to cdm_user

Revision ID: 013
Revises: 012
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns("cdm_user")] if insp.has_table("cdm_user") else []
    if "password_hash" not in cols:
        op.add_column("cdm_user", sa.Column("password_hash", sa.String(256), nullable=True, server_default=sa.text("NULL")))
    if "full_name" not in cols:
        op.add_column("cdm_user", sa.Column("full_name", sa.String(256), nullable=True, server_default=sa.text("NULL")))
    if "is_active" not in cols:
        op.add_column("cdm_user", sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")))


def downgrade():
    op.drop_column("cdm_user", "is_active")
    op.drop_column("cdm_user", "full_name")
    op.drop_column("cdm_user", "password_hash")