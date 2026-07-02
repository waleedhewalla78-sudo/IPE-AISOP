-- Configure Star Trans tenant for local Odoo (Odoo 19 on host)
-- Run against IPE PostgreSQL (Docker port 5433):
--   Get-Content scripts\configure-odoo-local.sql -Raw | docker exec -i docker-db-1 psql -U ipe -d ipe_test

UPDATE cdm_tenant
SET
  name = 'Star Trans — Electrical Transformer Technology',
  erp_type = 'odoo',
  erp_version = '19.0',
  erp_base_url = 'http://host.docker.internal:8069',
  config = COALESCE(config, '{}'::jsonb) || jsonb_build_object(
    'odoo_url', 'http://host.docker.internal:8069',
    'odoo_db', 'starttrans1',
    'odoo_username', 'admin',
    'odoo_password', 'admin'
  )
WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

-- Verify
SELECT id, name, erp_type, erp_version, erp_base_url,
       config->>'odoo_db' AS odoo_db,
       config->>'odoo_username' AS odoo_user
FROM cdm_tenant
WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
