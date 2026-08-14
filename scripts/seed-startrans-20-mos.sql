-- STREAM-2.6: Star Trans demo seed — 20 MOs with feasibility bands
-- Run after seed-demo-client.sql + seed-startrans-overlay.sql
-- Bands: 3 escalate (<50), 5 action (50-69), 4 review (70-84), 8 good/excellent (85+)

SELECT set_config('app.current_tenant_id', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', false);

UPDATE cdm_product SET name = 'Distribution Transformer 500 kVA' WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'PROD001';
UPDATE cdm_product SET name = 'Pad-Mount Transformer 250 kVA' WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'PROD002';
UPDATE cdm_product SET name = 'Power Transformer 50 MVA Core-Coil' WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'PROD004';

-- Upsert by erp_mo_id: update existing overlay rows, insert missing MO-ST-011..020
WITH src AS (
  SELECT * FROM (VALUES
    -- escalate <50 (3)
    ('MO-ST-001', 'PROD001', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 500, 42.0, 40.0, 50.0, 55.0, 'material_shortage', 'in_progress', 1, 4),
    ('MO-ST-007', 'PROD001', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 600, 45.0, 40.0, 50.0, 55.0, 'material_shortage', 'planned', 2, 6),
    ('MO-ST-011', 'PROD004', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 80, 38.0, 35.0, 45.0, 50.0, 'material_shortage', 'planned', 3, 8),
    -- action 50-69 (5)
    ('MO-ST-002', 'PROD002', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 250, 52.0, 55.0, 48.0, 60.0, 'capacity_overload', 'planned', 2, 6),
    ('MO-ST-008', 'PROD002', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 400, 62.0, 65.0, 58.0, 70.0, 'capacity_overload', 'planned', 2, 7),
    ('MO-ST-012', 'PROD001', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 350, 58.0, 60.0, 52.0, 65.0, 'capacity_overload', 'in_progress', 1, 5),
    ('MO-ST-013', 'PROD002', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 220, 65.0, 68.0, 70.0, 55.0, 'labor_shortage', 'planned', 4, 9),
    ('MO-ST-014', 'PROD004', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 110, 68.0, 70.0, 60.0, 72.0, 'capacity_overload', 'planned', 5, 10),
    -- review 70-84 (4)
    ('MO-ST-003', 'PROD004', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 120, 74.0, 80.0, 78.0, 60.0, 'labor_shortage', 'planned', 3, 8),
    ('MO-ST-004', 'PROD001', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 300, 81.0, 85.0, 82.0, 88.0, NULL, 'confirmed', 5, 9),
    ('MO-ST-015', 'PROD002', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 175, 78.0, 80.0, 82.0, 70.0, 'labor_shortage', 'planned', 2, 6),
    ('MO-ST-016', 'PROD001', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 280, 84.0, 86.0, 84.0, 85.0, NULL, 'confirmed', 1, 5),
    -- good/excellent 85+ (8)
    ('MO-ST-005', 'PROD002', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 180, 88.0, 90.0, 86.0, 90.0, NULL, 'in_progress', 0, 4),
    ('MO-ST-006', 'PROD004', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 90, 91.0, 92.0, 90.0, 93.0, NULL, 'confirmed', 1, 5),
    ('MO-ST-009', 'PROD001', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 200, 95.0, 94.0, 96.0, 95.0, NULL, 'completed', -5, -1),
    ('MO-ST-010', 'PROD002', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 150, 93.0, 91.0, 94.0, 92.0, NULL, 'completed', -4, 0),
    ('MO-ST-017', 'PROD001', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 240, 87.0, 88.0, 86.0, 89.0, NULL, 'confirmed', 1, 4),
    ('MO-ST-018', 'PROD002', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02', 160, 90.0, 91.0, 89.0, 92.0, NULL, 'in_progress', 0, 3),
    ('MO-ST-019', 'PROD004', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03', 70, 96.0, 95.0, 97.0, 96.0, NULL, 'confirmed', -2, 2),
    ('MO-ST-020', 'PROD001', 'e1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01', 190, 98.0, 97.0, 99.0, 98.0, NULL, 'confirmed', -3, 1)
  ) AS t(erp_mo_id, product_code, bom_id, qty, score, mat, cap, labor, constraint_type, status, start_off, end_off)
),
upd AS (
  UPDATE cdm_manufacturing_order mo
  SET quantity = s.qty,
      feasibility_score = s.score,
      material_score = s.mat,
      capacity_score = s.cap,
      labor_score = s.labor,
      primary_constraint = s.constraint_type,
      status = s.status,
      planned_start = NOW() + (s.start_off || ' days')::interval,
      planned_end = NOW() + (s.end_off || ' days')::interval,
      updated_at = NOW()
  FROM src s
  JOIN cdm_product p ON p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND p.erp_source_id = s.product_code
  WHERE mo.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
    AND mo.erp_mo_id = s.erp_mo_id
  RETURNING mo.erp_mo_id
)
INSERT INTO cdm_manufacturing_order (
  tenant_id, erp_mo_id, product_id, bom_id, quantity,
  planned_start, planned_end,
  feasibility_score, material_score, capacity_score, labor_score,
  primary_constraint, status, disruption_status
)
SELECT
  'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
  s.erp_mo_id,
  p.id,
  s.bom_id::uuid,
  s.qty,
  NOW() + (s.start_off || ' days')::interval,
  NOW() + (s.end_off || ' days')::interval,
  s.score, s.mat, s.cap, s.labor,
  s.constraint_type, s.status, 'none'
FROM src s
JOIN cdm_product p ON p.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND p.erp_source_id = s.product_code
WHERE NOT EXISTS (
  SELECT 1 FROM cdm_manufacturing_order mo
  WHERE mo.tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND mo.erp_mo_id = s.erp_mo_id
);

SELECT erp_mo_id, feasibility_score::float AS score, primary_constraint, status
FROM cdm_manufacturing_order
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND erp_mo_id LIKE 'MO-ST-%'
ORDER BY feasibility_score ASC NULLS LAST, erp_mo_id;
