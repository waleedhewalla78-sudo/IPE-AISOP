# W1-02 - Copilot R1 smoke test (auth + route + API 401)
param(
    [string]$ReportPath = "docs/qa/copilot-r1-smoke.txt"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $Root

$lines = @(
    "=== Copilot R1 Smoke Test (W1-02) ===",
    (Get-Date -Format o),
    ""
)

function Step($name, [scriptblock]$block) {
    Write-Host ">> $name"
    try {
        & $block
        if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) { throw "exit $LASTEXITCODE" }
        $script:lines += "[PASS] $name"
        Write-Host "[PASS] $name" -ForegroundColor Green
    } catch {
        $script:lines += "[FAIL] $name - $($_.Exception.Message)"
        Write-Host "[FAIL] $name - $($_.Exception.Message)" -ForegroundColor Red
        $script:failed = $true
    }
}

$failed = $false

Step "Vitest - copilot panel" {
    Push-Location apps/web
    npm test -- --run tests/features/copilot/CopilotPanel.test.tsx
    Pop-Location
}

Step "Vitest - copilot R1 smoke (auth + route + sidebar)" {
    Push-Location apps/web
    npm test -- --run tests/features/copilot/copilot-r1-smoke.test.tsx
    Pop-Location
}

Step "nlp-svc - copilot 401 unauthenticated" {
    Push-Location services/nlp-svc
    uv run pytest tests/test_api_copilot.py::test_unauthorized_access_returns_401 -q
    Pop-Location
}

Step "Playwright - copilot e2e (release1 profile)" {
    Push-Location apps/web
    $env:VITE_RELEASE_PROFILE = "release1"
    $env:VITE_API_BASE_URL = "http://127.0.0.1:9"
    npx playwright install chromium 2>$null
    npx playwright test e2e/copilot.spec.ts --project=desktop
    Pop-Location
}

$passCount = ($lines | Where-Object { $_ -match '^\[PASS\]' }).Count
$failCount = ($lines | Where-Object { $_ -match '^\[FAIL\]' }).Count
$lines += "", "=== RESULT: $passCount PASS, $failCount FAIL ==="

$reportFull = Join-Path $Root $ReportPath
$dir = Split-Path $reportFull -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$lines | Out-File -FilePath $reportFull -Encoding utf8
Write-Host ""
Write-Host "Report: $ReportPath"
if ($failed) { exit 1 }
