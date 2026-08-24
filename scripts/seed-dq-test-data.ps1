# Seed a tiny DQ-imperfect tenant overlay (does not auto-fix).
# Usage: .\scripts\seed-dq-test-data.ps1
Write-Host "DQ test data: insert one nameless ingest product under Star Trans tenant if table exists."
$sql = @"
SELECT set_config('app.current_tenant_id', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', false);
INSERT INTO cdm_ingest_product (tenant_id, product_id, name)
VALUES ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'DQ-BAD-001', NULL)
ON CONFLICT (tenant_id, product_id) DO NOTHING;
"@
$sql | docker compose -f "$PSScriptRoot\..\infrastructure\docker\docker-compose.release2.yml" exec -T db psql -U ipe -d ipe_test
Write-Host "Done. Run DQ engine to see products.missing_name."
