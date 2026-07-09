# Gate 11 — R1 demo on K8s ingress (T166)
# Usage: .\scripts\k8s\verify-gate11-r1-k8s.ps1

param(
    [string]$BaseUrl = "http://localhost/api/v1"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$EvidenceDir = Join-Path $Root "specs\015-enterprise-production-readiness\evidence"
$EvidenceFile = Join-Path $EvidenceDir "gate11-r1-k8s.txt"

if (-not (Test-Path $EvidenceDir)) {
    New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
}

Write-Host "=== Gate 11: R1 demo on K8s ($BaseUrl) ===" -ForegroundColor Cyan

$demoScript = Join-Path $Root "scripts\run-release1-integration-demo.ps1"
$reportRel = "specs\015-enterprise-production-readiness\evidence\gate11-r1-demo-report.txt"

& $demoScript -BaseUrl $BaseUrl -ReportPath $reportRel
$exitCode = $LASTEXITCODE

$reportFull = Join-Path $Root $reportRel
if (Test-Path $reportFull) {
    Copy-Item $reportFull $EvidenceFile -Force
} else {
    @("Gate 11 run exit=$exitCode", "Report not found: $reportFull") | Set-Content $EvidenceFile
}

Write-Host "Evidence: $EvidenceFile" -ForegroundColor Green
exit $exitCode
