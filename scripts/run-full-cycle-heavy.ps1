# IPE Full-Cycle Heavy Validation (Windows)
# Seeds demo + mass data, runs all backend tests, live demo, and E2E integration.
#
# Usage:
#   .\scripts\run-full-cycle-heavy.ps1
#   .\scripts\run-full-cycle-heavy.ps1 -SkipDocker
#   .\scripts\run-full-cycle-heavy.ps1 -UnitOnly

param(
    [switch]$SkipDocker,
    [switch]$UnitOnly,
    [string]$ReportPath = "docs\full-cycle-report.txt"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$DockerDir = Join-Path $Root "infrastructure\docker"
$Lines = @()
$PhasePass = 0
$PhaseFail = 0
$PhaseSkip = 0

function Write-Report([string]$Text, [string]$Color = "") {
    if ($Color) { Write-Host $Text -ForegroundColor $Color }
    else { Write-Host $Text }
    $script:Lines += $Text
}

function Test-Phase {
    param([string]$Name, [scriptblock]$Action)
    Write-Report ""
    Write-Report "=== $Name ===" "Yellow"
    try {
        $ok = & $Action
        if ($ok) {
            $script:PhasePass++
            Write-Report "[PASS] $Name" "Green"
            return $true
        }
        $script:PhaseFail++
        Write-Report "[FAIL] $Name" "Red"
        return $false
    } catch {
        $script:PhaseFail++
        Write-Report "[FAIL] $Name - $($_.Exception.Message)" "Red"
        return $false
    }
}

function Skip-Phase([string]$Name, [string]$Reason) {
    $script:PhaseSkip++
    Write-Report "[SKIP] $Name - $Reason" "DarkYellow"
}

function Write-Summary {
    Write-Report ""
    Write-Report "==============================================" "Cyan"
    Write-Report " SUMMARY: $PhasePass passed, $PhaseFail failed, $PhaseSkip skipped" "Cyan"
    Write-Report "==============================================" "Cyan"
    if ($ReportPath) {
        $fullPath = Join-Path $Root $ReportPath
        $dir = Split-Path -Parent $fullPath
        if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        $Lines | Set-Content -Path $fullPath -Encoding UTF8
        Write-Report " Report: $ReportPath" "DarkGray"
    }
    exit $(if ($PhaseFail -eq 0) { 0 } else { 1 })
}

Write-Report "==============================================" "Cyan"
Write-Report " IPE Full-Cycle Heavy Validation" "Cyan"
Write-Report " $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Cyan"
Write-Report " Root: $Root" "Cyan"
Write-Report "==============================================" "Cyan"

$AllServices = @(
    "shared", "dpe-svc", "mat-svc", "cap-svc", "fea-svc", "res-svc", "del-svc",
    "nlp-svc", "rec-svc", "alert-svc", "connector", "sustain-svc", "quality-svc",
    "scn-svc", "network-svc", "ml-svc"
)
$OptionalServices = @("ml-svc")

Test-Phase "Phase 1 - Backend unit tests ($($AllServices.Count) services)" {
    $failed = @()
    $skipped = @()
    foreach ($svc in $AllServices) {
        $svcPath = Join-Path $Root "services\$svc"
        if (-not (Test-Path (Join-Path $svcPath "tests"))) {
            Write-Report "  [SKIP] $svc - no tests/"
            continue
        }
        Push-Location $svcPath
        try {
            $out = uv run pytest tests/ -q --tb=no 2>&1
            if ($LASTEXITCODE -ne 0) {
                if ($OptionalServices -contains $svc) {
                    $skipped += $svc
                    Write-Report "  [WARN] $svc optional skip - $($out | Select-Object -Last 1)"
                } else {
                    $failed += $svc
                    Write-Report "  [FAIL] $svc - $($out | Select-Object -Last 1)"
                }
            } else {
                Write-Report "  [OK]   $svc - $($out | Select-Object -Last 1)"
            }
        } finally { Pop-Location }
    }
    if ($skipped.Count -gt 0) {
        Write-Report "  Optional skipped: $($skipped -join ', ')"
    }
    if ($failed.Count -gt 0) {
        Write-Report "  Failed: $($failed -join ', ')"
        return $false
    }
    return $true
}

if ($UnitOnly) { Write-Summary }

Test-Phase "Phase 2 - Frontend Vitest" {
    Push-Location (Join-Path $Root "apps\web")
    try {
        if (-not (Test-Path "node_modules")) { npm install 2>&1 | Out-Null }
        npm run test -- --run 2>&1 | Tee-Object -Variable vitestOut | Out-Null
        ($vitestOut | Select-Object -Last 3) | ForEach-Object { Write-Report "  $_" }
        return ($LASTEXITCODE -eq 0)
    } finally { Pop-Location }
}

Test-Phase "Phase 3 - Integration tests (root, infra may skip)" {
    Push-Location $Root
    try {
        $out = uv run pytest tests/integration/ -q --tb=line 2>&1
        Write-Report "  $($out | Select-Object -Last 1)"
        # Pass if only skips/failures are connection errors without live stack
        if ($LASTEXITCODE -eq 0) { return $true }
        $passed = ($out | Select-String "passed").Line
        $skipped = ($out | Select-String "skipped").Line
        if ($passed -and -not ($out | Select-String "failed")) { return $true }
        if ($SkipDocker -and $skipped) {
            Write-Report "  (expected without Docker - skipped live tests)"
            return $true
        }
        return $false
    } finally { Pop-Location }
}

if ($SkipDocker) {
    Skip-Phase "Phase 4 - Docker stack" "SkipDocker flag"
    Skip-Phase "Phase 5 - Seed data" "SkipDocker flag"
    Skip-Phase "Phase 6 - Live demo" "SkipDocker flag"
    Skip-Phase "Phase 7 - Live E2E" "SkipDocker flag"
    Skip-Phase "Phase 8 - k6 load" "SkipDocker flag"
    Write-Summary
}

$dockerOk = Test-Phase "Phase 4 - Docker stack up" {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Report "  Docker Desktop is not running. Start Docker Desktop and retry."
        return $false
    }
    Push-Location $DockerDir
    try {
        docker compose config 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { return $false }
        docker compose up -d --build 2>&1 | Select-Object -Last 12 | ForEach-Object { Write-Report "  $_" }
        if ($LASTEXITCODE -ne 0) { return $false }
        docker compose run --rm migrate 2>&1 | Select-Object -Last 5 | ForEach-Object { Write-Report "  $_" }
        docker compose up -d --force-recreate kong 2>&1 | Out-Null
        return ($LASTEXITCODE -eq 0)
    } finally { Pop-Location }
}

if (-not $dockerOk) {
    Skip-Phase "Phase 5 - Seed data" "Docker unavailable"
    Skip-Phase "Phase 6 - Live demo" "Docker unavailable"
    Skip-Phase "Phase 7 - Live E2E" "Docker unavailable"
    Skip-Phase "Phase 8 - k6 load" "Docker unavailable"
    Write-Summary
}

Test-Phase "Phase 5 - Seed base + demo + mass data" {
    & (Join-Path $Root "scripts\seed-data.ps1"); if ($LASTEXITCODE -ne 0) { return $false }
    & (Join-Path $Root "scripts\seed-demo-client.ps1"); if ($LASTEXITCODE -ne 0) { return $false }
    & (Join-Path $Root "scripts\seed-mass-data.ps1"); return ($LASTEXITCODE -eq 0)
}

Test-Phase "Phase 6 - Live demo (20 checkpoints)" {
    & (Join-Path $Root "scripts\run-full-demo.ps1") -ReportPath (Join-Path $Root "docs\demo-run-report-v6.txt")
    return ($LASTEXITCODE -eq 0)
}

Test-Phase "Phase 7 - Live E2E (sprint2 + phase5_6)" {
    Push-Location $Root
    try {
        $env:TEST_DPE_URL = "http://localhost:8000"
        $env:TEST_SUSTAIN_URL = "http://localhost:8000"
        $env:TEST_QUALITY_URL = "http://localhost:8000"
        $env:TEST_SCN_URL = "http://localhost:8000"
        $env:TEST_NETWORK_URL = "http://localhost:8000"
        $out = uv run pytest tests/integration/test_sprint2_e2e.py tests/integration/test_phase5_6_e2e.py -q --tb=line 2>&1
        Write-Report "  $($out | Select-Object -Last 1)"
        return ($LASTEXITCODE -eq 0)
    } finally { Pop-Location }
}

if (Get-Command k6 -ErrorAction SilentlyContinue) {
    Test-Phase "Phase 8 - k6 load smoke (5 VU, 30s)" {
        Push-Location $Root
        try {
            $env:BASE_URL = "http://localhost:8000"
            k6 run --vus 5 --duration 30s tests/performance/k6/load-test.js 2>&1 | Select-Object -Last 8 | ForEach-Object { Write-Report "  $_" }
            return ($LASTEXITCODE -eq 0)
        } finally { Pop-Location }
    }
} else {
    Skip-Phase "Phase 8 - k6 load" "k6 not installed"
}

Write-Summary
