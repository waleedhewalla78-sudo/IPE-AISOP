"""Add missing RLS policies for tables with tenant_id

Revision ID: 015
Revises: 012
Create Date: 2026-06-20

Enables Row-Level Security and creates the standard tenant_isolation
policy on every public.cdm_* table that has a tenant_id column but
does not yet have RLS enabled.

This is idempotent — re-running on an already-secured schema is safe.
"""

from alembic import op

revision = "015"
down_revision = "012"
branch_labels = None
depends_on = None


UPGRADE_SQL = """
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT tablename
        FROM pg_tables t
        WHERE t.schemaname = 'public'
          AND EXISTS (
              SELECT 1 FROM information_schema.columns c
              WHERE c.table_schema = 'public'
                AND c.table_name = t.tablename
                AND c.column_name = 'tenant_id'
          )
    LOOP
        -- Enable RLS (idempotent)
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', r.tablename);

        -- Create tenant_isolation policy if it does not exist
        IF NOT EXISTS (
            SELECT 1 FROM pg_policy p
            JOIN pg_class c ON c.oid = p.polrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname = r.tablename
              AND p.polname = 'tenant_isolation'
        ) THEN
            EXECUTE format(
                'CREATE POLICY tenant_isolation ON %I USING (tenant_id = NULLIF(current_setting(''app.current_tenant_id'', true), '''')::uuid)',
                r.tablename
            );
        END IF;
    END LOOP;
END $$;
"""


DOWNGRADE_SQL = """
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT tablename
        FROM pg_tables t
        WHERE t.schemaname = 'public'
          AND EXISTS (
              SELECT 1 FROM information_schema.columns c
              WHERE c.table_schema = 'public'
                AND c.table_name = t.tablename
                AND c.column_name = 'tenant_id'
          )
    LOOP
        -- Drop tenant_isolation policy if it exists
        IF EXISTS (
            SELECT 1 FROM pg_policy p
            JOIN pg_class c ON c.oid = p.polrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname = r.tablename
              AND p.polname = 'tenant_isolation'
        ) THEN
            EXECUTE format('DROP POLICY tenant_isolation ON %I', r.tablename);
        END IF;

        -- Disable RLS (idempotent)
        EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY', r.tablename);
    END LOOP;
END $$;
"""


def upgrade():
    op.execute(UPGRADE_SQL)


def downgrade():
    op.execute(DOWNGRADE_SQL)