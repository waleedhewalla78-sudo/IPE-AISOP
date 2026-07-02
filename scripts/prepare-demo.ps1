# One-shot demo preparation (backend + validation).
# Usage: .\scripts\prepare-demo.ps1
# Web UI: run separately — cd apps\web && npm run dev

param([switch]$SkipDemo)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$DockerDir = Join-Path $Root "infrastructure\docker"

Write-Host "=== IPE Demo Preparation ===" -ForegroundColor Cyan

Push-Location $DockerDir
try {
    $env:IPE_OLLAMA_MODEL = "llama3.2:3b"
    $env:IPE_LLM_PRIMARY_PROVIDER = "ollama"
    $env:IPE_OLLAMA_ENDPOINT_URL = "http://host.docker.internal:11434"
    $env:IPE_OPENROUTER_API_KEY = ""
    $env:IPE_ANTHROPIC_API_KEY = ""

    Write-Host "[1/4] Ensuring host Ollama is not blocked by container..." -ForegroundColor Yellow
    docker stop docker-ollama-1 2>$null | Out-Null

    Write-Host "[2/4] Starting backend stack (Ollama host mode)..." -ForegroundColor Yellow
    docker compose `
        -f docker-compose.yml `
        -f docker-compose.demo.yml `
        -f docker-compose.ollama-host.yml `
        up -d db redis zookeeper kafka dpe-svc mat-svc cap-svc fea-svc res-svc del-svc nlp-svc alert-svc kong 2>&1 | Out-Null

    Write-Host "[3/4] Waiting for API..." -ForegroundColor Yellow
    $ready = $false
    for ($i = 0; $i -lt 40; $i++) {
        try {
            $h = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -TimeoutSec 5
            if ($h.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Seconds 3 }
    }
    if (-not $ready) { throw "API not ready on :8000" }
}
finally {
    Pop-Location
}

Write-Host "[4/4] Smoke check..." -ForegroundColor Yellow
& (Join-Path $Root "scripts\check-product.ps1")
if ($LASTEXITCODE -ne 0) { exit 1 }

if (-not $SkipDemo) {
    Write-Host "`nRunning 20-checkpoint demo (Copilot may take ~3 min)..." -ForegroundColor Yellow
    & (Join-Path $Root "scripts\run-full-demo.ps1") -ReportPath (Join-Path $Root "docs\demo-ready-report.txt")
}

Write-Host ""
Write-Host "Demo backend ready." -ForegroundColor Green
Write-Host "  API:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  UI:   http://localhost:8082/login  (start: cd apps\web && npm run dev)" -ForegroundColor Cyan
Write-Host "  Login: Ahmed@nour / admin  |  admin@demo.com / demo" -ForegroundColor Cyan
Write-Host "  Copilot LLM: Ollama llama3.2:3b on host :11434" -ForegroundColor Cyan
Write-Host "  Guide: docs\FULL-DEMO-GUIDE.md" -ForegroundColor Cyan
