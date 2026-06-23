"""Add cdm_location table and inventory position updates

Revision ID: 014
Revises: 013
Create Date: 2026-06-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cdm_location",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("cdm_tenant.id"), nullable=False, index=True),
        sa.Column("erp_source_id", sa.String(128)),
        sa.Column("erp_source_type", sa.String(32)),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("location_type", sa.String(32), nullable=False, server_default="warehouse"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_foreign_key(
        "fk_inventory_position_location",
        "cdm_inventory_position",
        "cdm_location",
        ["location_id"],
        ["id"],
    )

    op.add_column(
        "cdm_inventory_position",
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("cdm_inventory_position", "last_updated")
    op.drop_constraint("fk_inventory_position_location", "cdm_inventory_position")
    op.drop_table("cdm_location")