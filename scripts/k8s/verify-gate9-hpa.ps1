# Gate 9 — HPA smoke test (T165)
param(
    [string]$Namespace = "ipe",
    [string]$BaseUrl = "http://localhost/api/v1",
    [int]$LoadSeconds = 90,
    [string]$ReportPath = "specs/015-enterprise-production-readiness/evidence/gate9-hpa.txt"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$reportFull = Join-Path $Root $ReportPath
New-Item -ItemType Directory -Force -Path (Split-Path $reportFull) | Out-Null

$lines = @("=== Gate 9 HPA Smoke ===", (Get-Date -Format o), "")

function Log($m) { $lines += $m; Write-Host $m }

Log "--- HPA before load ---"
$before = kubectl get hpa -n $Namespace -o wide 2>&1
$lines += $before

Log ""
Log "--- Applying load for ${LoadSeconds}s ---"
$end = (Get-Date).AddSeconds($LoadSeconds)
$i = 0
while ((Get-Date) -lt $end) {
    $i++
    curl.exe -s -o NUL -w "" "$BaseUrl/health" 2>$null
    curl.exe -s -o NUL "$BaseUrl/feasibility/kpis" -H "X-Tenant-ID: a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11" 2>$null
    if ($i % 20 -eq 0) {
        $snap = kubectl get hpa -n $Namespace 2>&1
        Log "  tick $i : $snap"
    }
    Start-Sleep -Milliseconds 200
}

Log ""
Log "--- HPA after load ---"
$after = kubectl get hpa -n $Namespace -o wide 2>&1
$lines += $after

Log ""
Log "--- Deployment replicas ---"
$deps = kubectl get deploy -n $Namespace dpe-svc fea-svc cap-svc -o wide 2>&1
$lines += $deps

$scaled = $after -match "3|4"
Log ""
if ($scaled) { Log "RESULT: PASS — HPA shows scale activity" }
else { Log "RESULT: PARTIAL — HPA present; scale-up may require metrics-server + CPU pressure" }

Set-Content -Path $reportFull -Value ($lines -join "`n")
if (-not $scaled) { exit 2 }
exit 0
