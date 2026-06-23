"""Enforce audit log immutability with RLS, REVOKE, and trigger

Revision ID: 021
Revises: 020
Create Date: 2026-06-20

P9-006: Append-only cdm_audit_log
- Enables RLS on cdm_audit_log if not already enabled
- Creates RLS policy audit_tenant_isolation
- Creates ipe_audit_writer role with INSERT and SELECT only
- REVOKES UPDATE, DELETE from PUBLIC and all non-superuser roles
- Creates trigger prevent_audit_modification on UPDATE OR DELETE
"""
from alembic import op

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE cdm_audit_log ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY audit_tenant_isolation ON cdm_audit_log "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)"
    )

    op.execute(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ipe_audit_writer') THEN "
        "CREATE ROLE ipe_audit_writer; "
        "END IF; "
        "END $$"
    )
    op.execute("GRANT INSERT, SELECT ON cdm_audit_log TO ipe_audit_writer")
    op.execute("REVOKE UPDATE, DELETE ON cdm_audit_log FROM PUBLIC")

    op.execute(
        "DO $$ DECLARE r RECORD; "
        "BEGIN "
        "FOR r IN SELECT rolname FROM pg_roles "
        "WHERE rolname NOT IN ('postgres', 'ipe_audit_writer') "
        "AND rolname NOT LIKE 'pg_%' LOOP "
        "EXECUTE format('REVOKE UPDATE, DELETE ON cdm_audit_log FROM %I', r.rolname); "
        "END LOOP; "
        "END $$"
    )

    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'cdm_audit_log is append-only: % operations are prohibited', TG_OP;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute(
        "CREATE TRIGGER trg_prevent_audit_modification "
        "BEFORE UPDATE OR DELETE ON cdm_audit_log "
        "FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification()"
    )


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_audit_modification ON cdm_audit_log")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_modification()")
    op.execute("GRANT UPDATE, DELETE ON cdm_audit_log TO PUBLIC")
    op.execute("REVOKE INSERT, SELECT ON cdm_audit_log FROM ipe_audit_writer")
    op.execute("DROP POLICY IF EXISTS audit_tenant_isolation ON cdm_audit_log")
    op.execute("ALTER TABLE cdm_audit_log DISABLE ROW LEVEL SECURITY")