# Load Star Trans demo branding (base demo graph + industry overlay)
# Usage: .\scripts\seed-startrans-demo.ps1
# Requires: docker-db-1 running, migrations applied, base seed loaded

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$OverlaySql = Join-Path $Root "scripts\seed-startrans-overlay.sql"
$Mos20Sql = Join-Path $Root "scripts\seed-startrans-20-mos.sql"
$MdrBoostSql = Join-Path $Root "scripts\seed-startrans-mdr-boost.sql"
$Container = "docker-db-1"
$DbName = "ipe_test"
$DbUser = "ipe"

function Test-IpeSchema {
    $sql = "SELECT to_regclass('public.cdm_tenant') IS NOT NULL AS ok;"
    $out = $sql | docker exec -i $Container psql -U $DbUser -d $DbName -t -A 2>&1
    if ($LASTEXITCODE -ne 0) { return $false }
    return ($out.Trim() -eq "t")
}

Write-Host "=== Star Trans Demo Data ===" -ForegroundColor Cyan

$running = docker ps --filter "name=$Container" --filter "status=running" -q 2>$null
if (-not $running) {
    Write-Host "Postgres container '$Container' is not running." -ForegroundColor Red
    Write-Host "Start: cd infrastructure\docker; docker compose up -d db dpe-svc" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-IpeSchema)) {
    Write-Host "IPE schema not found in ${DbName} (cdm_tenant missing)." -ForegroundColor Red
    Write-Host ""
    Write-Host "This script must run against the Docker demo database, not an empty IDE SQL connection." -ForegroundColor Yellow
    Write-Host "Bootstrap order:" -ForegroundColor Yellow
    Write-Host "  1. cd infrastructure\docker; docker compose up -d db dpe-svc   # applies migrations" -ForegroundColor DarkGray
    Write-Host "  2. .\scripts\seed-data.ps1" -ForegroundColor DarkGray
    Write-Host "  3. .\scripts\seed-demo-client.ps1" -ForegroundColor DarkGray
    Write-Host "  4. .\scripts\seed-startrans-demo.ps1" -ForegroundColor DarkGray
    exit 1
}

$moCheck = "SELECT COUNT(*) FROM cdm_manufacturing_order WHERE tenant_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' AND erp_mo_id LIKE 'MO-ST-%';"
$moCount = ($moCheck | docker exec -i $Container psql -U $DbUser -d $DbName -t -A 2>&1).Trim()

if ([int]$moCount -ge 10) {
    Write-Host "[1/3] Demo MO graph already loaded ($moCount MO-ST rows) - skipping seed-demo-client.ps1" -ForegroundColor DarkGray
} else {
    Write-Host "[1/3] Loading base client demo graph..." -ForegroundColor Yellow
    & (Join-Path $Root "scripts\seed-demo-client.ps1")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "[2/4] Applying Star Trans industry overlay..." -ForegroundColor Yellow
Get-Content $OverlaySql -Raw | docker exec -i $Container psql -U $DbUser -d $DbName -v ON_ERROR_STOP=1 2>&1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3/4] Seeding 20 MOs with feasibility bands..." -ForegroundColor Yellow
Get-Content $Mos20Sql -Raw | docker exec -i $Container psql -U $DbUser -d $DbName -v ON_ERROR_STOP=1 2>&1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[4/4] Applying MDR boost (BOMs, routing, inventory for schedule gate)..." -ForegroundColor Yellow
Get-Content $MdrBoostSql -Raw | docker exec -i $Container psql -U $DbUser -d $DbName -v ON_ERROR_STOP=1 2>&1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Star Trans demo data ready (20 MOs)." -ForegroundColor Green
Write-Host "  Tenant: Star Trans - Electrical Transformer Technology" -ForegroundColor DarkGray
Write-Host "  MOs: MO-ST-001 through MO-ST-010 (10 orders, 3 at-risk)" -ForegroundColor DarkGray
Write-Host "  Hero MO: MO-ST-001 - copper winding delay (score ~52)" -ForegroundColor DarkGray
Write-Host "  Validate: .\scripts\run-full-demo.ps1 -Profile startrans" -ForegroundColor DarkGray
