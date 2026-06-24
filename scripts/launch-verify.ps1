# IPE Launch Verification (Windows)
# Runs backend unit tests across all services and reports pass/fail summary.
# Usage: .\scripts\launch-verify.ps1

param(
    [string]$ReportPath = ""
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Services = @(
    "shared",
    "cap-svc",
    "dpe-svc",
    "fea-svc",
    "connector",
    "nlp-svc",
    "mat-svc",
    "res-svc",
    "del-svc",
    "alert-svc"
)

$Pass = 0
$Fail = 0
$Skip = 0
$Lines = @()

function Write-Line([string]$Text) {
    Write-Host $Text
    $script:Lines += $Text
}

Write-Line "=============================================="
Write-Line " IPE Launch Verification - Backend Tests"
Write-Line " $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Line " Root: $Root"
Write-Line "=============================================="
Write-Line ""

foreach ($svc in $Services) {
    $svcPath = Join-Path $Root "services\$svc"
    $testPath = Join-Path $svcPath "tests"
    if (-not (Test-Path $testPath)) {
        Write-Line "[SKIP] $svc - no tests directory"
        $Skip++
        continue
    }

    Push-Location $svcPath
    try {
        $output = uv run pytest tests/ -q --tb=no 2>&1
        $exitCode = $LASTEXITCODE
        $summary = ($output | Select-Object -Last 1)
        if ($exitCode -eq 0) {
            Write-Line "[PASS] $svc - $summary"
            $Pass++
        } else {
            Write-Line "[FAIL] $svc - $summary"
            $Fail++
            $failLines = $output | Select-String "FAILED"
            foreach ($f in $failLines | Select-Object -First 5) {
                Write-Line "       $f"
            }
        }
    } catch {
        Write-Line "[FAIL] $svc - $($_.Exception.Message)"
        $Fail++
    } finally {
        Pop-Location
    }
}

Write-Line ""
Write-Line "=============================================="
Write-Line " RESULT: $Pass passed, $Fail failed, $Skip skipped of $($Services.Count) services"
Write-Line "=============================================="
Write-Line ""
Write-Line " Next: run-full-demo.ps1 (20 checkpoints)"
Write-Line " Guide: docs\LAUNCH-CHECKLIST.md"

if ($ReportPath) {
    $dir = Split-Path -Parent $ReportPath
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $Lines | Set-Content -Path $ReportPath -Encoding UTF8
    Write-Line " Report saved: $ReportPath"
}

if ($Fail -eq 0) { exit 0 } else { exit 1 }
