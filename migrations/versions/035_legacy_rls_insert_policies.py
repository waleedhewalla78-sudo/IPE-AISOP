"""Add INSERT WITH CHECK to legacy v7 tenant-scoped RLS policies (ADR-002).

Revision ID: 035
Revises: 034
"""
from alembic import op

revision = "035"
down_revision = "034"
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
        IF EXISTS (
            SELECT 1 FROM pg_policy p
            JOIN pg_class c ON c.oid = p.polrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname = r.tablename
              AND p.polname = 'tenant_isolation'
        ) THEN
            EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I', r.tablename);
            EXECUTE format(
                'CREATE POLICY tenant_isolation ON %I '
                'USING (tenant_id = NULLIF(current_setting(''app.current_tenant_id'', true), '''')::uuid) '
                'WITH CHECK (tenant_id = NULLIF(current_setting(''app.current_tenant_id'', true), '''')::uuid)',
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
        IF EXISTS (
            SELECT 1 FROM pg_policy p
            JOIN pg_class c ON c.oid = p.polrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname = r.tablename
              AND p.polname = 'tenant_isolation'
        ) THEN
            EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I', r.tablename);
            EXECUTE format(
                'CREATE POLICY tenant_isolation ON %I '
                'USING (tenant_id = NULLIF(current_setting(''app.current_tenant_id'', true), '''')::uuid)',
                r.tablename
            );
        END IF;
    END LOOP;
END $$;
"""


def upgrade():
    op.execute(UPGRADE_SQL)


def downgrade():
    op.execute(DOWNGRADE_SQL)
