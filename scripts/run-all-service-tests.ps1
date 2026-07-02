# Aggregate backend unit tests per service (avoids pytest import-path collisions).
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Out = Join-Path $Root "docs\qa\full-test-suite-v8.2.0.txt"
$Services = @(
    "shared", "dpe-svc", "cap-svc", "mat-svc", "demand-svc", "scenario-svc",
    "supply-svc", "order-svc", "equipment-svc", "material-svc", "procurement-svc",
    "nlp-svc", "del-svc", "fea-svc", "res-svc", "alert-svc", "quality-svc", "sustain-svc"
)
$Lines = @("=== IPE Full Backend Test Suite v8.2.0 ===", "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')", "")
$TotalPass = 0
$TotalFail = 0
foreach ($svc in $Services) {
    $dir = Join-Path $Root "services\$svc"
    if (-not (Test-Path (Join-Path $dir "tests"))) { continue }
    Write-Host "Testing $svc..." -ForegroundColor Cyan
    Push-Location $dir
    $args = @("run", "pytest", "tests/", "-q", "--tb=no")
    if ($svc -eq "nlp-svc") {
        $args += @("--ignore=tests/test_llm_router.py", "-m", "not integration")
    }
    $result = & uv @args 2>&1 | Out-String
    Pop-Location
    $Lines += "--- $svc ---"
    $Lines += $result.Trim()
    if ($result -match "(\d+) passed") {
        $TotalPass += [int]$Matches[1]
    }
    if ($result -match "(\d+) failed") {
        $TotalFail += [int]$Matches[1]
    }
    $Lines += ""
}
$Lines += "=== Summary: $TotalPass passed, $TotalFail failed ==="
$Lines += "Completed: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$Lines | Set-Content -Path $Out -Encoding UTF8
Write-Host "Wrote $Out ($TotalPass passed, $TotalFail failed)"
if ($TotalFail -gt 0) { exit 1 }
