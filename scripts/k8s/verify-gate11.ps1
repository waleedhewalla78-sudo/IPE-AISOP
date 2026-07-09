# Gate 11 — R1 integration demo on K8s ingress (Spec 015 Phase 3)
param(
    [string]$BaseUrl = "http://localhost",
    [string]$EvidencePath = "specs/015-enterprise-production-readiness/evidence/gate11-r1-k8s.txt"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $Root

$report = "docs\demo-data\gate11-k8s-demo.txt"
$lines = @("=== Gate 11 R1 on K8s ===", (Get-Date -Format o), "BaseUrl: $BaseUrl", "")

& (Join-Path $Root "scripts\run-release1-integration-demo.ps1") `
    -BaseUrl $BaseUrl `
    -ReportPath $report 2>&1 | Tee-Object -Variable demoOut

$lines += $demoOut
$reportFull = Join-Path $Root $report
if (Test-Path $reportFull) { $lines += "", "--- Report file ---", (Get-Content $reportFull -Raw) }

$pass = ($demoOut -match "\[PASS\]") -and ($demoOut -notmatch "\[FAIL\]")
$summary = if ($pass) { "RESULT: PASS" } else { "RESULT: PARTIAL/FAIL - review steps above" }
$lines += "", $summary

$dir = Split-Path $EvidencePath -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$lines | Out-File -FilePath $EvidencePath -Encoding utf8
Write-Host $summary
if (-not $pass) { exit 1 }
