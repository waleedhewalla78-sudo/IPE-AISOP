"""Merge parallel migration branches into a single head.

Revision ID: 032
Revises: 014, 025, 031
"""
from alembic import op

revision = "032"
down_revision = ("014", "025", "031")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
