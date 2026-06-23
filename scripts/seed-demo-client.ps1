# Load client demo data (MOs, scenarios, delays, BOMs, routing)
# Usage: .\scripts\seed-demo-client.ps1
# Requires: docker-db-1 running + base seed (seed-data.ps1)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$SqlFile = Join-Path $Root "scripts\seed-demo-client.sql"
$Container = "docker-db-1"

Write-Host "=== Loading client demo data ===" -ForegroundColor Cyan

$running = docker ps --filter "name=$Container" --filter "status=running" -q 2>$null
if (-not $running) {
    Write-Host "Postgres container '$Container' is not running." -ForegroundColor Red
    exit 1
}

Get-Content $SqlFile -Raw | docker exec -i $Container psql -U ipe -d ipe_test -v ON_ERROR_STOP=1 2>&1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Client demo data loaded." -ForegroundColor Green
Write-Host "  - 10 MOs with feasibility scores (Control Tower queue)" -ForegroundColor DarkGray
Write-Host "  - 8 resolution scenarios (Resolution Center)" -ForegroundColor DarkGray
Write-Host "  - 8 delay events (Executive / War Room)" -ForegroundColor DarkGray
Write-Host "  - BOMs + routing (Schedule Gantt)" -ForegroundColor DarkGray
