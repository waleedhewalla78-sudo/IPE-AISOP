"""Migration 044 — ABC/XYZ product segmentation tables."""

from alembic import op

revision = "044"
down_revision = "042"
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
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_product_segment (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            product_id UUID NOT NULL REFERENCES cdm_product(id) ON DELETE CASCADE,
            segmentation_date DATE NOT NULL,
            abc_class VARCHAR(1) NOT NULL CHECK (abc_class IN ('A','B','C')),
            revenue_total NUMERIC(18,2),
            revenue_share_pct NUMERIC(8,4),
            cumulative_revenue_pct NUMERIC(8,4),
            xyz_class VARCHAR(1) NOT NULL CHECK (xyz_class IN ('X','Y','Z')),
            demand_cv NUMERIC(8,4),
            demand_mean NUMERIC(18,4),
            demand_stddev NUMERIC(18,4),
            combined_segment VARCHAR(2) NOT NULL,
            target_service_level_pct NUMERIC(5,2),
            forecast_model_recommendation VARCHAR(50),
            review_frequency VARCHAR(20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_pseg_tenant_product
        ON cdm_product_segment (tenant_id, product_id, segmentation_date)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pseg_segment
        ON cdm_product_segment (tenant_id, combined_segment)
        """
    )
    _rls("cdm_product_segment")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_segmentation_config (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE CASCADE,
            abc_a_threshold_pct NUMERIC(5,2) NOT NULL DEFAULT 80.0,
            abc_b_threshold_pct NUMERIC(5,2) NOT NULL DEFAULT 95.0,
            xyz_x_threshold NUMERIC(5,2) NOT NULL DEFAULT 0.5,
            xyz_y_threshold NUMERIC(5,2) NOT NULL DEFAULT 1.0,
            service_level_ax NUMERIC(5,2) NOT NULL DEFAULT 99.0,
            service_level_ay NUMERIC(5,2) NOT NULL DEFAULT 97.0,
            service_level_az NUMERIC(5,2) NOT NULL DEFAULT 95.0,
            service_level_bx NUMERIC(5,2) NOT NULL DEFAULT 97.0,
            service_level_by NUMERIC(5,2) NOT NULL DEFAULT 95.0,
            service_level_bz NUMERIC(5,2) NOT NULL DEFAULT 90.0,
            service_level_cx NUMERIC(5,2) NOT NULL DEFAULT 95.0,
            service_level_cy NUMERIC(5,2) NOT NULL DEFAULT 90.0,
            service_level_cz NUMERIC(5,2) NOT NULL DEFAULT 85.0,
            history_months INTEGER NOT NULL DEFAULT 12,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_segmentation_config_tenant UNIQUE (tenant_id)
        )
        """
    )
    _rls("cdm_segmentation_config")


def downgrade():
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_segmentation_config")
    op.execute("DROP TABLE IF EXISTS cdm_segmentation_config")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_product_segment")
    op.execute("DROP TABLE IF EXISTS cdm_product_segment")
