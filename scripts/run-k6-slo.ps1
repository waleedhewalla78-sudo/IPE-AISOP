#Requires -Version 5.1
<#
.SYNOPSIS
  Phase 2 k6 SLO baseline — P95 < 500ms, error rate < 5%, under Kong 500 req/min.
.PARAMETER KongUrl
  Kong HTTP base (default http://localhost:8000). Use https://localhost:8443 if TLS-only.
#>
param(
    [string]$KongUrl = "http://localhost:8000",
    [string]$KeycloakUrl = "http://localhost:8180",
    [string]$AuthMode = "keycloak",
    [string]$ReportJson = "docs\qa\k6-slo-baseline.json"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command k6 -ErrorAction SilentlyContinue)) {
    Write-Host "k6 not found. Install: winget install k6 --source winget" -ForegroundColor Red
    exit 1
}

$reportDir = Split-Path -Parent $ReportJson
if ($reportDir -and -not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
}

$env:KONG_URL = $KongUrl
$env:KEYCLOAK_URL = $KeycloakUrl
$env:AUTH_MODE = $AuthMode

Write-Host "=== k6 SLO (Phase 2 close) ===" -ForegroundColor Cyan
Write-Host "Kong: $KongUrl | Auth: $AuthMode" -ForegroundColor DarkGray

$prevEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
k6 run scripts/perf/k6-slo.js 2>&1 | ForEach-Object { Write-Host $_ }
$code = $LASTEXITCODE
$ErrorActionPreference = $prevEap

if ($code -eq 0) {
    Write-Host "PASS — k6 SLO thresholds met. Report: $ReportJson" -ForegroundColor Green
} else {
    Write-Host "FAIL — k6 SLO thresholds not met (see output above)" -ForegroundColor Red
}
exit $code
