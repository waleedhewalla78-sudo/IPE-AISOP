# Run all IPE unit tests (Gate 1 validation). Excludes .venv and third-party packages.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not $env:IPE_JWT_SECRET_KEY) {
    $env:IPE_JWT_SECRET_KEY = "dev-jwt-secret-change-in-production-min-32-chars"
}
$env:OTEL_SDK_DISABLED = "true"

$LogDir = Join-Path $Root "specs\002-release-stabilization-gates\evidence\gate-1"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$failed = @()

Write-Host "=== shared ===" -ForegroundColor Cyan
Push-Location (Join-Path $Root "services\shared")
$ErrorActionPreference = "Continue"
uv run pytest tests -q --tb=no 2>&1 | Tee-Object (Join-Path $LogDir "shared.log")
if ($LASTEXITCODE -ne 0) { $failed += "shared" }
Pop-Location

$services = @(
    "dpe-svc", "mat-svc", "cap-svc", "fea-svc", "res-svc", "del-svc", "nlp-svc",
    "rec-svc", "alert-svc", "connector", "network-svc", "scn-svc", "quality-svc",
    "sustain-svc", "ml-svc"
)

foreach ($svc in $services) {
    Write-Host "=== $svc ===" -ForegroundColor Cyan
    Push-Location (Join-Path $Root "services\$svc")
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    uv run pytest tests -q --tb=no 2>&1 | Tee-Object (Join-Path $LogDir "$svc.log")
    $exit = $LASTEXITCODE
    $ErrorActionPreference = $prevEap
    if ($exit -ne 0) { $failed += $svc }
    Pop-Location
}

Write-Host "=== frontend ===" -ForegroundColor Cyan
$pnpmCmd = $null
if (Get-Command pnpm -ErrorAction SilentlyContinue) { $pnpmCmd = "pnpm" }
elseif (Test-Path "$env:USERPROFILE\.local\pnpm.cmd") { $pnpmCmd = "$env:USERPROFILE\.local\pnpm.cmd" }
if ($pnpmCmd) {
    Push-Location (Join-Path $Root "apps\web")
    if (-not (Test-Path "node_modules")) { & $pnpmCmd install 2>&1 | Out-Null }
    & $pnpmCmd test -- --run 2>&1 | Tee-Object (Join-Path $LogDir "frontend.log")
    if ($LASTEXITCODE -ne 0) { $failed += "frontend" }
    & $pnpmCmd typecheck 2>&1 | Tee-Object -Append (Join-Path $LogDir "frontend.log")
    if ($LASTEXITCODE -ne 0) { $failed += "frontend-typecheck" }
    Pop-Location
} else {
    Write-Host "pnpm not found; skipping frontend tests (install Node.js/pnpm for T020)" -ForegroundColor Yellow
    "SKIPPED: pnpm not installed on PATH" | Out-File (Join-Path $LogDir "frontend.log")
}

if ($failed.Count -gt 0) {
    Write-Host "FAILED suites: $($failed -join ', ')" -ForegroundColor Red
    exit 1
}

Write-Host "All test suites passed." -ForegroundColor Green
exit 0
