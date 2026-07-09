# Gate 11 — R1 integration demo via K8s ingress (T166)
param(
    [string]$BaseUrl = "http://localhost/api/v1",
    [string]$ReportPath = "specs/015-enterprise-production-readiness/evidence/gate11-r1-k8s.txt"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$demoScript = Join-Path $Root "scripts\run-release1-integration-demo.ps1"
$reportFull = Join-Path $Root $ReportPath
New-Item -ItemType Directory -Force -Path (Split-Path $reportFull) | Out-Null

$lines = @("=== Gate 11 R1 on K8s ===", (Get-Date -Format o), "BaseUrl: $BaseUrl", "")
& $demoScript -BaseUrl $BaseUrl -ReportPath $ReportPath 2>&1 | ForEach-Object {
    $lines += $_
    Write-Host $_
}

$pass = ([regex]::Matches(($lines -join "`n"), '\[PASS\]')).Count
$fail = ([regex]::Matches(($lines -join "`n"), '\[FAIL\]')).Count
$lines += ""
$lines += "Summary: PASS=$pass FAIL=$fail"
Set-Content -Path $reportFull -Value ($lines -join "`n")

if ($fail -gt 0) { exit 1 }
exit 0
