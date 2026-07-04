#Requires -Version 5.1
<#
.SYNOPSIS
  k6 stress test — validates Kong rate limiter returns 429 under overload.
  Expected: rate_limit_429 > 1% (PASS means rate limiting works).
#>
param(
    [string]$KongUrl = "http://localhost:8000",
    [string]$KeycloakUrl = "http://localhost:8180",
    [string]$AuthMode = "keycloak"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command k6 -ErrorAction SilentlyContinue)) {
    Write-Host "k6 not found. Install: winget install k6 --source winget" -ForegroundColor Red
    exit 1
}

$reportDir = "docs\qa"
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
}

$env:KONG_URL = $KongUrl
$env:KEYCLOAK_URL = $KeycloakUrl
$env:AUTH_MODE = $AuthMode

Write-Host "=== k6 Stress (rate limit validation) ===" -ForegroundColor Cyan
Write-Host "Kong: $KongUrl - expect mass 429 (correct rate-limit behavior)" -ForegroundColor DarkGray

$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
k6 run scripts/perf/k6-stress.js 2>&1 | ForEach-Object { Write-Host $_ }
$code = $LASTEXITCODE
$ErrorActionPreference = $prevEap

if ($code -eq 0) {
    Write-Host "PASS - rate limiter confirmed (429s observed)" -ForegroundColor Green
} else {
    Write-Host 'FAIL/WARN — see output (threshold: rate_limit_429 > 1%)' -ForegroundColor Yellow
}
exit $code
