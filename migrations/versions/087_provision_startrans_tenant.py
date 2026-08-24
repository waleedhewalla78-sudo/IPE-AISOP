"""Provision Star Trans tenant onboarding registry (BATCH2-1).

Revision ID: 087
Revises: 086

Does NOT create a second operational tenant on lab. The Star Trans seed
tenant a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11 already holds 28 MOs.
This migration:

1. Creates cdm_tenant_onboarding (slug → tenant_id, FORCE RLS)
2. Stores deterministic uuid5(NAMESPACE_URL, ipe://tenant/star-trans)
   as canonical_uuid for future Hetzner production
3. Records HMAC secret *reference* only (no production secret in git/DB dump)
4. Records storage namespace path
5. Flags Copilot audit + DQ overnight as enabled in registry
6. Idempotent upsert by slug
7. down() drops registry tables and placeholder admin; never deletes the
   seeded cdm_tenant row
"""

from alembic import op

revision = "087"
down_revision = "086"
branch_labels = None
depends_on = None

LAB_TENANT = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
# uuid.uuid5(uuid.NAMESPACE_URL, "ipe://tenant/star-trans")
CANONICAL_UUID = "6a7281ee-62cb-5a72-8162-d3c573e54877"
HMAC_REF = "hetzner-secrets://ipe/tenants/star-trans/copilot-hmac"
STORAGE_NS = "s3://ipe-tenant-star-trans"


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_tenant_onboarding (
          slug TEXT PRIMARY KEY,
          tenant_id UUID NOT NULL REFERENCES cdm_tenant(id) ON DELETE RESTRICT,
          canonical_uuid UUID NOT NULL,
          display_name TEXT NOT NULL,
          license_tier TEXT NOT NULL,
          support_tier TEXT NOT NULL,
          is_reference_customer BOOLEAN NOT NULL DEFAULT TRUE,
          hmac_secret_ref TEXT NOT NULL,
          storage_namespace TEXT NOT NULL,
          copilot_audit_enabled BOOLEAN NOT NULL DEFAULT TRUE,
          dq_dashboard_enabled BOOLEAN NOT NULL DEFAULT TRUE,
          dq_overnight_enabled BOOLEAN NOT NULL DEFAULT TRUE,
          config JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_cdm_tenant_onboarding_tenant "
        "ON cdm_tenant_onboarding (tenant_id)"
    )
    op.execute("ALTER TABLE cdm_tenant_onboarding ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE cdm_tenant_onboarding FORCE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_tenant_onboarding")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON cdm_tenant_onboarding
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cdm_tenant_hmac_ref (
          tenant_id UUID PRIMARY KEY REFERENCES cdm_tenant(id) ON DELETE CASCADE,
          secret_ref TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("ALTER TABLE cdm_tenant_hmac_ref ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE cdm_tenant_hmac_ref FORCE ROW LEVEL SECURITY")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON cdm_tenant_hmac_ref")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON cdm_tenant_hmac_ref
        USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
        """
    )

    # Bind slug to existing lab Star Trans tenant (do not INSERT a second cdm_tenant).
    op.execute(
        f"""
        INSERT INTO cdm_tenant_onboarding (
          slug, tenant_id, canonical_uuid, display_name, license_tier, support_tier,
          is_reference_customer, hmac_secret_ref, storage_namespace,
          copilot_audit_enabled, dq_dashboard_enabled, dq_overnight_enabled, config
        )
        SELECT
          'star-trans',
          t.id,
          '{CANONICAL_UUID}'::uuid,
          'Star Trans',
          'enterprise',
          'phase1_business_hours',
          TRUE,
          '{HMAC_REF}',
          '{STORAGE_NS}',
          TRUE, TRUE, TRUE,
          jsonb_build_object(
            'slug', 'star-trans',
            'timezone', 'Africa/Cairo',
            'locale_primary', 'en-EG',
            'locale_fallback', 'ar-EG',
            'currency', 'EGP',
            'currency_reference', 'USD',
            'hosting', 'diligent-hetzner',
            'data_residency', 'hetzner-eu-east',
            'tier_badge', 'reference_customer',
            'contract_start', NULL,
            'contract_end', NULL,
            'environment', 'lab'
          )
        FROM cdm_tenant t
        WHERE t.id = '{LAB_TENANT}'::uuid
        ON CONFLICT (slug) DO UPDATE SET
          tenant_id = EXCLUDED.tenant_id,
          canonical_uuid = EXCLUDED.canonical_uuid,
          display_name = EXCLUDED.display_name,
          license_tier = EXCLUDED.license_tier,
          support_tier = EXCLUDED.support_tier,
          hmac_secret_ref = EXCLUDED.hmac_secret_ref,
          storage_namespace = EXCLUDED.storage_namespace,
          copilot_audit_enabled = EXCLUDED.copilot_audit_enabled,
          dq_dashboard_enabled = EXCLUDED.dq_dashboard_enabled,
          dq_overnight_enabled = EXCLUDED.dq_overnight_enabled,
          updated_at = now()
        """
    )

    op.execute(
        f"""
        INSERT INTO cdm_tenant_hmac_ref (tenant_id, secret_ref)
        VALUES ('{LAB_TENANT}'::uuid, '{HMAC_REF}')
        ON CONFLICT (tenant_id) DO UPDATE SET secret_ref = EXCLUDED.secret_ref
        """
    )

    op.execute(
        f"""
        UPDATE cdm_tenant
        SET
          config = COALESCE(config, '{{}}'::jsonb) || jsonb_build_object(
            'onboarding_slug', 'star-trans',
            'canonical_uuid', '{CANONICAL_UUID}',
            'reference_customer', true,
            'copilot_audit_enabled', true,
            'dq_dashboard_enabled', true,
            'dq_overnight_enabled', true,
            'storage_namespace', '{STORAGE_NS}',
            'hmac_secret_ref', '{HMAC_REF}',
            'timezone', 'Africa/Cairo'
          ),
          updated_at = now()
        WHERE id = '{LAB_TENANT}'::uuid
        """
    )

    # Placeholder admin — no usable password (BATCH2-4 provisions real users).
    op.execute(
        f"""
        INSERT INTO cdm_user (tenant_id, email, role, full_name, is_active, password_hash)
        VALUES (
          '{LAB_TENANT}'::uuid,
          'admin@startrans.eg',
          'admin',
          'Star Trans Lab Admin (placeholder)',
          FALSE,
          NULL
        )
        ON CONFLICT (tenant_id, email) DO NOTHING
        """
    )


def downgrade():
    op.execute(
        f"""
        DELETE FROM cdm_user
        WHERE tenant_id = '{LAB_TENANT}'::uuid
          AND email = 'admin@startrans.eg'
          AND password_hash IS NULL
        """
    )
    op.execute(
        f"""
        UPDATE cdm_tenant
        SET config = config
          - 'onboarding_slug' - 'canonical_uuid' - 'reference_customer'
          - 'copilot_audit_enabled' - 'dq_dashboard_enabled' - 'dq_overnight_enabled'
          - 'storage_namespace' - 'hmac_secret_ref' - 'timezone'
        WHERE id = '{LAB_TENANT}'::uuid
        """
    )
    op.execute("DROP TABLE IF EXISTS cdm_tenant_hmac_ref CASCADE")
    op.execute("DROP TABLE IF EXISTS cdm_tenant_onboarding CASCADE")
