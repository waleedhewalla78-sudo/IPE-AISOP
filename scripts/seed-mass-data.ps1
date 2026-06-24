# Load mass stress-test data (40 MOs, 80 demand lines, chaos snapshots)
# Usage: .\scripts\seed-mass-data.ps1
# Requires: docker-db-1 + base seed + demo seed

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$SqlFile = Join-Path $Root "scripts\seed-mass-data.sql"
$Container = "docker-db-1"

Write-Host "=== Loading mass stress data ===" -ForegroundColor Cyan

$running = docker ps --filter "name=$Container" --filter "status=running" -q 2>$null
if (-not $running) {
    Write-Host "Postgres container '$Container' is not running." -ForegroundColor Red
    exit 1
}

Get-Content $SqlFile -Raw | docker exec -i $Container psql -U ipe -d ipe_test -v ON_ERROR_STOP=1 2>&1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Mass data loaded." -ForegroundColor Green
Write-Host "  - 40 MOs (MO-MASS-001..040)" -ForegroundColor DarkGray
Write-Host "  - 80 demand lines (DEM-MASS-*)" -ForegroundColor DarkGray
Write-Host "  - 7 chaos cost snapshots" -ForegroundColor DarkGray
Write-Host "  - 25 delay events" -ForegroundColor DarkGray
