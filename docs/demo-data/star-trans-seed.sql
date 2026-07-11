-- ============================================
-- IPE Star Trans Demo Data Seed
-- Egyptian electrical transformer manufacturer
-- Run after migrations:
--   docker compose exec -T db psql -U ipe -d ipe < star-trans-seed.sql
-- Or (PowerShell from repo root):
--   Get-Content docs/demo-data/star-trans-seed.sql -Raw |
--     docker compose -f deploy/star-trans/docker-compose.yml exec -T db psql -U ipe -d ipe
-- Idempotent: ON CONFLICT DO NOTHING / fixed UUIDs
-- ============================================

BEGIN;

-- Tenant context for RLS (migration 033+ uses app.current_tenant_id)
SELECT set_config('app.current_tenant_id', '00000000-0000-0000-0000-000000000001', false);

-- ---------------------------------------------------------------------------
-- TENANT
-- ---------------------------------------------------------------------------
INSERT INTO cdm_tenant (
  id, name, tier, erp_type, autonomy_mode, config, erp_version, erp_base_url, is_active
) VALUES (
  '00000000-0000-0000-0000-000000000001'::uuid,
  'Star Trans',
  'professional',
  'odoo',
  'shadow',
  '{
    "erp_type": "odoo",
    "odoo_url": "http://localhost:8069",
    "odoo_db": "star_trans",
    "sync_interval_seconds": 900,
    "plant": "10th of Ramadan City",
    "country": "EG",
    "currency": "EGP"
  }'::jsonb,
  '19.0',
  'http://localhost:8069',
  true
) ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- PRODUCTS (12) — finished / sub-assemblies / raw materials
-- source_type: manufactured | purchased | subcontracted
-- ---------------------------------------------------------------------------
INSERT INTO cdm_product (
  id, tenant_id, erp_source_id, name, source_type, erp_source_type,
  internal_ref, uom, standard_cost, unit_cost, list_price, lead_time_days, safety_stock, category_tags
) VALUES
  -- Finished goods
  ('10000000-0000-0000-0000-000000000001'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'ST-FG-DT100', 'Distribution Transformer 100KVA', 'manufactured', 'manufactured',
   'FG-DT100', 'unit', 32000, 32000, 45000, 21, 2, '["finished","transformer","distribution"]'::jsonb),
  ('10000000-0000-0000-0000-000000000002'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'ST-FG-DT250', 'Distribution Transformer 250KVA', 'manufactured', 'manufactured',
   'FG-DT250', 'unit', 58000, 58000, 85000, 28, 1, '["finished","transformer","distribution"]'::jsonb),
  ('10000000-0000-0000-0000-000000000003'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'ST-FG-PT500', 'Power Transformer 500KVA', 'manufactured', 'manufactured',
   'FG-PT500', 'unit', 112000, 112000, 165000, 42, 1, '["finished","transformer","power"]'::jsonb),
  -- Sub-assemblies
  ('10000000-0000-0000-0000-000000000004'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'ST-SA-HVW', 'HV Winding Assembly', 'manufactured', 'manufactured',
   'SA-HVW', 'unit', 8500, 8500, NULL, 7, 5, '["subassembly","winding"]'::jsonb),
  ('10000000-0000-0000-0000-000000000005'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'ST-SA-LVW', 'LV Winding Assembly', 'manufactured', 'manufactured',
   'SA-LVW', 'unit', 6200, 6200, NULL, 7, 5, '["subassembly","winding"]'::jsonb),
  ('10000000-0000-0000-0000-000000000006'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'ST-SA-CAL', 'Core Assembly L-type', 'manufactured', 'manufactured',
   'SA-CAL', 'unit', 12000, 12000, NULL, 5, 4, '["subassembly","core"]'::jsonb),
  ('10000000-0000-0000-0000-000000000007'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'ST-SA-CAE', 'Core Assembly E-type', 'manufactured', 'manufactured',
   'SA-CAE', 'unit', 15000, 15000, NULL, 6, 3, '["subassembly","core"]'::jsonb),
  -- Raw materials
  ('10000000-0000-0000-0000-000000000008'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'ST-RM-CW25', 'Copper Wire 2.5mm', 'purchased', 'purchased',
   'RM-CW25', 'kg', 180, 180, NULL, 14, 500, '["raw","copper"]'::jsonb),
  ('10000000-0000-0000-0000-000000000009'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'ST-RM-CW40', 'Copper Wire 4.0mm', 'purchased', 'purchased',
   'RM-CW40', 'kg', 195, 195, NULL, 14, 400, '["raw","copper"]'::jsonb),
  ('10000000-0000-0000-0000-00000000000a'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'ST-RM-SSL', 'Silicon Steel Lamination', 'purchased', 'purchased',
   'RM-SSL', 'kg', 85, 85, NULL, 21, 2000, '["raw","steel","crgo"]'::jsonb),
  ('10000000-0000-0000-0000-00000000000b'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'ST-RM-INS', 'Insulation Paper', 'purchased', 'purchased',
   'RM-INS', 'roll', 45, 45, NULL, 10, 50, '["raw","insulation"]'::jsonb),
  ('10000000-0000-0000-0000-00000000000c'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'ST-RM-OIL', 'Transformer Oil', 'purchased', 'purchased',
   'RM-OIL', 'L', 12, 12, NULL, 7, 2000, '["raw","oil"]'::jsonb)
ON CONFLICT (tenant_id, erp_source_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- WORK CENTRES (5)
-- capacity_hours_per_day = shifts × hours (Winding = 2 × 8 = 16)
-- ---------------------------------------------------------------------------
INSERT INTO cdm_work_center (
  id, tenant_id, erp_source_id, name, capacity_hours_per_day, oee, cost_per_hour, status, effective_capacity_hours
) VALUES
  ('20000000-0000-0000-0000-000000000001'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'WC-CCS', 'Core Cutting & Stacking', 8.0, 0.88, 95.00, 'operational', 8.0),
  ('20000000-0000-0000-0000-000000000002'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'WC-WND', 'Winding', 16.0, 0.82, 110.00, 'operational', 16.0),
  ('20000000-0000-0000-0000-000000000003'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'WC-ASM', 'Assembly', 8.0, 0.90, 85.00, 'operational', 8.0),
  ('20000000-0000-0000-0000-000000000004'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'WC-TQC', 'Testing & QC', 8.0, 0.94, 75.00, 'operational', 8.0),
  ('20000000-0000-0000-0000-000000000005'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'WC-PNT', 'Painting & Finishing', 8.0, 0.91, 65.00, 'operational', 8.0)
ON CONFLICT (tenant_id, erp_source_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- BOMs (3) + BOM LINES
-- ---------------------------------------------------------------------------
INSERT INTO cdm_bill_of_material (id, tenant_id, product_id, erp_source_id, version, is_active) VALUES
  ('30000000-0000-0000-0000-000000000001'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '10000000-0000-0000-0000-000000000001'::uuid, 'BOM-DT100', '1.0', true),
  ('30000000-0000-0000-0000-000000000002'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '10000000-0000-0000-0000-000000000002'::uuid, 'BOM-DT250', '1.0', true),
  ('30000000-0000-0000-0000-000000000003'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '10000000-0000-0000-0000-000000000003'::uuid, 'BOM-PT500', '1.0', true)
ON CONFLICT (id) DO NOTHING;

-- DT100: Core L(1), HV(1), LV(1), Insulation(3), Oil(50L)
INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, uom, is_critical) VALUES
  ('31000000-0000-0000-0000-000000000001'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000001'::uuid, '10000000-0000-0000-0000-000000000006'::uuid, 1, 'unit', true),
  ('31000000-0000-0000-0000-000000000002'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000001'::uuid, '10000000-0000-0000-0000-000000000004'::uuid, 1, 'unit', true),
  ('31000000-0000-0000-0000-000000000003'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000001'::uuid, '10000000-0000-0000-0000-000000000005'::uuid, 1, 'unit', true),
  ('31000000-0000-0000-0000-000000000004'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000001'::uuid, '10000000-0000-0000-0000-00000000000b'::uuid, 3, 'roll', false),
  ('31000000-0000-0000-0000-000000000005'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000001'::uuid, '10000000-0000-0000-0000-00000000000c'::uuid, 50, 'L', true),
  -- DT250: Core L(1), HV(1), LV(2), Insulation(5), Oil(120L)
  ('31000000-0000-0000-0000-000000000006'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000002'::uuid, '10000000-0000-0000-0000-000000000006'::uuid, 1, 'unit', true),
  ('31000000-0000-0000-0000-000000000007'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000002'::uuid, '10000000-0000-0000-0000-000000000004'::uuid, 1, 'unit', true),
  ('31000000-0000-0000-0000-000000000008'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000002'::uuid, '10000000-0000-0000-0000-000000000005'::uuid, 2, 'unit', true),
  ('31000000-0000-0000-0000-000000000009'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000002'::uuid, '10000000-0000-0000-0000-00000000000b'::uuid, 5, 'roll', false),
  ('31000000-0000-0000-0000-00000000000a'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000002'::uuid, '10000000-0000-0000-0000-00000000000c'::uuid, 120, 'L', true),
  -- PT500: Core E(1), HV(2), LV(2), Insulation(8), Oil(300L)
  ('31000000-0000-0000-0000-00000000000b'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000003'::uuid, '10000000-0000-0000-0000-000000000007'::uuid, 1, 'unit', true),
  ('31000000-0000-0000-0000-00000000000c'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000003'::uuid, '10000000-0000-0000-0000-000000000004'::uuid, 2, 'unit', true),
  ('31000000-0000-0000-0000-00000000000d'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000003'::uuid, '10000000-0000-0000-0000-000000000005'::uuid, 2, 'unit', true),
  ('31000000-0000-0000-0000-00000000000e'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000003'::uuid, '10000000-0000-0000-0000-00000000000b'::uuid, 8, 'roll', false),
  ('31000000-0000-0000-0000-00000000000f'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000003'::uuid, '10000000-0000-0000-0000-00000000000c'::uuid, 300, 'L', true)
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- ROUTING OPERATIONS (15 — 5 per finished product)
-- Sequence: Core Cutting(120) → Winding(360) → Assembly(180) → Testing(120) → Painting(90)
-- ---------------------------------------------------------------------------
INSERT INTO cdm_routing_operation (
  id, tenant_id, bom_id, sequence, work_center_id, operation_name, duration_planned_mins, setup_time_mins
) VALUES
  -- DT100
  ('40000000-0000-0000-0000-000000000001'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000001'::uuid, 10, '20000000-0000-0000-0000-000000000001'::uuid, 'Core Cutting & Stacking', 120, 15),
  ('40000000-0000-0000-0000-000000000002'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000001'::uuid, 20, '20000000-0000-0000-0000-000000000002'::uuid, 'Winding', 360, 30),
  ('40000000-0000-0000-0000-000000000003'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000001'::uuid, 30, '20000000-0000-0000-0000-000000000003'::uuid, 'Assembly', 180, 20),
  ('40000000-0000-0000-0000-000000000004'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000001'::uuid, 40, '20000000-0000-0000-0000-000000000004'::uuid, 'Testing & QC', 120, 10),
  ('40000000-0000-0000-0000-000000000005'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000001'::uuid, 50, '20000000-0000-0000-0000-000000000005'::uuid, 'Painting & Finishing', 90, 15),
  -- DT250
  ('40000000-0000-0000-0000-000000000006'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000002'::uuid, 10, '20000000-0000-0000-0000-000000000001'::uuid, 'Core Cutting & Stacking', 120, 15),
  ('40000000-0000-0000-0000-000000000007'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000002'::uuid, 20, '20000000-0000-0000-0000-000000000002'::uuid, 'Winding', 360, 30),
  ('40000000-0000-0000-0000-000000000008'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000002'::uuid, 30, '20000000-0000-0000-0000-000000000003'::uuid, 'Assembly', 180, 20),
  ('40000000-0000-0000-0000-000000000009'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000002'::uuid, 40, '20000000-0000-0000-0000-000000000004'::uuid, 'Testing & QC', 120, 10),
  ('40000000-0000-0000-0000-00000000000a'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000002'::uuid, 50, '20000000-0000-0000-0000-000000000005'::uuid, 'Painting & Finishing', 90, 15),
  -- PT500
  ('40000000-0000-0000-0000-00000000000b'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000003'::uuid, 10, '20000000-0000-0000-0000-000000000001'::uuid, 'Core Cutting & Stacking', 120, 15),
  ('40000000-0000-0000-0000-00000000000c'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000003'::uuid, 20, '20000000-0000-0000-0000-000000000002'::uuid, 'Winding', 360, 30),
  ('40000000-0000-0000-0000-00000000000d'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000003'::uuid, 30, '20000000-0000-0000-0000-000000000003'::uuid, 'Assembly', 180, 20),
  ('40000000-0000-0000-0000-00000000000e'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000003'::uuid, 40, '20000000-0000-0000-0000-000000000004'::uuid, 'Testing & QC', 120, 10),
  ('40000000-0000-0000-0000-00000000000f'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   '30000000-0000-0000-0000-000000000003'::uuid, 50, '20000000-0000-0000-0000-000000000005'::uuid, 'Painting & Finishing', 90, 15)
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- CUSTOMERS (3) + SUPPLIERS (3)
-- ---------------------------------------------------------------------------
INSERT INTO cdm_customer (id, tenant_id, erp_source_id, name, tier) VALUES
  ('50000000-0000-0000-0000-000000000001'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'CUST-EEUA', 'Egyptian Electric Utility Authority', 1),
  ('50000000-0000-0000-0000-000000000002'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'CUST-SEC', 'Saudi Electricity Company', 1),
  ('50000000-0000-0000-0000-000000000003'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'CUST-DEWA', 'Dubai Water & Electricity Authority', 1)
ON CONFLICT (tenant_id, erp_source_id) DO NOTHING;

INSERT INTO cdm_supplier (id, tenant_id, erp_source_id, name, reliability_score, avg_delay_days, delay_std_dev_days) VALUES
  ('60000000-0000-0000-0000-000000000001'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'SUPP-CCI', 'Cairo Copper Industries', 0.92, 2.0, 1.2),
  ('60000000-0000-0000-0000-000000000002'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'SUPP-SSS', 'Shanghai Silicon Steel Co.', 0.85, 5.5, 3.0),
  ('60000000-0000-0000-0000-000000000003'::uuid, '00000000-0000-0000-0000-000000000001'::uuid,
   'SUPP-NIP', 'National Insulation Products', 0.90, 1.5, 0.8)
ON CONFLICT (tenant_id, erp_source_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- MANUFACTURING ORDERS (10)
-- ---------------------------------------------------------------------------
INSERT INTO cdm_manufacturing_order (
  id, tenant_id, erp_mo_id, product_id, bom_id, quantity,
  planned_start, planned_end, actual_start,
  feasibility_score, material_score, capacity_score, labor_score,
  primary_constraint, status, variance_notes
) VALUES
  -- MO-ST-001: DT100 qty5 confirmed, start tomorrow, on-time
  ('70000000-0000-0000-0000-000000000001'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'MO-ST-001',
   '10000000-0000-0000-0000-000000000001'::uuid, '30000000-0000-0000-0000-000000000001'::uuid, 5,
   NOW() + INTERVAL '1 day', NOW() + INTERVAL '6 days', NULL,
   88.0, 90.0, 85.0, 90.0, NULL, 'confirmed', 'On-time — standard DT100 batch'),
  -- MO-ST-002: DT250 qty3 confirmed, start in 3 days, on-time
  ('70000000-0000-0000-0000-000000000002'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'MO-ST-002',
   '10000000-0000-0000-0000-000000000002'::uuid, '30000000-0000-0000-0000-000000000002'::uuid, 3,
   NOW() + INTERVAL '3 days', NOW() + INTERVAL '10 days', NULL,
   86.0, 88.0, 84.0, 88.0, NULL, 'confirmed', 'On-time'),
  -- MO-ST-003: PT500 qty2 in-progress, started 2 days ago, on-time
  ('70000000-0000-0000-0000-000000000003'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'MO-ST-003',
   '10000000-0000-0000-0000-000000000003'::uuid, '30000000-0000-0000-0000-000000000003'::uuid, 2,
   NOW() - INTERVAL '2 days', NOW() + INTERVAL '12 days', NOW() - INTERVAL '2 days',
   82.0, 80.0, 85.0, 84.0, NULL, 'in_progress', 'On-time — winding in progress'),
  -- MO-ST-004: DT100 qty8 confirmed, start next week, at-risk (Winding capacity)
  ('70000000-0000-0000-0000-000000000004'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'MO-ST-004',
   '10000000-0000-0000-0000-000000000001'::uuid, '30000000-0000-0000-0000-000000000001'::uuid, 8,
   NOW() + INTERVAL '7 days', NOW() + INTERVAL '14 days', NULL,
   55.0, 78.0, 42.0, 70.0, 'capacity_overload', 'confirmed',
   'AT-RISK: Winding work centre overloaded — capacity conflict with MO-ST-001/002'),
  -- MO-ST-005: DT250 qty4 in-progress, LATE (planned end was yesterday)
  ('70000000-0000-0000-0000-000000000005'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'MO-ST-005',
   '10000000-0000-0000-0000-000000000002'::uuid, '30000000-0000-0000-0000-000000000002'::uuid, 4,
   NOW() - INTERVAL '10 days', NOW() - INTERVAL '1 day', NOW() - INTERVAL '10 days',
   38.0, 65.0, 40.0, 55.0, 'capacity_overload', 'in_progress',
   'LATE: Planned end was yesterday — Testing & QC backlog'),
  -- MO-ST-006: PT500 qty1 confirmed, start in 2 weeks, on-time
  ('70000000-0000-0000-0000-000000000006'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'MO-ST-006',
   '10000000-0000-0000-0000-000000000003'::uuid, '30000000-0000-0000-0000-000000000003'::uuid, 1,
   NOW() + INTERVAL '14 days', NOW() + INTERVAL '28 days', NULL,
   90.0, 92.0, 88.0, 90.0, NULL, 'confirmed', 'On-time'),
  -- MO-ST-007: DT100 qty10 confirmed, start in 3 weeks, at-risk (copper shortage)
  ('70000000-0000-0000-0000-000000000007'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'MO-ST-007',
   '10000000-0000-0000-0000-000000000001'::uuid, '30000000-0000-0000-0000-000000000001'::uuid, 10,
   NOW() + INTERVAL '21 days', NOW() + INTERVAL '30 days', NULL,
   48.0, 35.0, 75.0, 80.0, 'material_shortage', 'confirmed',
   'AT-RISK: Copper wire 2.5mm shortage — PO-ST-CW25 expected late'),
  -- MO-ST-008: DT250 qty2 in-progress, started 3 days ago, on-time
  ('70000000-0000-0000-0000-000000000008'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'MO-ST-008',
   '10000000-0000-0000-0000-000000000002'::uuid, '30000000-0000-0000-0000-000000000002'::uuid, 2,
   NOW() - INTERVAL '3 days', NOW() + INTERVAL '5 days', NOW() - INTERVAL '3 days',
   84.0, 86.0, 82.0, 85.0, NULL, 'in_progress', 'On-time'),
  -- MO-ST-009: DT100 qty6 draft, planned for next month
  ('70000000-0000-0000-0000-000000000009'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'MO-ST-009',
   '10000000-0000-0000-0000-000000000001'::uuid, '30000000-0000-0000-0000-000000000001'::uuid, 6,
   NOW() + INTERVAL '30 days', NOW() + INTERVAL '40 days', NULL,
   NULL, NULL, NULL, NULL, NULL, 'draft', 'Draft — next month capacity plan'),
  -- MO-ST-010: PT500 qty3 confirmed, start in 4 weeks, on-time
  ('70000000-0000-0000-0000-00000000000a'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'MO-ST-010',
   '10000000-0000-0000-0000-000000000003'::uuid, '30000000-0000-0000-0000-000000000003'::uuid, 3,
   NOW() + INTERVAL '28 days', NOW() + INTERVAL '45 days', NULL,
   87.0, 85.0, 88.0, 90.0, NULL, 'confirmed', 'On-time')
ON CONFLICT (id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- DEMAND LINES (6)
-- ---------------------------------------------------------------------------
INSERT INTO cdm_demand_line (
  id, tenant_id, erp_source_id, product_id, quantity, required_date,
  demand_type, erp_source_type, uom, customer_id, customer_tier, margin_pct, status, mo_id, revenue
) VALUES
  ('80000000-0000-0000-0000-000000000001'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'DEM-ST-001',
   '10000000-0000-0000-0000-000000000001'::uuid, 5, NOW() + INTERVAL '14 days',
   'customer', 'sale_order', 'unit', '50000000-0000-0000-0000-000000000001'::uuid, 1, 28.5, 'confirmed',
   '70000000-0000-0000-0000-000000000001'::uuid, 225000),
  ('80000000-0000-0000-0000-000000000002'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'DEM-ST-002',
   '10000000-0000-0000-0000-000000000002'::uuid, 3, NOW() + INTERVAL '18 days',
   'customer', 'sale_order', 'unit', '50000000-0000-0000-0000-000000000002'::uuid, 1, 31.0, 'confirmed',
   '70000000-0000-0000-0000-000000000002'::uuid, 255000),
  ('80000000-0000-0000-0000-000000000003'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'DEM-ST-003',
   '10000000-0000-0000-0000-000000000003'::uuid, 2, NOW() + INTERVAL '25 days',
   'customer', 'sale_order', 'unit', '50000000-0000-0000-0000-000000000003'::uuid, 1, 32.0, 'confirmed',
   '70000000-0000-0000-0000-000000000003'::uuid, 330000),
  ('80000000-0000-0000-0000-000000000004'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'DEM-ST-004',
   '10000000-0000-0000-0000-000000000001'::uuid, 8, NOW() + INTERVAL '21 days',
   'customer', 'sale_order', 'unit', '50000000-0000-0000-0000-000000000001'::uuid, 1, 27.0, 'confirmed',
   '70000000-0000-0000-0000-000000000004'::uuid, 360000),
  ('80000000-0000-0000-0000-000000000005'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'DEM-ST-005',
   '10000000-0000-0000-0000-000000000002'::uuid, 4, NOW() + INTERVAL '2 days',
   'customer', 'sale_order', 'unit', '50000000-0000-0000-0000-000000000002'::uuid, 1, 30.0, 'confirmed',
   '70000000-0000-0000-0000-000000000005'::uuid, 340000),
  ('80000000-0000-0000-0000-000000000006'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'DEM-ST-006',
   '10000000-0000-0000-0000-000000000003'::uuid, 1, NOW() + INTERVAL '35 days',
   'customer', 'sale_order', 'unit', '50000000-0000-0000-0000-000000000003'::uuid, 1, 33.0, 'draft',
   '70000000-0000-0000-0000-000000000006'::uuid, 165000)
ON CONFLICT (tenant_id, erp_source_id) DO NOTHING;

-- ---------------------------------------------------------------------------
-- SUPPLY ORDERS (4) — copper, silicon steel, insulation, oil
-- ---------------------------------------------------------------------------
INSERT INTO cdm_supply_order (
  id, tenant_id, erp_source_id, product_id, supplier_id,
  quantity_ordered, expected_date, status, erp_source_type, quantity_received
) VALUES
  ('90000000-0000-0000-0000-000000000001'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'PO-ST-CW25',
   '10000000-0000-0000-0000-000000000008'::uuid, '60000000-0000-0000-0000-000000000001'::uuid,
   2500, NOW() + INTERVAL '18 days', 'confirmed', 'purchase_order', 0),
  ('90000000-0000-0000-0000-000000000002'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'PO-ST-SSL',
   '10000000-0000-0000-0000-00000000000a'::uuid, '60000000-0000-0000-0000-000000000002'::uuid,
   8000, NOW() + INTERVAL '12 days', 'confirmed', 'purchase_order', 0),
  ('90000000-0000-0000-0000-000000000003'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'PO-ST-INS',
   '10000000-0000-0000-0000-00000000000b'::uuid, '60000000-0000-0000-0000-000000000003'::uuid,
   120, NOW() + INTERVAL '5 days', 'confirmed', 'purchase_order', 40),
  ('90000000-0000-0000-0000-000000000004'::uuid, '00000000-0000-0000-0000-000000000001'::uuid, 'PO-ST-OIL',
   '10000000-0000-0000-0000-00000000000c'::uuid, '60000000-0000-0000-0000-000000000003'::uuid,
   5000, NOW() + INTERVAL '7 days', 'confirmed', 'purchase_order', 1000)
ON CONFLICT (tenant_id, erp_source_id) DO NOTHING;

COMMIT;

-- Verification counts (run after commit)
-- SELECT 'products' AS entity, COUNT(*) FROM cdm_product WHERE tenant_id = '00000000-0000-0000-0000-000000000001'
-- UNION ALL SELECT 'work_centers', COUNT(*) FROM cdm_work_center WHERE tenant_id = '00000000-0000-0000-0000-000000000001'
-- UNION ALL SELECT 'boms', COUNT(*) FROM cdm_bill_of_material WHERE tenant_id = '00000000-0000-0000-0000-000000000001'
-- UNION ALL SELECT 'routing_ops', COUNT(*) FROM cdm_routing_operation WHERE tenant_id = '00000000-0000-0000-0000-000000000001'
-- UNION ALL SELECT 'mos', COUNT(*) FROM cdm_manufacturing_order WHERE tenant_id = '00000000-0000-0000-0000-000000000001'
-- UNION ALL SELECT 'customers', COUNT(*) FROM cdm_customer WHERE tenant_id = '00000000-0000-0000-0000-000000000001'
-- UNION ALL SELECT 'suppliers', COUNT(*) FROM cdm_supplier WHERE tenant_id = '00000000-0000-0000-0000-000000000001'
-- UNION ALL SELECT 'demand', COUNT(*) FROM cdm_demand_line WHERE tenant_id = '00000000-0000-0000-0000-000000000001'
-- UNION ALL SELECT 'supply', COUNT(*) FROM cdm_supply_order WHERE tenant_id = '00000000-0000-0000-0000-000000000001';
