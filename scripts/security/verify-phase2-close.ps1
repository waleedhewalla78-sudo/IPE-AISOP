#Requires -Version 5.1
<#
.SYNOPSIS
  Phase 2 closure verifier — k6 SLO + Gate 5 full E2E bundle.
#>
param(
    [string]$BaseUrlHttps = "https://localhost:8443",
    [string]$KongUrl = "http://localhost:8000",
    [switch]$SkipK6
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$PASS = $true

Write-Host "=== Phase 2 Closure Verification ===" -ForegroundColor Cyan

if (-not $SkipK6) {
    Write-Host "`n--- k6 SLO ---" -ForegroundColor Yellow
    & (Join-Path $Root "scripts\run-k6-slo.ps1") -KongUrl $KongUrl
    if ($LASTEXITCODE -ne 0) { $PASS = $false; Write-Host "  [FAIL] k6 SLO" -ForegroundColor Red }
    else { Write-Host "  [PASS] k6 SLO" -ForegroundColor Green }
}

Write-Host "`n--- Gate 5 Full E2E ---" -ForegroundColor Yellow
& (Join-Path $Root "scripts\security\verify-gate5.ps1") -BaseUrlHttps $BaseUrlHttps
if ($LASTEXITCODE -ne 0) { $PASS = $false; Write-Host "  [FAIL] Gate 5" -ForegroundColor Red }
else { Write-Host "  [PASS] Gate 5" -ForegroundColor Green }

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
if ($PASS) {
    Write-Host "  PHASE 2 CLOSE: PASS" -ForegroundColor Green
    Write-Host "  Ready for tag v9.3.0-p2" -ForegroundColor Green
    exit 0
}
Write-Host "  PHASE 2 CLOSE: FAIL" -ForegroundColor Red
exit 1
