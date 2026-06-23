# R4 production hardening verification orchestrator
$ErrorActionPreference = "Continue"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

Write-Host "=== R4 Production Hardening Verification ==="
Write-Host ""

$steps = @(
    @{ Name = "SAP sandbox (mapper + optional live)"; Script = ".\scripts\test-sap-sandbox.ps1" },
    @{ Name = "D365 sandbox (mapper + optional live)"; Script = ".\scripts\test-d365-sandbox.ps1" },
    @{ Name = "Airflow compose health"; Script = ".\scripts\verify-airflow.ps1" }
)

$pass = 0
foreach ($step in $steps) {
    Write-Host "--- $($step.Name) ---"
    & $step.Script
    if ($LASTEXITCODE -eq 0) { $pass++ }
    Write-Host ""
}

Write-Host "Optional (requires k6 + running stack): .\scripts\run-k6-200vu.ps1"
Write-Host "Optional (requires kubectl + staging): .\infrastructure\chaos\run-chaos.ps1"
Write-Host ""
Write-Host "R4 automated checks: $pass / $($steps.Count) passed"
exit $(if ($pass -eq $steps.Count) { 0 } else { 1 })
