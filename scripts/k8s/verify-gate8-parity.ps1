# Gate 8 — Compose-K8s parity evidence (T164)
param(
    [string]$ReportPath = "specs/015-enterprise-production-readiness/evidence/gate8-parity.txt"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $Root
$reportFull = Join-Path $Root $ReportPath
New-Item -ItemType Directory -Force -Path (Split-Path $reportFull) | Out-Null

$env:COMPOSE_BASE = "http://localhost:8000/api/v1"
$env:K8S_BASE = "http://localhost/api/v1"

$out = python scripts/k8s/test-compose-k8s-parity.py 2>&1
$lines = @("=== Gate 8 Compose-K8s Parity ===", (Get-Date -Format o), "", $out)
Set-Content -Path $reportFull -Value ($lines -join "`n")
Write-Host $out
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
exit 0
