# REL-STACK — lean demo stack (no ollama/airflow/keycloak). Blocks until API healthy or fails.
# Usage: .\scripts\rel-demo-stack.ps1
#        .\scripts\rel-demo-stack.ps1 -SkipBuild   # when images already built
#        .\scripts\rel-demo-stack.ps1 -DemoOnly    # skip stack; run demo only

param(
    [switch]$SkipBuild,
    [switch]$SkipSeed,
    [switch]$DemoOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$DockerDir = Join-Path $Root "infrastructure\docker"
$Compose = @("-f", "docker-compose.yml", "-f", "docker-compose.demo.yml")

$AppServices = @(
    "dpe-svc", "mat-svc", "cap-svc", "fea-svc", "res-svc", "del-svc",
    "nlp-svc", "alert-svc", "connector", "scn-svc", "network-svc", "rec-svc", "kong"
)

function Wait-HttpOk {
    param([string]$Url, [int]$MaxSec = 180)
    $deadline = (Get-Date).AddSeconds($MaxSec)
    $attempt = 0
    while ((Get-Date) -lt $deadline) {
        $attempt++
        try {
            $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
            if ($r.StatusCode -eq 200) { return $true }
        } catch { }
        if ($attempt % 10 -eq 0) {
            Write-Host "  still waiting for $Url ($attempt attempts)..." -ForegroundColor DarkGray
        }
        Start-Sleep -Seconds 3
    }
    return $false
}

function Wait-ServiceHealthy {
    param([string]$Container, [int]$MaxSec = 300)
    $deadline = (Get-Date).AddSeconds($MaxSec)
    while ((Get-Date) -lt $deadline) {
        $status = docker inspect --format "{{.State.Health.Status}}" $Container 2>$null
        if ($status -eq "healthy") { return $true }
        if ($status -eq "unhealthy") {
            Write-Host "  $Container unhealthy - check logs" -ForegroundColor DarkYellow
        }
        Start-Sleep -Seconds 5
    }
    return $false
}

if (-not $DemoOnly) {
    Push-Location $DockerDir
    try {
        Write-Host "=== REL-STACK (demo overlay) ===" -ForegroundColor Cyan

        Write-Host '[1/6] Infra (db, redis, kafka)...' -ForegroundColor Yellow
        docker compose @Compose up -d db redis zookeeper kafka
        if ($LASTEXITCODE -ne 0) { throw "infra up failed" }

        $deadline = (Get-Date).AddSeconds(120)
        do {
            $ready = docker compose @Compose exec -T db pg_isready -U ipe 2>$null
            if ($LASTEXITCODE -eq 0) { break }
            Start-Sleep -Seconds 2
        } while ((Get-Date) -lt $deadline)
        if ($LASTEXITCODE -ne 0) { throw "postgres not ready" }

        if (-not $SkipBuild) {
            Write-Host "`n[2/6] Building app images (first run ~10-20 min)..." -ForegroundColor Yellow
            docker compose @Compose build @AppServices
            if ($LASTEXITCODE -ne 0) { throw "build failed" }
        } else {
            Write-Host "`n[2/6] Skipping build (-SkipBuild)" -ForegroundColor DarkYellow
        }

        Write-Host "`n[3/6] Migrations..." -ForegroundColor Yellow
        docker compose @Compose run --rm migrate
        if ($LASTEXITCODE -ne 0) { throw "migrate failed" }

        Write-Host "`n[4/6] Starting app services + Kong..." -ForegroundColor Yellow
        docker compose @Compose up -d @AppServices
        if ($LASTEXITCODE -ne 0) { throw "app services up failed" }

        Write-Host '[5/6] Waiting for core services and Kong on port 8000...' -ForegroundColor Yellow
        foreach ($c in @("docker-dpe-svc-1", "docker-cap-svc-1", "docker-mat-svc-1")) {
            Write-Host "  waiting for $c healthy..." -ForegroundColor DarkGray
            if (-not (Wait-ServiceHealthy $c 360)) {
                docker logs $c --tail 20 2>&1 | ForEach-Object { Write-Host "    $_" }
            }
        }
        $apiOk = $false
        if (Wait-HttpOk "http://localhost:8020/api/v1/health" 120) {
            Write-Host "  dpe-svc direct :8020 OK" -ForegroundColor DarkGreen
        }
        if (Wait-HttpOk "http://localhost:8000/api/v1/health" 420) {
            $apiOk = $true
        }
        if (-not $apiOk) {
            Write-Host "  docker ps:" -ForegroundColor Red
            docker ps -a --format "table {{.Names}}\t{{.Status}}" 2>&1 | Select-String "docker-" | ForEach-Object { Write-Host "    $_" }
            docker logs docker-kong-1 --tail 15 2>&1 | ForEach-Object { Write-Host "    kong: $_" }
            throw "Kong/API not healthy on :8000 after 420s"
        }
        Write-Host "API healthy." -ForegroundColor Green

        if (-not $SkipSeed) {
            Write-Host "`n[6/6] Seed data..." -ForegroundColor Yellow
            Pop-Location
            & (Join-Path $Root "scripts\seed-data.ps1")
            if ($LASTEXITCODE -ne 0) { throw "seed-data failed" }
            & (Join-Path $Root "scripts\seed-demo-client.ps1")
            if ($LASTEXITCODE -ne 0) { throw "seed-demo-client failed" }
            Push-Location $DockerDir
        } else {
            Write-Host "`n[6/6] Skipping seed (-SkipSeed)" -ForegroundColor DarkYellow
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host '=== Full demo (20 checkpoints) ===' -ForegroundColor Cyan
$report = Join-Path $Root "docs\demo-run-report-v6.txt"
& (Join-Path $Root "scripts\run-full-demo.ps1") -ReportPath $report
$demoExit = $LASTEXITCODE
Write-Host '=== REL-STACK COMPLETE [6/6] ===' -ForegroundColor Green
Write-Host '  API: http://localhost:8000  Report: docs\demo-run-report-v6.txt' -ForegroundColor Cyan
exit $demoExit
