# Load demo seed data via Docker Postgres (Windows — no bash required)
# Usage: .\scripts\seed-data.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$SeedSh = Join-Path $Root "scripts\seed-data.sh"
$Container = "docker-db-1"

Write-Host "=== Loading seed data (via Docker) ===" -ForegroundColor Cyan

$running = docker ps --filter "name=$Container" --filter "status=running" -q 2>$null
if (-not $running) {
    Write-Host "Postgres container '$Container' is not running. Start stack first:" -ForegroundColor Red
    Write-Host "  cd infrastructure\docker; docker compose up -d db" -ForegroundColor Yellow
    exit 1
}

$content = Get-Content $SeedSh -Raw
if ($content -notmatch "(?s)<<'SQL'\r?\n(.*)\r?\nSQL") {
    throw "Could not extract SQL from seed-data.sh"
}

$sql = "CREATE EXTENSION IF NOT EXISTS pgcrypto;`n" + $Matches[1]
$prevEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$sql | docker exec -i $Container psql -U ipe -d ipe_test -v ON_ERROR_STOP=1 2>&1 | ForEach-Object { Write-Host $_ }
$ErrorActionPreference = $prevEap
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Seed data loaded successfully." -ForegroundColor Green
