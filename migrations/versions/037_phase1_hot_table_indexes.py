"""Phase 1 composite indexes for frequently queried CDM tables."""

from alembic import op

revision = "037"
down_revision = "036"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_bom_tenant_product_active",
        "cdm_bill_of_material",
        ["tenant_id", "product_id"],
        postgresql_where="is_active = true",
    )
    op.create_index(
        "ix_product_tenant_source_type",
        "cdm_product",
        ["tenant_id", "source_type"],
    )
    op.create_index(
        "ix_inventory_tenant_product",
        "cdm_inventory_position",
        ["tenant_id", "product_id"],
    )
    op.create_index(
        "ix_mo_tenant_bom_status",
        "cdm_manufacturing_order",
        ["tenant_id", "bom_id", "status"],
    )
    op.create_index(
        "ix_audit_tenant_timestamp",
        "cdm_audit_log",
        ["tenant_id", "timestamp"],
    )


def downgrade():
    op.drop_index("ix_audit_tenant_timestamp", table_name="cdm_audit_log")
    op.drop_index("ix_mo_tenant_bom_status", table_name="cdm_manufacturing_order")
    op.drop_index("ix_inventory_tenant_product", table_name="cdm_inventory_position")
    op.drop_index("ix_product_tenant_source_type", table_name="cdm_product")
    op.drop_index("ix_bom_tenant_product_active", table_name="cdm_bill_of_material")
