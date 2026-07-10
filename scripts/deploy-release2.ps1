#Requires -Version 5.1
<#
.SYNOPSIS
  Deploy IPE Release 2 stack (R1 + nlp-svc, demand-svc, scenario-svc).
#>
param(
    [ValidateSet("staging", "production")]
    [string]$Environment = "staging"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$ComposeFile = Join-Path $Root "infrastructure\docker\docker-compose.release2.yml"

Write-Host "=== IPE Release 2 deploy ($Environment) ===" -ForegroundColor Cyan
Set-Location (Join-Path $Root "infrastructure\docker")

docker compose -f docker-compose.release2.yml pull 2>$null
docker compose -f docker-compose.release2.yml up -d --build

Write-Host "Waiting for Kong..." -ForegroundColor Yellow
$deadline = (Get-Date).AddMinutes(8)
do {
    Start-Sleep -Seconds 3
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -eq 200) { break }
    } catch { }
} while ((Get-Date) -lt $deadline)

Write-Host "Waiting for R2 services (nlp, demand, scenario)..." -ForegroundColor Yellow
$r2Services = @(
    @{ Name = "nlp-svc"; Url = "http://localhost:8007/api/v1/health" },
    @{ Name = "demand-svc"; Url = "http://localhost:8040/api/v1/health" },
    @{ Name = "scenario-svc"; Url = "http://localhost:8050/api/v1/health" }
)
foreach ($svc in $r2Services) {
    $svcDeadline = (Get-Date).AddMinutes(3)
    do {
        Start-Sleep -Seconds 3
        try {
            $r = Invoke-WebRequest -Uri $svc.Url -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) { break }
        } catch { }
    } while ((Get-Date) -lt $svcDeadline)
}

Write-Host "Release 2 stack up. Web UI: http://localhost:8082 (profile=release2)" -ForegroundColor Green
Write-Host "Smoke: .\scripts\release2-smoke.ps1" -ForegroundColor Green
