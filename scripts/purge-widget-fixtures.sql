-- STREAM-1.2: Purge legacy Widget/Gadget product names from live demo DB.
-- Safe to re-run. Prefer Star Trans catalog names.

SELECT set_config('app.current_tenant_id', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', false);

UPDATE cdm_product SET name = 'Distribution Transformer 500 kVA', internal_ref = COALESCE(NULLIF(internal_ref, ''), 'ST-DT-500')
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND (erp_source_id = 'PROD001' OR name ILIKE '%widget%');

UPDATE cdm_product SET name = 'Pad-Mount Transformer 250 kVA', internal_ref = COALESCE(NULLIF(internal_ref, ''), 'ST-PM-250')
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND (erp_source_id = 'PROD002' OR name ILIKE '%gadget%');

UPDATE cdm_routing_operation SET operation_name = 'Wind LV/HV Coils'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND operation_name ILIKE '%widget%housing%';

UPDATE cdm_routing_operation SET operation_name = 'Core & Coil Assembly'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND operation_name ILIKE '%assemble widget%';

UPDATE cdm_routing_operation SET operation_name = 'Tank Fit-Up & Vacuum Test'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND operation_name ILIKE '%pack widget%';

UPDATE cdm_routing_operation SET operation_name = 'Wind Pad-Mount Coils'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND operation_name ILIKE '%fabricate gadget%';

UPDATE cdm_routing_operation SET operation_name = 'Pad-Mount Final Test'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
  AND operation_name ILIKE '%qc gadget%';

-- Report residual hits (should be empty)
SELECT 'product' AS kind, id::text, name AS label FROM cdm_product
WHERE name ILIKE '%widget%' OR name ILIKE '%gadget%'
UNION ALL
SELECT 'routing', id::text, operation_name FROM cdm_routing_operation
WHERE operation_name ILIKE '%widget%' OR operation_name ILIKE '%gadget%';
