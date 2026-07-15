"""Phase 3 — Extend supplier reliability scoring (041 already created cdm_supplier_score).

Conflict note: Tech Spec §1.2 lists migration 055 as CREATE cdm_supplier_score, but
migration 041 already created that table for Sprint S10. This revision ALTERs the
existing table to add Phase 3 columns instead of recreating it.

Revision ID: 055
Revises: 054
"""

from alembic import op

revision = "055"
down_revision = "054"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE cdm_supplier_score
        ADD COLUMN IF NOT EXISTS quality_rejection_pct NUMERIC(5, 2),
        ADD COLUMN IF NOT EXISTS concentration_pct NUMERIC(5, 2),
        ADD COLUMN IF NOT EXISTS lead_time_trend VARCHAR(20),
        ADD COLUMN IF NOT EXISTS overall_score NUMERIC(6, 2),
        ADD COLUMN IF NOT EXISTS recommendation TEXT
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_supplier_score_overall
        ON cdm_supplier_score (tenant_id, overall_score)
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_supplier_score_overall")
    op.execute("""
        ALTER TABLE cdm_supplier_score
        DROP COLUMN IF EXISTS quality_rejection_pct,
        DROP COLUMN IF EXISTS concentration_pct,
        DROP COLUMN IF EXISTS lead_time_trend,
        DROP COLUMN IF EXISTS overall_score,
        DROP COLUMN IF EXISTS recommendation
    """)
