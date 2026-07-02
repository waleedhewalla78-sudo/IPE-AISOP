"""Release 1: Odoo sync audit tables and MO ERP sync columns.

Revision ID: 036
Revises: 035
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "036"
down_revision = "035"
branch_labels = None
depends_on = None

_SYNC_RUN_STATUS = ("running", "success", "partial", "failed")
_DATA_QUALITY_FLAGS = (
    "MISSING_BOM",
    "MISSING_ROUTING",
    "MISSING_WC",
    "SYNC_CONFLICT",
    "MISSING_PRODUCT",
    "INVALID_QUANTITY",
)


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
        "cdm_sync_run",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id",
            UUID,
            sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.String(32), nullable=False, server_default="odoo"),
        sa.Column("trigger", sa.String(32), nullable=False, server_default="scheduled"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("entity_counts", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error_summary", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in _SYNC_RUN_STATUS)})",
            name="ck_sync_run_status",
        ),
    )
    op.create_index("ix_sync_run_tenant_started", "cdm_sync_run", ["tenant_id", "started_at"])

    op.create_table(
        "cdm_data_quality_flag",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "tenant_id",
            UUID,
            sa.ForeignKey("cdm_tenant.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "mo_id",
            UUID,
            sa.ForeignKey("cdm_manufacturing_order.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("flag_code", sa.String(50), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("details", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            f"flag_code IN ({', '.join(repr(f) for f in _DATA_QUALITY_FLAGS)})",
            name="ck_data_quality_flag_code",
        ),
    )
    op.create_index(
        "ix_data_quality_flag_tenant_mo",
        "cdm_data_quality_flag",
        ["tenant_id", "mo_id"],
    )
    op.create_index(
        "ix_data_quality_flag_active",
        "cdm_data_quality_flag",
        ["tenant_id", "resolved_at"],
        postgresql_where=sa.text("resolved_at IS NULL"),
    )

    op.add_column(
        "cdm_manufacturing_order",
        sa.Column("erp_last_update", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "cdm_manufacturing_order",
        sa.Column("erp_synced_at", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "cdm_manufacturing_order",
        sa.Column("sync_conflict", JSONB),
    )
    op.create_index(
        "ix_mo_tenant_erp_synced",
        "cdm_manufacturing_order",
        ["tenant_id", "erp_synced_at"],
    )

    _rls("cdm_sync_run")
    _rls("cdm_data_quality_flag")


def downgrade():
    op.drop_index("ix_mo_tenant_erp_synced", table_name="cdm_manufacturing_order")
    op.drop_column("cdm_manufacturing_order", "sync_conflict")
    op.drop_column("cdm_manufacturing_order", "erp_synced_at")
    op.drop_column("cdm_manufacturing_order", "erp_last_update")

    op.drop_index("ix_data_quality_flag_active", table_name="cdm_data_quality_flag")
    op.drop_index("ix_data_quality_flag_tenant_mo", table_name="cdm_data_quality_flag")
    op.drop_table("cdm_data_quality_flag")

    op.drop_index("ix_sync_run_tenant_started", table_name="cdm_sync_run")
    op.drop_table("cdm_sync_run")
