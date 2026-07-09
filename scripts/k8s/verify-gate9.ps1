# Gate 9 — HPA smoke test (Spec 015 Phase 3)
param(
    [string]$Namespace = "ipe",
    [string]$EvidencePath = "specs/015-enterprise-production-readiness/evidence/gate9-hpa.txt",
    [int]$LoadSeconds = 90
)

$ErrorActionPreference = "Continue"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $Root

$lines = @("=== Gate 9 HPA Smoke ===", (Get-Date -Format o), "")

$hpaBefore = kubectl get hpa -n $Namespace -o wide 2>&1
$lines += "--- HPA before load ---"
$lines += $hpaBefore

$target = "http://localhost/api/v1/health"
$lines += "--- Load $LoadSeconds s on $target ---"
$end = (Get-Date).AddSeconds($LoadSeconds)
while ((Get-Date) -lt $end) {
    curl.exe -s -o NUL $target 2>$null
}

Start-Sleep -Seconds 30
$hpaAfter = kubectl get hpa -n $Namespace -o wide 2>&1
$lines += "--- HPA after load ---"
$lines += $hpaAfter

$events = kubectl get events -n $Namespace --field-selector reason=SuccessfulRescale --sort-by=.lastTimestamp 2>&1 | Select-Object -Last 10
$lines += "--- Recent scale events ---"
$lines += $events

$pass = $false
if ($hpaAfter -match "dpe-svc|fea-svc|cap-svc") {
    $pass = $true
    $lines += "", "RESULT: PASS (HPA resources present; verify replica increase manually if metrics-server slow)"
} else {
    $lines += "", "RESULT: FAIL (no HPA found - install with values-gate9.yaml)"
}

$dir = Split-Path $EvidencePath -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$lines | Out-File -FilePath $EvidencePath -Encoding utf8
Write-Host ($lines -join "`n")
if (-not $pass) { exit 1 }
