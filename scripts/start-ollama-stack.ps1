# Start IPE demo stack with Ollama as the LLM backbone.
# Usage: .\scripts\start-ollama-stack.ps1
#        .\scripts\start-ollama-stack.ps1 -Model llama3.2:3b

param(
    [string]$Model = "llama3.2:3b",
    [switch]$SkipPull,
    [switch]$SkipBuild,
    [switch]$UseHostOllama
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$DockerDir = Join-Path $Root "infrastructure\docker"
$Compose = @(
    "-f", "docker-compose.yml",
    "-f", "docker-compose.demo.yml"
)
if ($UseHostOllama) {
    $Compose += @("-f", "docker-compose.ollama-host.yml")
} else {
    $Compose += @("-f", "docker-compose.ollama.yml", "--profile", "ollama")
}

Push-Location $DockerDir
try {
    Write-Host "=== IPE + Ollama stack ===" -ForegroundColor Cyan

    docker compose @Compose up -d db redis zookeeper kafka 2>&1 | Out-Null
    if (-not $UseHostOllama) {
        docker compose @Compose up -d ollama 2>&1 | Out-Null
    }
    Start-Sleep -Seconds 5

    if (-not $SkipPull -and -not $UseHostOllama) {
        Write-Host "Pulling Ollama model: $Model (first run may take several minutes)..." -ForegroundColor Yellow
        docker compose @Compose exec -T ollama ollama pull $Model
        if ($LASTEXITCODE -ne 0) { throw "ollama pull failed" }
    }

    $env:IPE_OLLAMA_MODEL = $Model
    $env:IPE_LLM_PRIMARY_PROVIDER = "ollama"
    if ($UseHostOllama) {
        $env:IPE_OLLAMA_ENDPOINT_URL = "http://host.docker.internal:11434"
    } else {
        $env:IPE_OLLAMA_ENDPOINT_URL = "http://ollama:11434"
    }
    $env:IPE_OPENROUTER_API_KEY = ""
    $env:IPE_ANTHROPIC_API_KEY = ""

    if (-not $SkipBuild) {
        docker compose @Compose build nlp-svc 2>&1 | Select-Object -Last 8
    }

    docker compose @Compose up -d nlp-svc dpe-svc mat-svc cap-svc fea-svc alert-svc res-svc del-svc kong 2>&1 | Out-Null

    Write-Host "Waiting for nlp-svc..." -ForegroundColor Yellow
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $h = Invoke-WebRequest -Uri "http://localhost:8007/api/v1/health" -UseBasicParsing -TimeoutSec 5
            if ($h.StatusCode -eq 200) { $ready = $true; break }
        } catch { }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw "nlp-svc not healthy" }

    Write-Host ""
    Write-Host "Ollama stack ready." -ForegroundColor Green
    Write-Host "  API:  http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  UI:   http://localhost:8082" -ForegroundColor Cyan
    Write-Host "  LLM:  Ollama $Model @ $($env:IPE_OLLAMA_ENDPOINT_URL)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Verify Copilot:" -ForegroundColor Yellow
    Write-Host '  POST /api/v1/copilot/query and /api/v1/copilot/chat with JWT' -ForegroundColor Gray
}
finally {
    Pop-Location
}
