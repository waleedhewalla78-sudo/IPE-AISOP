# Star Trans Demo — One-shot preparation
# Usage: .\scripts\prepare-startrans-demo.ps1

param([switch]$SkipValidation)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$DockerDir = Join-Path $Root "infrastructure\docker"

Write-Host "=== Star Trans Demo Preparation ===" -ForegroundColor Cyan

Push-Location $DockerDir
try {
    docker compose up -d db redis kong dpe-svc nlp-svc demand-svc scenario-svc supply-svc order-svc equipment-svc material-svc procurement-svc sustain-svc quality-svc 2>&1 | Out-Null
    docker compose up -d --force-recreate kong 2>&1 | Out-Null
} finally {
    Pop-Location
}

Start-Sleep -Seconds 15

& (Join-Path $Root "scripts\seed-startrans-demo.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& (Join-Path $Root "scripts\convert-project-plan-to-xlsx.ps1")
# xlsx optional - csv manual fallback documented

if (-not $SkipValidation) {
    & (Join-Path $Root "scripts\run-full-demo.ps1") `
        -Profile startrans `
        -ReportPath (Join-Path $Root "docs\demo-data\startrans-pre-demo.txt")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host ""
Write-Host "Star Trans demo ready." -ForegroundColor Green
Write-Host "  UI:     http://localhost:8082/login  (run: cd apps\web && npm run dev)" -ForegroundColor Cyan
Write-Host "  Login:  Ahmed@nour / admin" -ForegroundColor Cyan
Write-Host "  Spec:   docs\demo-data\STARTRANS-CSV-UPLOAD-SPEC.md" -ForegroundColor Cyan
Write-Host "  Guide:  docs\demo-data\STARTRANS-DEMO-GUIDE.md" -ForegroundColor Cyan
