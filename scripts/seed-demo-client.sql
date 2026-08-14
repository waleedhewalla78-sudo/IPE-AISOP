-- Client demo seed: MOs, BOMs, routing, resolution, delays, executive metrics
-- Tenant: Demo Manufacturing Inc (run after seed-data.sh base master data)

SELECT set_config('app.current_tenant_id', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', false);

-- Clear prior demo MO graph (idempotent re-run)
DELETE FROM cdm_resolution_scenario
WHERE mo_id IN (SELECT id FROM cdm_manufacturing_order WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_mo_id LIKE 'MO-DEMO-%');

DELETE FROM cdm_delay_event
WHERE mo_id IN (SELECT id FROM cdm_manufacturing_order WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_mo_id LIKE 'MO-DEMO-%');

DELETE FROM cdm_disruption_event
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

DELETE FROM cdm_work_order
WHERE mo_id IN (SELECT id FROM cdm_manufacturing_order WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_mo_id LIKE 'MO-DEMO-%');

DELETE FROM cdm_demand_line
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id LIKE 'DEM-DEMO-%';

DELETE FROM cdm_manufacturing_order
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_mo_id LIKE 'MO-DEMO-%';

-- Ensure base master data exists (partial base seed recovery)
INSERT INTO cdm_work_center (tenant_id, erp_source_id, name, capacity_hours_per_day, oee, cost_per_hour, status)
VALUES
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'WC001', 'Assembly Line 1', 16.0, 0.92, 75.00, 'operational'),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'WC002', 'Machining Center', 8.0, 0.85, 120.00, 'operational'),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'WC003', 'Packaging Station', 8.0, 0.95, 45.00, 'operational')
ON CONFLICT (tenant_id, erp_source_id) DO NOTHING;

INSERT INTO cdm_operator (tenant_id, erp_source_id, name, skill_tags, cost_per_hour)
VALUES
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'OP001', 'John Smith', '["assembly","qc"]', 32.00),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'OP002', 'Jane Doe', '["machining","welding"]', 38.00),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'OP003', 'Bob Wilson', '["packaging","logistics"]', 28.00)
ON CONFLICT (tenant_id, erp_source_id) DO NOTHING;

INSERT INTO cdm_supplier (tenant_id, erp_source_id, name, reliability_score, avg_delay_days, delay_std_dev_days)
VALUES
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'SUPP001', 'Parts R Us', 0.95, 1.5, 0.8),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'SUPP002', 'Global Materials Ltd', 0.88, 3.2, 2.1),
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'SUPP003', 'QuickShip Logistics', 0.75, 5.0, 4.0)
ON CONFLICT (tenant_id, erp_source_id) DO NOTHING;

-- BOMs (PROD001 / PROD002 / PROD004 — Star Trans transformers)
INSERT INTO cdm_bill_of_material (id, tenant_id, product_id, erp_source_id, version, is_active)
SELECT 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', p.id, 'BOM-DT-500', '1.0', true
FROM cdm_product p WHERE p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND p.erp_source_id = 'PROD001'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bill_of_material (id, tenant_id, product_id, erp_source_id, version, is_active)
SELECT 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', p.id, 'BOM-PM-250', '1.0', true
FROM cdm_product p WHERE p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND p.erp_source_id = 'PROD002'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bill_of_material (id, tenant_id, product_id, erp_source_id, version, is_active)
SELECT 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', p.id, 'BOM-PT-50M', '1.0', true
FROM cdm_product p WHERE p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND p.erp_source_id = 'PROD004'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380b01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', comp.id, 2.0, true
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'PROD003'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380b02', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', comp.id, 1.5, false
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'PROD003'
ON CONFLICT (id) DO NOTHING;

-- Routing (3 ops per BOM -> Schedule solver)
INSERT INTO cdm_routing_operation (id, tenant_id, bom_id, sequence, work_center_id, operation_name, duration_planned_mins, setup_time_mins)
SELECT 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 10, wc.id, 'Wind LV/HV Coils', 90, 15
FROM cdm_work_center wc WHERE wc.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND wc.erp_source_id = 'WC002'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_routing_operation (id, tenant_id, bom_id, sequence, work_center_id, operation_name, duration_planned_mins, setup_time_mins)
SELECT 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c02', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 20, wc.id, 'Core & Coil Assembly', 120, 20
FROM cdm_work_center wc WHERE wc.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND wc.erp_source_id = 'WC001'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_routing_operation (id, tenant_id, bom_id, sequence, work_center_id, operation_name, duration_planned_mins, setup_time_mins)
SELECT 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c03', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 30, wc.id, 'Tank Fit-Up & Vacuum Test', 45, 10
FROM cdm_work_center wc WHERE wc.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND wc.erp_source_id = 'WC003'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_routing_operation (id, tenant_id, bom_id, sequence, work_center_id, operation_name, duration_planned_mins, setup_time_mins)
SELECT 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c04', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 10, wc.id, 'Wind Pad-Mount Coils', 150, 25
FROM cdm_work_center wc WHERE wc.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND wc.erp_source_id = 'WC002'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_routing_operation (id, tenant_id, bom_id, sequence, work_center_id, operation_name, duration_planned_mins, setup_time_mins)
SELECT 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c05', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 20, wc.id, 'Pad-Mount Final Test', 60, 5
FROM cdm_work_center wc WHERE wc.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND wc.erp_source_id = 'WC003'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_routing_operation (id, tenant_id, bom_id, sequence, work_center_id, operation_name, duration_planned_mins, setup_time_mins)
SELECT 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c06', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 10, wc.id, 'Build Assembly D', 180, 30
FROM cdm_work_center wc WHERE wc.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND wc.erp_source_id = 'WC001'
ON CONFLICT (id) DO NOTHING;

-- Manufacturing orders (feasibility scores drive Control Tower + Resolution)
INSERT INTO cdm_manufacturing_order (
  id, tenant_id, erp_mo_id, product_id, bom_id, quantity,
  planned_start, planned_end, actual_start, actual_end,
  feasibility_score, material_score, capacity_score, labor_score,
  primary_constraint, status, autonomy_action, disruption_status
) VALUES
  ('d1eebc99-9c0b-4ef8-bb6d-6bb9bd380001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'MO-DEMO-001',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD001' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 500,
   NOW() + INTERVAL '1 day', NOW() + INTERVAL '4 days', NOW() - INTERVAL '4 hours', NULL,
   52.0, 45.0, 70.0, 80.0, 'material_shortage', 'in_progress', NULL, 'impacted'),
  ('d1eebc99-9c0b-4ef8-bb6d-6bb9bd380002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'MO-DEMO-002',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD002' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 250,
   NOW() + INTERVAL '2 days', NOW() + INTERVAL '6 days', NULL, NULL,
   68.0, 72.0, 55.0, 75.0, 'capacity_overload', 'planned', NULL, 'impacted'),
  ('d1eebc99-9c0b-4ef8-bb6d-6bb9bd380003', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'MO-DEMO-003',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD004' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 120,
   NOW() + INTERVAL '3 days', NOW() + INTERVAL '8 days', NULL, NULL,
   74.0, 80.0, 78.0, 60.0, 'labor_shortage', 'planned', NULL, 'none'),
  ('d1eebc99-9c0b-4ef8-bb6d-6bb9bd380004', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'MO-DEMO-004',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD001' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 300,
   NOW() + INTERVAL '5 days', NOW() + INTERVAL '9 days', NULL, NULL,
   81.0, 85.0, 82.0, 88.0, NULL, 'confirmed', NULL, 'none'),
  ('d1eebc99-9c0b-4ef8-bb6d-6bb9bd380005', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'MO-DEMO-005',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD002' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 180,
   NOW() - INTERVAL '1 day', NOW() + INTERVAL '2 days', NOW() - INTERVAL '1 day', NULL,
   88.0, 90.0, 86.0, 92.0, NULL, 'in_progress', NULL, 'none'),
  ('d1eebc99-9c0b-4ef8-bb6d-6bb9bd380006', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'MO-DEMO-006',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD004' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 90,
   NOW() + INTERVAL '7 days', NOW() + INTERVAL '12 days', NULL, NULL,
   91.0, 92.0, 90.0, 89.0, NULL, 'confirmed', NULL, 'none'),
  ('d1eebc99-9c0b-4ef8-bb6d-6bb9bd380007', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'MO-DEMO-007',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD001' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 600,
   NOW() + INTERVAL '2 days', NOW() + INTERVAL '5 days', NULL, NULL,
   45.0, 40.0, 50.0, 55.0, 'material_shortage', 'planned', NULL, 'impacted'),
  ('d1eebc99-9c0b-4ef8-bb6d-6bb9bd380008', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'MO-DEMO-008',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD002' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 400,
   NOW() + INTERVAL '4 days', NOW() + INTERVAL '10 days', NULL, NULL,
   62.0, 65.0, 58.0, 70.0, 'capacity_overload', 'planned', NULL, 'impacted'),
  ('d1eebc99-9c0b-4ef8-bb6d-6bb9bd380009', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'MO-DEMO-009',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD001' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 200,
   NOW() - INTERVAL '14 days', NOW() - INTERVAL '10 days', NOW() - INTERVAL '14 days', NOW() - INTERVAL '10 days',
   95.0, 94.0, 96.0, 93.0, NULL, 'completed', NULL, 'resolved'),
  ('d1eebc99-9c0b-4ef8-bb6d-6bb9bd380010', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'MO-DEMO-010',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD002' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 150,
   NOW() - INTERVAL '21 days', NOW() - INTERVAL '17 days', NOW() - INTERVAL '21 days', NOW() - INTERVAL '16 days',
   93.0, 91.0, 94.0, 90.0, NULL, 'completed', 'auto_confirmed', 'resolved');

-- Demand lines linked to MOs (dashboard + queue context)
INSERT INTO cdm_demand_line (id, tenant_id, erp_source_id, erp_source_type, product_id, quantity, uom, required_date, demand_type, customer_id, customer_tier, margin_pct, penalty_cost, priority_score, status, mo_id)
VALUES
  ('a2eebc99-9c0b-4ef8-bb6d-6bb9bd380001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'DEM-DEMO-001', 'odoo',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD001' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   500, 'unit', NOW() + INTERVAL '5 days', 'MTO',
   (SELECT id FROM cdm_customer WHERE erp_source_id='CUST001' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   1, 32.5, 25000, 0.92, 'classified', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380001'),
  ('a2eebc99-9c0b-4ef8-bb6d-6bb9bd380002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'DEM-DEMO-002', 'odoo',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD002' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   250, 'unit', NOW() + INTERVAL '7 days', 'MTO',
   (SELECT id FROM cdm_customer WHERE erp_source_id='CUST002' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   2, 28.0, 18000, 0.85, 'classified', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380002'),
  ('a2eebc99-9c0b-4ef8-bb6d-6bb9bd380003', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'DEM-DEMO-003', 'odoo',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD004' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   120, 'unit', NOW() + INTERVAL '9 days', 'ETO',
   (SELECT id FROM cdm_customer WHERE erp_source_id='CUST003' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   3, 22.0, 12000, 0.78, 'classified', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380003'),
  ('a2eebc99-9c0b-4ef8-bb6d-6bb9bd380004', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'DEM-DEMO-004', 'odoo',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD001' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   600, 'unit', NOW() + INTERVAL '4 days', 'MTO',
   (SELECT id FROM cdm_customer WHERE erp_source_id='CUST001' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   1, 35.0, 45000, 0.95, 'classified', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380007'),
  ('a2eebc99-9c0b-4ef8-bb6d-6bb9bd380005', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'DEM-DEMO-005', 'odoo',
   (SELECT id FROM cdm_product WHERE erp_source_id='PROD002' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   400, 'unit', NOW() + INTERVAL '11 days', 'MTS',
   (SELECT id FROM cdm_customer WHERE erp_source_id='CUST002' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   2, 18.0, 8000, 0.72, 'classified', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380008');

-- Resolution scenarios (Resolution Center)
INSERT INTO cdm_resolution_scenario (id, tenant_id, mo_id, strategy, description, delivery_impact_days, cost_impact, business_score, status) VALUES
  ('c1eebc99-9c0b-4ef8-bb6d-6bb9bd380001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380001', 'expedite_po', 'Expedite Component C purchase order from Parts R Us', 1.0, 4200.00, 0.82, 'proposed'),
  ('c1eebc99-9c0b-4ef8-bb6d-6bb9bd380002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380001', 'substitute_material', 'Use alternate supplier for Component C', 2.0, 1800.00, 0.74, 'proposed'),
  ('c1eebc99-9c0b-4ef8-bb6d-6bb9bd380003', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380001', 'split_mo', 'Split MO into two batches to reduce material peak', 3.0, 950.00, 0.68, 'proposed'),
  ('c1eebc99-9c0b-4ef8-bb6d-6bb9bd380004', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380002', 'overtime', 'Add Saturday overtime on Machining Center', 0.5, 5600.00, 0.79, 'proposed'),
  ('c1eebc99-9c0b-4ef8-bb6d-6bb9bd380005', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380002', 'alternate_wc', 'Route to backup CNC cell', 1.5, 2100.00, 0.71, 'approved'),
  ('c1eebc99-9c0b-4ef8-bb6d-6bb9bd380006', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380007', 'expedite_po', 'Emergency PO for Raw Material E', 0.0, 8900.00, 0.85, 'proposed'),
  ('c1eebc99-9c0b-4ef8-bb6d-6bb9bd380007', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380007', 'defer_mo', 'Defer MO-DEMO-007 by 5 days (customer Tier 1 penalty)', 5.0, 12000.00, 0.55, 'proposed'),
  ('c1eebc99-9c0b-4ef8-bb6d-6bb9bd380008', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380008', 'overtime', 'Weekend shift on Assembly Line 1', 1.0, 4800.00, 0.76, 'proposed');

-- Active disruption events (War Room recovery plan — V6-R5)
INSERT INTO cdm_disruption_event (id, tenant_id, mo_id, work_center_id, event_type, severity, description, detected_at, metadata)
VALUES
  ('f2eebc99-9c0b-4ef8-bb6d-6bb9bd380001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
   'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380001',
   (SELECT id FROM cdm_work_center WHERE erp_source_id='WC002' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   'maintenance', 'high', 'Predictive maintenance block on Machining Center (RUL 36h)',
   NOW() - INTERVAL '2 hours', '{"impacted_mo_count": 1, "source": "iot_telemetry"}'::jsonb),
  ('f2eebc99-9c0b-4ef8-bb6d-6bb9bd380002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
   'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380007',
   NULL, 'material', 'critical', 'Raw Material E below safety stock — supplier delay',
   NOW() - INTERVAL '6 hours', '{"impacted_mo_count": 1, "source": "delay_feed"}'::jsonb);

-- Delay events (Executive + War Room + dashboard alerts)
INSERT INTO cdm_delay_event (id, tenant_id, mo_id, cause_category, cause_detail, classification_method, classification_confidence, delay_minutes, cost_impact, linked_wc_id) VALUES
  ('d2eebc99-9c0b-4ef8-bb6d-6bb9bd380001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380001', 'material', 'Component C PO delayed 2 days', 'manual', 0.92, 2880, 4200.00,
   (SELECT id FROM cdm_work_center WHERE erp_source_id='WC001' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11')),
  ('d2eebc99-9c0b-4ef8-bb6d-6bb9bd380002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380002', 'capacity', 'Machining Center at 96% utilization', 'rule', 0.88, 360, 2100.00,
   (SELECT id FROM cdm_work_center WHERE erp_source_id='WC002' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11')),
  ('d2eebc99-9c0b-4ef8-bb6d-6bb9bd380003', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380003', 'labor', 'Welder absent - skill gap on Assembly D', 'manual', 0.85, 480, 1500.00,
   (SELECT id FROM cdm_work_center WHERE erp_source_id='WC001' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11')),
  ('d2eebc99-9c0b-4ef8-bb6d-6bb9bd380004', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380007', 'material', 'Raw Material E below safety stock', 'rule', 0.91, 4320, 8900.00, NULL),
  ('d2eebc99-9c0b-4ef8-bb6d-6bb9bd380005', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380008', 'capacity', 'Assembly line changeover overrun', 'manual', 0.80, 120, 800.00,
   (SELECT id FROM cdm_work_center WHERE erp_source_id='WC001' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11')),
  ('d2eebc99-9c0b-4ef8-bb6d-6bb9bd380006', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380009', 'quality', 'Minor rework on packaging step', 'manual', 0.75, 90, 450.00,
   (SELECT id FROM cdm_work_center WHERE erp_source_id='WC003' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11')),
  ('d2eebc99-9c0b-4ef8-bb6d-6bb9bd380007', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380010', 'supplier', 'Supplier shipment arrived 1 day early', 'rule', 0.95, -1440, -500.00, NULL),
  ('d2eebc99-9c0b-4ef8-bb6d-6bb9bd380008', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380005', 'equipment', 'CNC spindle warmup extended', 'manual', 0.82, 45, 320.00,
   (SELECT id FROM cdm_work_center WHERE erp_source_id='WC002' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'));

-- Work orders for shop floor (in-progress MOs)
INSERT INTO cdm_work_order (id, tenant_id, mo_id, routing_op_id, work_center_id, operator_id, sequence, status)
VALUES
  ('a3eebc99-9c0b-4ef8-bb6d-6bb9bd380001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380001', 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c02', 
   (SELECT id FROM cdm_work_center WHERE erp_source_id='WC001' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   (SELECT id FROM cdm_operator WHERE erp_source_id='OP001' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'), 20, 'in_progress'),
  ('a3eebc99-9c0b-4ef8-bb6d-6bb9bd380002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380005', 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c04',
   (SELECT id FROM cdm_work_center WHERE erp_source_id='WC002' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   (SELECT id FROM cdm_operator WHERE erp_source_id='OP002' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'), 10, 'in_progress'),
  ('a3eebc99-9c0b-4ef8-bb6d-6bb9bd380003', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'd1eebc99-9c0b-4ef8-bb6d-6bb9bd380005', 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c05',
   (SELECT id FROM cdm_work_center WHERE erp_source_id='WC003' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'),
   (SELECT id FROM cdm_operator WHERE erp_source_id='OP003' AND tenant_id='a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'), 20, 'pending');

-- V6-R1: Activity cost drivers (DT-500 high margin, pad-mount lower after overhead)
DELETE FROM cdm_activity_cost_drivers
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

INSERT INTO cdm_activity_cost_drivers (tenant_id, product_id, setup_mins, overtime_rate_usd_per_hr, expedite_cost_per_unit, overhead_pct)
SELECT 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', p.id, 12, 85.00, 0.50, 0.08
FROM cdm_product p
WHERE p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND p.erp_source_id = 'PROD001';

INSERT INTO cdm_activity_cost_drivers (tenant_id, product_id, setup_mins, overtime_rate_usd_per_hr, expedite_cost_per_unit, overhead_pct)
SELECT 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', p.id, 45, 120.00, 3.50, 0.22
FROM cdm_product p
WHERE p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND p.erp_source_id = 'PROD002';

INSERT INTO cdm_activity_cost_drivers (tenant_id, product_id, setup_mins, overtime_rate_usd_per_hr, expedite_cost_per_unit, overhead_pct)
SELECT 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', p.id, 25, 95.00, 1.25, 0.15
FROM cdm_product p
WHERE p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND p.erp_source_id = 'PROD004';

-- V6-R2: Material attributes (Region_X, HS-8471), landed cost profiles, substitute mapping
DELETE FROM cdm_material_attributes
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

DELETE FROM cdm_landed_cost_profiles
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

INSERT INTO cdm_material_attributes (tenant_id, material_id, attributes)
SELECT 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', p.id,
  '{"origin_region": "Region_X", "tariff_code": "HS-8471", "carbon_intensity_kg": 12.4}'::jsonb
FROM cdm_product p
WHERE p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND p.erp_source_id = 'PROD003';

INSERT INTO cdm_material_attributes (tenant_id, material_id, attributes)
SELECT 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', p.id,
  '{"origin_region": "Region_X", "tariff_code": "HS-8471", "carbon_intensity_kg": 8.2, "substitute_for": "PROD003"}'::jsonb
FROM cdm_product p
WHERE p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND p.erp_source_id = 'PROD005';

INSERT INTO cdm_landed_cost_profiles (tenant_id, region, base_cost_usd, freight_usd, tariff_pct, risk_premium_pct)
VALUES
  ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'Region_X', 10.00, 1.50, 20.0, 7.5);

UPDATE cdm_tenant
SET config = COALESCE(config, '{}'::jsonb) || jsonb_build_object(
  'substitute_materials',
  jsonb_build_object(
    (SELECT id::text FROM cdm_product WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'PROD003'),
    (SELECT id::text FROM cdm_product WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'PROD005')
  )
)
WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
