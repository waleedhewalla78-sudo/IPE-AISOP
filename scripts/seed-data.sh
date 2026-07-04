#!/usr/bin/env bash
set -euo pipefail

echo "=== Loading seed data ==="

PG_DSN="${IPE_DATABASE_URL_SYNC:-postgresql://ipe:ipe_test_pass@localhost:5433/ipe_test}"

psql "$PG_DSN" <<'SQL'
-- Seed tenant
INSERT INTO cdm_tenant (id, name, tier, erp_type, autonomy_mode)
VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Demo Manufacturing Inc', 'professional', 'odoo', 'shadow')
ON CONFLICT (id) DO NOTHING;

-- Seed users (password: demo or admin in development)
INSERT INTO cdm_user (id, tenant_id, email, password_hash, full_name, role, is_active, created_at)
VALUES
  ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'admin@demo.com', '$2b$12$LJ3m4ys3Lk_xsHX7x7x7xO', 'Alice Admin', 'admin', true, NOW()),
  ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c02', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'planner@demo.com', '$2b$12$LJ3m4ys3Lk_xsHX7x7x7xO', 'Bob Planner', 'planner', true, NOW()),
  ('c0eebc99-9c0b-4ef8-bb6d-6bb9bd380c03', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Ahmed@nour', crypt('admin', gen_salt('bf')), 'Ahmed Nour', 'admin', true, NOW())
ON CONFLICT (tenant_id, email) DO UPDATE SET
  password_hash = EXCLUDED.password_hash,
  full_name = EXCLUDED.full_name,
  role = EXCLUDED.role,
  is_active = EXCLUDED.is_active;

-- Seed products
INSERT INTO cdm_product (tenant_id, erp_source_id, erp_source_type, name, internal_ref, source_type, uom, standard_cost, lead_time_days, safety_stock)
VALUES
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'PROD001', 'odoo', 'Widget A', 'WGT-A-100', 'manufactured', 'unit', 15.50, 3, 100),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'PROD002', 'odoo', 'Gadget B', 'GDT-B-200', 'manufactured', 'unit', 42.00, 5, 50),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'PROD003', 'odoo', 'Component C', 'CMP-C-300', 'purchased', 'unit', 3.25, 10, 500),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'PROD004', 'odoo', 'Assembly D', 'ASM-D-400', 'manufactured', 'unit', 89.99, 7, 25),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'PROD005', 'odoo', 'Raw Material E', 'RAW-E-500', 'purchased', 'kg', 1.10, 20, 1000)
ON CONFLICT (tenant_id, erp_source_id) DO NOTHING;

-- Seed customers
INSERT INTO cdm_customer (tenant_id, erp_source_id, name, tier)
VALUES
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'CUST001', 'Acme Corp', 1),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'CUST002', 'Globex Inc', 2),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'CUST003', 'Initech', 3)
ON CONFLICT (tenant_id, erp_source_id) DO NOTHING;

-- Seed suppliers
INSERT INTO cdm_supplier (tenant_id, erp_source_id, name, reliability_score, avg_delay_days, delay_std_dev_days)
VALUES
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'SUPP001', 'Parts R Us', 0.95, 1.5, 0.8),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'SUPP002', 'Global Materials Ltd', 0.88, 3.2, 2.1),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'SUPP003', 'QuickShip Logistics', 0.75, 5.0, 4.0)
ON CONFLICT (tenant_id, erp_source_id) DO NOTHING;

-- Seed work centers
INSERT INTO cdm_work_center (tenant_id, erp_source_id, name, capacity_hours_per_day, oee, cost_per_hour, status)
VALUES
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'WC001', 'Assembly Line 1', 16.0, 0.92, 75.00, 'operational'),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'WC002', 'Machining Center', 8.0, 0.85, 120.00, 'operational'),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'WC003', 'Packaging Station', 8.0, 0.95, 45.00, 'operational')
ON CONFLICT (tenant_id, erp_source_id) DO NOTHING;

-- Seed operators
INSERT INTO cdm_operator (tenant_id, erp_source_id, name, skill_tags, cost_per_hour)
VALUES
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'OP001', 'John Smith', '["assembly","qc"]', 32.00),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'OP002', 'Jane Doe', '["machining","welding"]', 38.00),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'OP003', 'Bob Wilson', '["packaging","logistics"]', 28.00);

-- Seed locations
INSERT INTO cdm_location (id, tenant_id, erp_source_id, erp_source_type, name, location_type)
VALUES
  ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380b01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'LOC001', 'odoo', 'Main Warehouse', 'warehouse'),
  ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380b02', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'LOC002', 'odoo', 'Satellite Storage', 'warehouse'),
  ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380b03', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'LOC003', 'odoo', 'Dock Staging', 'dock');

-- ============ 30 DEMAND LINES ============
-- Varying customer_tier (1-3), margin_pct (5-45), required_date (3-90 days out), penalty_cost
INSERT INTO cdm_demand_line (tenant_id, erp_source_id, erp_source_type, product_id, quantity, required_date, demand_type, customer_id, customer_tier, margin_pct, penalty_cost, status)
SELECT
  'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  'DEM' || LPAD(ROW_NUMBER() OVER ()::text, 3, '0'),
  'odoo',
  p.id,
  (50 + RANDOM() * 950)::int,
  NOW() + (INTERVAL '1 day' * (3 + RANDOM() * 87)::int),
  CASE (RANDOM() * 3)::int
    WHEN 0 THEN 'MTO'
    WHEN 1 THEN 'MTS'
    WHEN 2 THEN 'ETO'
    ELSE 'MTO'
  END,
  c.id,
  (1 + RANDOM() * 3)::int,
  ROUND((5 + RANDOM() * 40)::numeric, 2),
  (RANDOM() * 50000)::int,
  'new'
FROM cdm_product p
CROSS JOIN cdm_customer c
WHERE RANDOM() < 0.5
LIMIT 30;

-- ============ 50 HISTORICAL SUPPLY ORDERS ============
-- Varied expected_date (past 90d to future 60d), actual_date (NULL for future, varied for past), quantity_ordered
INSERT INTO cdm_supply_order (tenant_id, erp_source_id, erp_source_type, product_id, supplier_id, quantity_ordered, quantity_received, expected_date, actual_date, status)
SELECT
  'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  'PO' || LPAD(ROW_NUMBER() OVER ()::text, 3, '0'),
  'odoo',
  p.id,
  s.id,
  (100 + RANDOM() * 4900)::int,
  CASE WHEN RANDOM() < 0.7 THEN (100 + RANDOM() * 4900)::int ELSE NULL END,
  NOW() - (INTERVAL '1 day' * (RANDOM() * 90)::int) + (INTERVAL '1 day' * (RANDOM() * 60)::int),
  CASE
    WHEN RANDOM() < 0.4 THEN NOW() - (INTERVAL '1 day' * (RANDOM() * 30)::int)
    WHEN RANDOM() < 0.7 THEN NOW() + (INTERVAL '1 day' * (RANDOM() * 30)::int)
    ELSE NULL
  END,
  CASE
    WHEN RANDOM() < 0.5 THEN 'confirmed'
    WHEN RANDOM() < 0.8 THEN 'in_transit'
    ELSE 'completed'
  END
FROM cdm_product p
CROSS JOIN cdm_supplier s
WHERE p.source_type = 'purchased'
LIMIT 50;

WITH supplier_order_rows AS (
  SELECT id, expected_date, RANDOM() AS rand
  FROM cdm_supply_order
  WHERE actual_date IS NOT NULL AND status != 'completed'
)
UPDATE cdm_supply_order so
SET status = CASE
  WHEN so.actual_date <= so.expected_date + INTERVAL '2 days' THEN 'completed'
  ELSE 'completed'
END,
actual_date = so.expected_date + (INTERVAL '1 day' * (CASE WHEN sor.rand < 0.3 THEN (1 + RANDOM() * 5)::int ELSE 0 END))
FROM supplier_order_rows sor
WHERE so.id = sor.id AND so.actual_date IS NULL;

-- ============ INVENTORY POSITIONS ============
INSERT INTO cdm_inventory_position (time, tenant_id, product_id, location_id, qty_on_hand, qty_reserved, qty_in_transit)
SELECT NOW(), 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', p.id, l.id,
  (50 + RANDOM() * 500)::int,
  (0 + RANDOM() * 100)::int,
  (0 + RANDOM() * 200)::int
FROM cdm_product p
CROSS JOIN cdm_location l
WHERE l.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
LIMIT 15;

SQL

echo "Seed data loaded successfully."
