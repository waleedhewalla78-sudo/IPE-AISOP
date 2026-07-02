#Requires -Version 5.1
<#
.SYNOPSIS
  Deploy IPE Release 1 stack (Odoo + Star Trans profile).
#>
param(
    [ValidateSet("staging", "production")]
    [string]$Environment = "staging"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$ComposeFile = Join-Path $Root "infrastructure\docker\docker-compose.release1.yml"

Write-Host "=== IPE Release 1 deploy ($Environment) ===" -ForegroundColor Cyan
Set-Location (Join-Path $Root "infrastructure\docker")

docker compose -f docker-compose.release1.yml pull 2>$null
docker compose -f docker-compose.release1.yml up -d --build

Write-Host "Waiting for Kong..." -ForegroundColor Yellow
$deadline = (Get-Date).AddMinutes(5)
do {
    Start-Sleep -Seconds 3
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -eq 200) { break }
    } catch { }
} while ((Get-Date) -lt $deadline)

Write-Host "Release 1 stack up. Web UI: cd apps\web; `$env:VITE_RELEASE_PROFILE='release1'; npm run dev" -ForegroundColor Green
