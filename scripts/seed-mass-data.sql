-- Mass load: 40 additional MOs, demand lines, chaos snapshots, delay events
-- Run after seed-data.ps1 + seed-demo-client.ps1
-- Tenant: Demo Manufacturing Inc

SELECT set_config('app.current_tenant_id', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', false);

DELETE FROM cdm_manufacturing_order
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_mo_id LIKE 'MO-MASS-%';

DELETE FROM cdm_demand_line
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id LIKE 'DEM-MASS-%';

DELETE FROM cdm_chaos_cost_snapshot
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

-- 40 manufacturing orders (stress scheduler, feasibility queue, analytics)
INSERT INTO cdm_manufacturing_order (
  id, tenant_id, erp_mo_id, product_id, bom_id, quantity,
  planned_start, planned_end, feasibility_score, material_score, capacity_score, labor_score,
  primary_constraint, status, disruption_status
)
SELECT
  ('e2eebc99-9c0b-4ef8-bb6d-' || lpad(to_hex(i), 12, '0'))::uuid,
  'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  'MO-MASS-' || lpad(i::text, 3, '0'),
  CASE (i % 3)
    WHEN 0 THEN (SELECT id FROM cdm_product WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'PROD001')
    WHEN 1 THEN (SELECT id FROM cdm_product WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'PROD002')
    ELSE (SELECT id FROM cdm_product WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'PROD004')
  END,
  CASE (i % 3)
    WHEN 0 THEN 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01'::uuid
    WHEN 1 THEN 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02'::uuid
    ELSE 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03'::uuid
  END,
  (50 + (i * 17) % 450)::numeric,
  NOW() + (i || ' days')::interval,
  NOW() + ((i + 5) || ' days')::interval,
  (45 + (i * 7) % 50)::numeric,
  (40 + (i * 11) % 55)::numeric,
  (50 + (i * 13) % 45)::numeric,
  (55 + (i * 9) % 40)::numeric,
  CASE (i % 4)
    WHEN 0 THEN 'material_shortage'
    WHEN 1 THEN 'capacity_overload'
    WHEN 2 THEN 'labor_shortage'
    ELSE NULL
  END,
  CASE WHEN i % 5 = 0 THEN 'completed' WHEN i % 3 = 0 THEN 'in_progress' ELSE 'planned' END,
  CASE WHEN i % 6 = 0 THEN 'impacted' ELSE 'none' END
FROM generate_series(1, 40) AS i;

-- 80 mass demand lines
INSERT INTO cdm_demand_line (
  id, tenant_id, erp_source_id, erp_source_type, product_id, quantity, uom,
  required_date, demand_type, customer_id, customer_tier, margin_pct, penalty_cost, priority_score, status
)
SELECT
  ('f2eebc99-9c0b-4ef8-bb6d-' || lpad(to_hex(i), 12, '0'))::uuid,
  'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  'DEM-MASS-' || lpad(i::text, 3, '0'),
  'odoo',
  p.id,
  (25 + (i * 13) % 800)::numeric,
  'unit',
  NOW() + ((i % 30 + 1) || ' days')::interval,
  CASE (i % 3) WHEN 0 THEN 'MTO' WHEN 1 THEN 'MTS' ELSE 'ETO' END,
  c.id,
  (1 + (i % 3))::int,
  ROUND((8 + (i * 3) % 35)::numeric, 2),
  (1000 + (i * 500) % 40000)::numeric,
  ROUND((0.5 + (i % 50) / 100.0)::numeric, 2),
  'classified'
FROM generate_series(1, 80) AS i
CROSS JOIN LATERAL (
  SELECT id FROM cdm_product
  WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  ORDER BY erp_source_id
  OFFSET (i % 5) LIMIT 1
) p
CROSS JOIN LATERAL (
  SELECT id FROM cdm_customer
  WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  ORDER BY erp_source_id
  OFFSET (i % 3) LIMIT 1
) c;

-- Chaos cost snapshots (7 days — V6-R5 Cost of Chaos dashboard)
INSERT INTO cdm_chaos_cost_snapshot (tenant_id, snapshot_date, total_chaos_usd, categories, top_mos, war_room_links)
SELECT
  'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  (CURRENT_DATE - d)::date,
  (12000 + d * 1500 + random() * 3000)::numeric(14,2),
  jsonb_build_array(
    jsonb_build_object('category', 'material', 'usd', (3000 + d * 400)::float),
    jsonb_build_object('category', 'capacity', 'usd', (2500 + d * 350)::float),
    jsonb_build_object('category', 'labor', 'usd', (1800 + d * 200)::float),
    jsonb_build_object('category', 'supplier', 'usd', (2200 + d * 280)::float),
    jsonb_build_object('category', 'quality', 'usd', (900 + d * 120)::float),
    jsonb_build_object('category', 'equipment', 'usd', (600 + d * 90)::float)
  ),
  jsonb_build_array(
    jsonb_build_object('mo_id', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380001', 'chaos_usd', 4200),
    jsonb_build_object('mo_id', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380007', 'chaos_usd', 8900)
  ),
  jsonb_build_array(jsonb_build_object('route', '/war-room', 'severity', 'high'))
FROM generate_series(0, 6) AS d;

-- Extra delay events tied to mass MOs (analytics / war room)
INSERT INTO cdm_delay_event (id, tenant_id, mo_id, cause_category, cause_detail, classification_method, classification_confidence, delay_minutes, cost_impact)
SELECT
  ('d3eebc99-9c0b-4ef8-bb6d-' || lpad(to_hex(i), 12, '0'))::uuid,
  'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  mo.id,
  CASE (i % 6)
    WHEN 0 THEN 'material'
    WHEN 1 THEN 'capacity'
    WHEN 2 THEN 'labor'
    WHEN 3 THEN 'supplier'
    WHEN 4 THEN 'quality'
    ELSE 'equipment'
  END,
  'Mass seed delay event #' || i,
  CASE WHEN i % 2 = 0 THEN 'rule' ELSE 'manual' END,
  ROUND((0.7 + (i % 30) / 100.0)::numeric, 2),
  (30 + (i * 17) % 4800)::int,
  (200 + (i * 89) % 12000)::numeric
FROM generate_series(1, 25) AS i
JOIN cdm_manufacturing_order mo
  ON mo.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
 AND mo.erp_mo_id = 'MO-MASS-' || lpad(i::text, 3, '0');
