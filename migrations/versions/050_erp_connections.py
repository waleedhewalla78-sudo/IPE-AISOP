"""W1-03: ERP connection management tables with encrypted credentials and audit log.

Revision ID: 050
Revises: 049
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "050"
down_revision = "049"
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
        "cdm_erp_connection",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id",
            UUID,
            sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("erp_type", sa.String(20), nullable=False, server_default="odoo"),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("host_url", sa.String(500), nullable=False),
        sa.Column("database_name", sa.String(100), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password_encrypted", sa.Text, nullable=False),
        sa.Column("api_protocol", sa.String(20), server_default="xmlrpc"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("is_production", sa.Boolean, server_default=sa.text("false")),
        sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_test_result", sa.String(20), nullable=True),
        sa.Column("last_test_message", sa.Text, nullable=True),
        sa.Column("sync_interval_seconds", sa.Integer, server_default="900"),
        sa.Column("sync_enabled", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_by", UUID, nullable=True),
    )
    op.create_index("ix_erp_connection_tenant", "cdm_erp_connection", ["tenant_id"])
    op.create_index(
        "uq_tenant_active_erp",
        "cdm_erp_connection",
        ["tenant_id", "erp_type"],
        unique=True,
        postgresql_where=sa.text("is_active = TRUE"),
    )
    _rls("cdm_erp_connection")

    op.create_table(
        "cdm_erp_connection_log",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID, nullable=False),
        sa.Column(
            "connection_id",
            UUID,
            sa.ForeignKey("cdm_erp_connection.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("result", sa.String(20), nullable=True),
        sa.Column("details", JSONB, nullable=True),
        sa.Column("performed_by", UUID, nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_erp_connection_log_tenant", "cdm_erp_connection_log", ["tenant_id"])
    op.create_index("ix_erp_connection_log_connection", "cdm_erp_connection_log", ["connection_id"])
    op.create_index("ix_erp_connection_log_performed", "cdm_erp_connection_log", ["performed_at"])
    _rls("cdm_erp_connection_log")

    # Migrate encrypted/plaintext Odoo credentials from tenant.config when present
    op.execute(
        """
        INSERT INTO cdm_erp_connection (
            tenant_id, erp_type, display_name, host_url, database_name,
            username, password_encrypted, api_protocol, is_active, is_production,
            sync_interval_seconds, sync_enabled
        )
        SELECT
            t.id,
            'odoo',
            COALESCE(t.config->>'odoo_instance_name', 'Migrated Odoo'),
            COALESCE(t.erp_base_url, t.config->>'odoo_url'),
            t.config->>'odoo_db',
            t.config->>'odoo_username',
            COALESCE(t.config->>'odoo_password_enc', t.config->>'odoo_password', ''),
            'xmlrpc',
            COALESCE((t.config->>'odoo_enabled')::boolean, true),
            false,
            COALESCE((t.config->>'odoo_sync_interval_minutes')::integer, 900),
            true
        FROM cdm_tenant t
        WHERE COALESCE(t.erp_base_url, t.config->>'odoo_url') IS NOT NULL
          AND t.config->>'odoo_db' IS NOT NULL
          AND t.config->>'odoo_username' IS NOT NULL
          AND (
              COALESCE(t.config->>'odoo_password_enc', '') <> ''
              OR COALESCE(t.config->>'odoo_password', '') <> ''
          )
          AND NOT EXISTS (
              SELECT 1 FROM cdm_erp_connection c
              WHERE c.tenant_id = t.id AND c.erp_type = 'odoo' AND c.is_active = true
          )
        """
    )


def downgrade():
    op.drop_index("ix_erp_connection_log_performed", table_name="cdm_erp_connection_log")
    op.drop_index("ix_erp_connection_log_connection", table_name="cdm_erp_connection_log")
    op.drop_index("ix_erp_connection_log_tenant", table_name="cdm_erp_connection_log")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_erp_connection_log")
    op.drop_table("cdm_erp_connection_log")
    op.drop_index("uq_tenant_active_erp", table_name="cdm_erp_connection")
    op.drop_index("ix_erp_connection_tenant", table_name="cdm_erp_connection")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_erp_connection")
    op.drop_table("cdm_erp_connection")
