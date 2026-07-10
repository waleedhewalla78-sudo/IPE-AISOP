"""W1-03: Odoo config versioning table with RLS.

Revision ID: 043
Revises: 038
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "043"
down_revision = "038"
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
        "cdm_odoo_config_version",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id",
            UUID,
            sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_key", sa.String(64), nullable=False, server_default="primary"),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("name", sa.String(128), nullable=False, server_default=""),
        sa.Column("odoo_url", sa.String(512), nullable=False),
        sa.Column("odoo_db", sa.String(128), nullable=False),
        sa.Column("odoo_username", sa.String(256), nullable=False),
        sa.Column("odoo_password_enc", sa.Text),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("sync_interval_minutes", sa.Integer, nullable=False, server_default="900"),
        sa.Column("field_mappings", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("config_meta", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("change_summary", sa.Text),
        sa.Column("created_by", UUID),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "entity_key", "version", name="uq_odoo_config_tenant_entity_version"),
    )
    op.create_index(
        "ix_odoo_config_tenant_entity_current",
        "cdm_odoo_config_version",
        ["tenant_id", "entity_key"],
        unique=True,
        postgresql_where=sa.text("is_current = true"),
    )
    op.create_index(
        "ix_odoo_config_tenant_created",
        "cdm_odoo_config_version",
        ["tenant_id", "created_at"],
    )
    _rls("cdm_odoo_config_version")


def downgrade():
    op.drop_index("ix_odoo_config_tenant_created", table_name="cdm_odoo_config_version")
    op.drop_index("ix_odoo_config_tenant_entity_current", table_name="cdm_odoo_config_version")
    op.drop_table("cdm_odoo_config_version")
