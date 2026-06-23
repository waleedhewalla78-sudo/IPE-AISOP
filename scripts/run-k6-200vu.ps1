# k6 200 VU re-certification (R4 T044 / SC-012)
# Requires: k6 installed, Kong + services running (scripts/start-product.ps1)
param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$ReportPath = "specs/003-autonomous-planning-v5/evidence/r4/k6-200vu-summary.txt"
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$evidenceDir = Split-Path -Parent $ReportPath
if ($evidenceDir -and -not (Test-Path $evidenceDir)) {
    New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null
}

$env:BASE_URL = $BaseUrl
$env:K6_SUMMARY_PATH = $ReportPath

Write-Host "Running k6 200 VU test against $BaseUrl ..."
k6 run tests/performance/k6/load-test-200vu.js
$code = $LASTEXITCODE
if ($code -eq 0) {
    Write-Host "PASS — summary: $ReportPath"
} else {
    Write-Host "FAIL — see k6 output above"
}
exit $code
