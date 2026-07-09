# Gate 8 — Compose vs K8s API parity (Spec 015 Phase 3)
param(
    [string]$ComposeBase = "http://localhost:8000/api/v1",
    [string]$K8sBase = "http://localhost/api/v1",
    [string]$EvidencePath = "specs/015-enterprise-production-readiness/evidence/gate8-parity.txt"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $Root

$env:COMPOSE_BASE = $ComposeBase
$env:K8S_BASE = $K8sBase

$out = @("=== Gate 8 Compose-K8s Parity ===", (Get-Date -Format o), "")
python -m pip install httpx -q 2>$null
$exitCode = 0
try {
    $result = python scripts/k8s/test-compose-k8s-parity.py 2>&1
    $out += $result
    if ($LASTEXITCODE -ne 0) { $exitCode = $LASTEXITCODE }
} catch {
    $out += "ERROR: $_"
    $exitCode = 1
}

$dir = Split-Path $EvidencePath -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$out | Out-File -FilePath $EvidencePath -Encoding utf8
Write-Host ($out -join "`n")
exit $exitCode
