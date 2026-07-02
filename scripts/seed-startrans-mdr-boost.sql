-- Star Trans MDR boost — raises composite score >= 70% for OR-Tools scheduling gate
-- Run after seed-startrans-overlay.sql (via seed-startrans-demo.ps1 step 3)
-- Idempotent: safe to re-run after Odoo sync (IPE-native BOMs use ST-* erp_source_id)

SELECT set_config('app.current_tenant_id', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', false);

-- Transformer component materials (IPE-native, preserved on Odoo sync)
INSERT INTO cdm_product (id, tenant_id, erp_source_id, name, internal_ref, source_type, lead_time_days)
VALUES
  ('a3eebc99-9c0b-4ef8-bb6d-6bb9bd380001', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'ST-OIL-001', 'Mineral insulating oil', 'OIL-001', 'purchased', 7),
  ('a3eebc99-9c0b-4ef8-bb6d-6bb9bd380002', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'ST-BUS-001', 'Porcelain bushing set', 'BUS-001', 'purchased', 14),
  ('a3eebc99-9c0b-4ef8-bb6d-6bb9bd380003', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'ST-TK-001', 'Steel tank assembly', 'TK-001', 'purchased', 10),
  ('a3eebc99-9c0b-4ef8-bb6d-6bb9bd380004', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'ST-GSK-001', 'Gasket set (tank seal)', 'GSK-001', 'purchased', 5),
  ('a3eebc99-9c0b-4ef8-bb6d-6bb9bd380005', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'ST-RAD-001', 'Cooling radiator bank', 'RAD-001', 'purchased', 21),
  ('a3eebc99-9c0b-4ef8-bb6d-6bb9bd380006', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'ST-OLTC-001', 'OLTC tap-changer mechanism', 'OLTC-001', 'purchased', 28),
  ('a3eebc99-9c0b-4ef8-bb6d-6bb9bd380007', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'ST-AW-001', 'Aluminum winding wire', 'AW-001', 'purchased', 12),
  ('a3eebc99-9c0b-4ef8-bb6d-6bb9bd380008', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'ST-BUCH-001', 'Buchholz relay', 'BUCH-001', 'purchased', 14),
  ('a3eebc99-9c0b-4ef8-bb6d-6bb9bd380009', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'ST-PAD-001', 'Pad-mount enclosure', 'PAD-001', 'purchased', 18)
ON CONFLICT (tenant_id, erp_source_id) DO UPDATE SET
  name = EXCLUDED.name,
  internal_ref = EXCLUDED.internal_ref,
  lead_time_days = EXCLUDED.lead_time_days;

-- Lead times for all products (MDR lead_time_accuracy dimension)
UPDATE cdm_product
SET lead_time_days = COALESCE(lead_time_days, 14)
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

-- BOM for Office Combo (Odoo-synced manufactured product without BOM)
INSERT INTO cdm_bill_of_material (id, tenant_id, product_id, erp_source_id, version, is_active)
SELECT 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a04', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', p.id, 'ST-BOM-OFFICE-COMBO', '1.0', true
FROM cdm_product p
WHERE p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND p.erp_source_id = '52'
ON CONFLICT (id) DO NOTHING;

-- Expanded BOM lines: Distribution Transformer 500 kVA (MO-ST-001, 004, 007, 009)
INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380c01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', comp.id, 850.0, true
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'PROD003'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380c02', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', comp.id, 420.0, true
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'PROD005'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380c03', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', comp.id, 1.0, true
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'ST-TK-001'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380c04', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', comp.id, 6.0, false
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'ST-BUS-001'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380c05', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', comp.id, 480.0, false
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'ST-OIL-001'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380c06', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', comp.id, 2.0, false
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'ST-GSK-001'
ON CONFLICT (id) DO NOTHING;

-- Pad-Mount Transformer 250 kVA (MO-ST-002, 005, 008, 010)
INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380d01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', comp.id, 520.0, true
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'PROD003'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380d02', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', comp.id, 280.0, true
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'PROD005'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380d03', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', comp.id, 1.0, true
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'ST-PAD-001'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380d04', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', comp.id, 4.0, false
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'ST-BUS-001'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380d05', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', comp.id, 320.0, false
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'ST-OIL-001'
ON CONFLICT (id) DO NOTHING;

-- Power Transformer 50 MVA Core-Coil (MO-ST-003, 006 and large power variants)
INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380e01', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', comp.id, 2400.0, true
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'PROD003'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380e02', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', comp.id, 1800.0, true
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'PROD005'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380e03', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', comp.id, 1.0, true
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'ST-TK-001'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380e04', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', comp.id, 4.0, true
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'ST-RAD-001'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380e05', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', comp.id, 12.0, false
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'ST-BUS-001'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380e06', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', comp.id, 1.0, true
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'ST-OLTC-001'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_bom_line (id, tenant_id, bom_id, component_id, quantity_per, is_critical)
SELECT 'f1eebc99-9c0b-4ef8-bb6d-6bb9bd380e07', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', comp.id, 1.0, false
FROM cdm_product comp WHERE comp.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND comp.erp_source_id = 'ST-BUCH-001'
ON CONFLICT (id) DO NOTHING;

-- Additional routing for Assembly D BOM (MO-ST-003, 006)
INSERT INTO cdm_routing_operation (id, tenant_id, bom_id, sequence, work_center_id, operation_name, duration_planned_mins, setup_time_mins)
SELECT 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c07', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 20, wc.id, 'Install Cooling Radiators', 120, 20
FROM cdm_work_center wc WHERE wc.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND wc.erp_source_id = 'WC001'
ON CONFLICT (id) DO NOTHING;

INSERT INTO cdm_routing_operation (id, tenant_id, bom_id, sequence, work_center_id, operation_name, duration_planned_mins, setup_time_mins)
SELECT 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c08', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 30, wc.id, 'Final HV Test & OLTC Commission', 90, 15
FROM cdm_work_center wc WHERE wc.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND wc.erp_source_id = 'WC003'
ON CONFLICT (id) DO NOTHING;

-- Routing for E2E Odoo test BOM (only when that BOM exists from a prior E2E run)
INSERT INTO cdm_routing_operation (id, tenant_id, bom_id, sequence, work_center_id, operation_name, duration_planned_mins, setup_time_mins)
SELECT 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c09', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', b.id, 10, wc.id, 'E2E Assembly', 60, 10
FROM cdm_work_center wc
JOIN cdm_bill_of_material b ON b.id = '0ab541eb-1e68-41e0-a723-72bb24e89e06' AND b.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
WHERE wc.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND wc.erp_source_id = 'WC001'
ON CONFLICT (id) DO NOTHING;

-- Inventory positions for all products missing on-hand data (MDR inventory_accuracy)
INSERT INTO cdm_inventory_position (tenant_id, product_id, qty_on_hand, qty_reserved)
SELECT p.tenant_id, p.id,
  CASE WHEN p.source_type = 'manufactured' THEN 25.0 ELSE 500.0 END,
  CASE WHEN p.erp_source_id IN ('PROD003', 'PROD005') THEN 50.0 ELSE 0.0 END
FROM cdm_product p
WHERE p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND NOT EXISTS (
    SELECT 1 FROM cdm_inventory_position ip
    WHERE ip.tenant_id = p.tenant_id AND ip.product_id = p.id
  );

-- =============================================================================
-- POST-SYNC MDR REMEDIATION — populate ALL dimensions cap-svc / mdr_engine measures
-- Formula: composite = 0.40×BOM + 0.35×routing + 0.25×inventory (gate ≥ 70%)
-- =============================================================================

-- Finished goods used in demo / Odoo sync
UPDATE cdm_product
SET source_type = 'manufactured'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND (
    erp_source_id IN ('PROD001', 'PROD002', 'PROD004', '52')
    OR internal_ref LIKE 'ST-DT%'
    OR internal_ref LIKE 'ST-PM%'
    OR internal_ref LIKE 'ST-PT%'
  );

-- Active BOM for every manufactured product missing one (Odoo sync adds products without BOMs)
INSERT INTO cdm_bill_of_material (id, tenant_id, product_id, erp_source_id, version, is_active)
SELECT
  gen_random_uuid(),
  p.tenant_id,
  p.id,
  'ST-BOM-' || COALESCE(NULLIF(p.internal_ref, ''), p.erp_source_id),
  '1.0',
  true
FROM cdm_product p
WHERE p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND p.source_type = 'manufactured'
  AND NOT EXISTS (
    SELECT 1 FROM cdm_bill_of_material b
    WHERE b.tenant_id = p.tenant_id AND b.product_id = p.id AND b.is_active = true
  );

-- Routing operation for every active BOM that lacks operations
INSERT INTO cdm_routing_operation (
  tenant_id, bom_id, sequence, work_center_id, operation_name, duration_planned_mins, setup_time_mins
)
SELECT
  b.tenant_id,
  b.id,
  10,
  wc.id,
  'Standard Assembly',
  120,
  15
FROM cdm_bill_of_material b
CROSS JOIN LATERAL (
  SELECT id FROM cdm_work_center
  WHERE tenant_id = b.tenant_id AND status = 'operational'
  ORDER BY erp_source_id
  LIMIT 1
) wc
WHERE b.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND b.is_active = true
  AND NOT EXISTS (
    SELECT 1 FROM cdm_routing_operation r
    WHERE r.tenant_id = b.tenant_id AND r.bom_id = b.id
  );

-- Link every MO to an active BOM for its product (required for routing_accuracy_pct)
UPDATE cdm_manufacturing_order mo
SET bom_id = b.id
FROM cdm_bill_of_material b
WHERE mo.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND b.tenant_id = mo.tenant_id
  AND b.product_id = mo.product_id
  AND b.is_active = true
  AND (
    mo.bom_id IS NULL
    OR NOT EXISTS (
      SELECT 1 FROM cdm_routing_operation r
      WHERE r.tenant_id = mo.tenant_id AND r.bom_id = mo.bom_id
    )
  );

-- Ensure all products have inventory positions (inventory_accuracy dimension)
INSERT INTO cdm_inventory_position (tenant_id, product_id, qty_on_hand, qty_reserved)
SELECT
  p.tenant_id,
  p.id,
  CASE WHEN p.source_type = 'manufactured' THEN 25.0 ELSE 500.0 END,
  CASE WHEN p.erp_source_id IN ('PROD003', 'PROD005') THEN 50.0 ELSE 0.0 END
FROM cdm_product p
WHERE p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND NOT EXISTS (
    SELECT 1 FROM cdm_inventory_position ip
    WHERE ip.tenant_id = p.tenant_id AND ip.product_id = p.id
  );

-- Lead time for all products (lead_time_accuracy — not in composite but tracked)
UPDATE cdm_product
SET lead_time_days = COALESCE(lead_time_days, 14)
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
