-- Star Trans industry overlay — run AFTER seed-demo-client.sql
-- Tenant: same UUID as demo (preserves 32/32 checkpoint graph)
--
-- DO NOT run this file in Cursor/IDE SQL against an empty database.
-- Target: PostgreSQL database "ipe_test" inside container docker-db-1 (port 5433).
--
-- Correct (PowerShell from repo root):
--   .\scripts\seed-startrans-demo.ps1
--
-- Manual:
--   Get-Content scripts\seed-startrans-overlay.sql -Raw |
--     docker exec -i docker-db-1 psql -U ipe -d ipe_test -v ON_ERROR_STOP=1

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'cdm_tenant'
  ) THEN
    RAISE EXCEPTION E'IPE schema missing (cdm_tenant not found).\n'
      'You are likely connected to the wrong database or migrations were never applied.\n'
      'Fix: cd infrastructure\\docker && docker compose up -d db dpe-svc\n'
      '     .\\scripts\\seed-data.ps1 && .\\scripts\\seed-demo-client.ps1\n'
      '     .\\scripts\\seed-startrans-demo.ps1';
  END IF;
END $$;

SELECT set_config('app.current_tenant_id', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', false);

-- Tenant branding
UPDATE cdm_tenant
SET name = 'Star Trans - Electrical Transformer Technology'
WHERE id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

-- Products (keep erp_source_id PROD001–005 for FK stability)
UPDATE cdm_product SET name = 'Distribution Transformer 500 kVA', internal_ref = 'ST-DT-500'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'PROD001';

UPDATE cdm_product SET name = 'Pad-Mount Transformer 250 kVA', internal_ref = 'ST-PM-250'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'PROD002';

UPDATE cdm_product SET name = 'Copper Winding Wire', internal_ref = 'ST-CU-WIRE'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'PROD003';

UPDATE cdm_product SET name = 'Power Transformer 50 MVA Core-Coil', internal_ref = 'ST-PT-50M'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'PROD004';

UPDATE cdm_product SET name = 'CRGO Electrical Steel', internal_ref = 'ST-CRGO'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'PROD005';

-- Customers
UPDATE cdm_customer SET name = 'Great Lakes Utility', tier = 1
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'CUST001';

UPDATE cdm_customer SET name = 'Midwest Grid Co', tier = 2
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'CUST002';

UPDATE cdm_customer SET name = 'Regional Power Authority', tier = 3
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'CUST003';

-- Work centers
UPDATE cdm_work_center SET name = 'Core & Coil Assembly'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'WC001';

UPDATE cdm_work_center SET name = 'Winding Station'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'WC002';

UPDATE cdm_work_center SET name = 'Tank Fabrication & Test Bay'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'WC003';

-- Suppliers
UPDATE cdm_supplier SET name = 'Midwest Copper Supply'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'SUPP001';

UPDATE cdm_supplier SET name = 'CRGO Steel International'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'SUPP002';

UPDATE cdm_supplier SET name = 'Gulf Coast Logistics'
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id = 'SUPP003';

-- Manufacturing order IDs (same UUIDs — 32/32 stable)
UPDATE cdm_manufacturing_order SET erp_mo_id = 'MO-ST-' || LPAD(SUBSTRING(erp_mo_id FROM 9), 3, '0')
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_mo_id LIKE 'MO-DEMO-%';

-- Routing operation names (transformer process)
UPDATE cdm_routing_operation SET operation_name = 'Wind LV/HV Coils'
WHERE id = 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c01';

UPDATE cdm_routing_operation SET operation_name = 'Core & Coil Assembly'
WHERE id = 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c02';

UPDATE cdm_routing_operation SET operation_name = 'Tank Fit-Up & Vacuum Test'
WHERE id = 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c03';

UPDATE cdm_routing_operation SET operation_name = 'Fabricate Pad-Mount Tank'
WHERE id = 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c04';

UPDATE cdm_routing_operation SET operation_name = 'Final Electrical Test (FPY)'
WHERE id = 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c05';

UPDATE cdm_routing_operation SET operation_name = 'Build 50 MVA Core-Coil'
WHERE id = 'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380c06';

-- Resolution scenarios — transformer context
UPDATE cdm_resolution_scenario SET description = 'Expedite copper winding wire PO from Midwest Copper Supply'
WHERE id = 'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380001';

UPDATE cdm_resolution_scenario SET description = 'Substitute alternate gauge copper from approved vendor list'
WHERE id = 'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380002';

UPDATE cdm_resolution_scenario SET description = 'Split MO-ST-001 into two coil batches to reduce copper peak demand'
WHERE id = 'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380003';

UPDATE cdm_resolution_scenario SET description = 'Add Saturday overtime on Winding Station'
WHERE id = 'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380004';

UPDATE cdm_resolution_scenario SET description = 'Route to backup winding cell (Bay 2)'
WHERE id = 'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380005';

UPDATE cdm_resolution_scenario SET description = 'Emergency PO for CRGO electrical steel'
WHERE id = 'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380006';

UPDATE cdm_resolution_scenario SET description = 'Defer MO-ST-007 by 5 days (Great Lakes Utility Tier 1 penalty)'
WHERE id = 'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380007';

UPDATE cdm_resolution_scenario SET description = 'Weekend shift on Core & Coil Assembly'
WHERE id = 'c1eebc99-9c0b-4ef8-bb6d-6bb9bd380008';

-- Delay events
UPDATE cdm_delay_event SET cause_detail = 'Copper winding wire PO delayed 2 days - Midwest Copper Supply'
WHERE id = 'd2eebc99-9c0b-4ef8-bb6d-6bb9bd380001';

UPDATE cdm_delay_event SET cause_detail = 'Winding Station at 96% utilization - utility order surge'
WHERE id = 'd2eebc99-9c0b-4ef8-bb6d-6bb9bd380002';

UPDATE cdm_delay_event SET cause_detail = 'Certified welder absent - core assembly skill gap'
WHERE id = 'd2eebc99-9c0b-4ef8-bb6d-6bb9bd380003';

UPDATE cdm_delay_event SET cause_detail = 'CRGO electrical steel below safety stock - 8-week lead time'
WHERE id = 'd2eebc99-9c0b-4ef8-bb6d-6bb9bd380004';

UPDATE cdm_delay_event SET cause_detail = 'Core assembly changeover overrun - 50 MVA custom spec'
WHERE id = 'd2eebc99-9c0b-4ef8-bb6d-6bb9bd380005';

UPDATE cdm_delay_event SET cause_detail = 'Minor rework on vacuum test - tank seal inspection'
WHERE id = 'd2eebc99-9c0b-4ef8-bb6d-6bb9bd380006';

-- Disruption events
UPDATE cdm_disruption_event SET description = 'Predictive maintenance block on Winding Station (RUL 36h)'
WHERE id = 'f2eebc99-9c0b-4ef8-bb6d-6bb9bd380001';

UPDATE cdm_disruption_event SET description = 'CRGO steel below safety stock - supplier delay on long-lead laminations'
WHERE id = 'f2eebc99-9c0b-4ef8-bb6d-6bb9bd380002';

-- Supply network plants (migration 034)
UPDATE cdm_plant SET name = 'Star Trans Chicago HQ' WHERE code = 'DEMO-HAMBURG';
UPDATE cdm_plant SET name = 'Star Trans Houston Plant' WHERE code = 'DEMO-SHANGHAI';
UPDATE cdm_plant SET name = 'Star Trans Regional DC Dallas' WHERE code = 'DEMO-ROTTERDAM';
UPDATE cdm_plant SET name = 'Star Trans Winding Center Minneapolis' WHERE code = 'DEMO-CHICAGO';

-- Demand line source IDs (cosmetic)
UPDATE cdm_demand_line SET erp_source_id = REPLACE(erp_source_id, 'DEM-DEMO', 'DEM-ST')
WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_source_id LIKE 'DEM-DEMO-%';
