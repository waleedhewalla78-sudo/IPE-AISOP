# Start IPE — ready-to-use local product stack (Windows PowerShell)
# Usage: .\scripts\start-product.ps1
# Optional: .\scripts\start-product.ps1 -SkipSeed -SkipFrontend

param(
    [switch]$SkipSeed,
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$DockerDir = Join-Path $Root "infrastructure\docker"
$WebDir = Join-Path $Root "apps\web"

Write-Host "=== IPE Product Startup ===" -ForegroundColor Cyan
Write-Host "Repository: $Root"

Push-Location $DockerDir
try {
    Write-Host "`n[1/5] Starting Docker services..." -ForegroundColor Yellow
    docker compose up -d
    if ($LASTEXITCODE -ne 0) { throw "docker compose up failed" }

    Write-Host "`n[2/5] Ensuring dpe-svc (auth API) is current..." -ForegroundColor Yellow
    docker compose build dpe-svc 2>&1 | Out-Null
    docker compose up -d dpe-svc 2>&1 | Out-Null
    docker compose up -d --force-recreate kong 2>&1 | Out-Null

    Write-Host "`n[3/5] Running database migrations..." -ForegroundColor Yellow
    docker compose run --rm migrate
    if ($LASTEXITCODE -ne 0) { throw "migrate failed" }

    if (-not $SkipSeed) {
        Write-Host "`n[4/5] Loading demo seed data..." -ForegroundColor Yellow
        $seedPs1 = Join-Path $Root "scripts\seed-data.ps1"
        & $seedPs1
        if ($LASTEXITCODE -ne 0) { throw "base seed failed" }
        $demoPs1 = Join-Path $Root "scripts\seed-demo-client.ps1"
        & $demoPs1
        if ($LASTEXITCODE -ne 0) { throw "demo seed failed" }
    } else {
        Write-Host "`n[4/5] Skipping seed (-SkipSeed)" -ForegroundColor DarkYellow
    }
}
finally {
    Pop-Location
}

Write-Host "`nBackend API (Kong): http://localhost:8000" -ForegroundColor Green
Write-Host "Health:             http://localhost:8000/api/v1/health" -ForegroundColor Green

if (-not $SkipFrontend) {
    Write-Host "`n[5/5] Starting web UI on http://localhost:8082 ..." -ForegroundColor Yellow
    Push-Location $WebDir
    try {
        if (-not (Test-Path "node_modules")) {
            npm install
        }
        Write-Host "`nLogin: admin@demo.com / demo" -ForegroundColor Cyan
        Write-Host "Keep this window open while using the app.`n" -ForegroundColor DarkYellow
        npm run dev
    }
    finally {
        Pop-Location
    }
} else {
    Write-Host "`n[5/5] Skipped frontend (-SkipFrontend). Run: cd apps/web && npm run dev" -ForegroundColor DarkYellow
}
