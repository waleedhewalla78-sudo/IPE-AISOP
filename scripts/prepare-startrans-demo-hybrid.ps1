# Star Trans — 180-Minute Hybrid Demo (Mixed Audience + Copilot)
# One-shot prep: full seed (32/32) + Odoo sync path + Ollama for Copilot
# Usage: .\scripts\prepare-startrans-demo-hybrid.ps1

param(
    [switch]$SkipValidation,
    [switch]$SkipOdooSync,
    [switch]$SkipOllamaPull,
    [switch]$UseHostOllama
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$DockerDir = Join-Path $Root "infrastructure\docker"
$TenantId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

function Invoke-DockerCompose {
    param([string[]]$Args)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & docker compose @Args 2>&1 | Out-Null
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) { throw "docker compose failed (exit $code): docker compose $($Args -join ' ')" }
}

Write-Host "=== Star Trans HYBRID Demo Preparation (180 min) ===" -ForegroundColor Cyan
Write-Host "  Mode: Seeded 32/32 + live Odoo sync + Copilot" -ForegroundColor DarkGray

# --- 1. Core + planning + connector + v8 + copilot services ---
Push-Location $DockerDir
try {
    $composeArgs = @("-f", "docker-compose.yml", "-f", "docker-compose.demo.yml")
    if ($UseHostOllama) {
        $composeArgs += @("-f", "docker-compose.ollama-host.yml")
    } else {
        $composeArgs += @("-f", "docker-compose.ollama.yml", "--profile", "ollama")
    }

    Write-Host "`n[1/6] Starting infrastructure + services..." -ForegroundColor Yellow
    Invoke-DockerCompose -Args ($composeArgs + @("up", "-d", "db", "redis"))
    if (-not $UseHostOllama) {
        Invoke-DockerCompose -Args ($composeArgs + @("up", "-d", "ollama"))
        Start-Sleep -Seconds 8
        if (-not $SkipOllamaPull) {
            Write-Host "  Pulling Ollama model llama3.2:3b (skip with -SkipOllamaPull)..." -ForegroundColor DarkGray
            $prev = $ErrorActionPreference
            $ErrorActionPreference = "Continue"
            docker compose @composeArgs exec -T ollama ollama pull llama3.2:3b 2>&1 | Out-Null
            $ErrorActionPreference = $prev
        }
    }

    $services = @(
        "dpe-svc", "mat-svc", "cap-svc", "fea-svc", "res-svc", "del-svc",
        "nlp-svc", "connector", "alert-svc",
        "demand-svc", "scenario-svc", "supply-svc", "order-svc",
        "equipment-svc", "material-svc", "procurement-svc",
        "sustain-svc", "quality-svc", "kong"
    )
    Invoke-DockerCompose -Args ($composeArgs + @("up", "-d") + $services)
    Invoke-DockerCompose -Args ($composeArgs + @("up", "-d", "--force-recreate", "kong"))
    # Verify critical containers are running (not just Exited)
    Start-Sleep -Seconds 5
    $required = @("nlp-svc", "res-svc", "demand-svc", "fea-svc", "cap-svc", "mat-svc", "ollama")
    $psOut = docker compose @composeArgs ps --format "{{.Service}} {{.State}}" 2>&1
    foreach ($svc in $required) {
        if ($psOut -notmatch "$svc running") {
            Write-Host "  WARN: $svc not running - attempting start..." -ForegroundColor Yellow
            Invoke-DockerCompose -Args ($composeArgs + @("up", "-d", $svc))
        }
    }
} finally {
    Pop-Location
}

Write-Host "  Waiting 20s for health checks..." -ForegroundColor DarkGray
Start-Sleep -Seconds 20

# --- 2. Seed Star Trans demo data ---
Write-Host "`n[2/6] Seeding Star Trans demo data..." -ForegroundColor Yellow
& (Join-Path $Root "scripts\seed-startrans-demo.ps1")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& (Join-Path $Root "scripts\convert-project-plan-to-xlsx.ps1")

# --- 3. Configure tenant for Odoo (hybrid sync act) ---
Write-Host "`n[3/6] Ensuring tenant Odoo config..." -ForegroundColor Yellow
docker exec docker-db-1 psql -U ipe -d ipe_test -c @"
UPDATE cdm_tenant SET
  name = 'Star Trans',
  erp_type = 'odoo',
  erp_version = '19.0',
  erp_base_url = 'http://host.docker.internal:8069',
  config = COALESCE(config,'{}'::jsonb) || jsonb_build_object(
    'odoo_url','http://host.docker.internal:8069',
    'odoo_db','starttrans1',
    'odoo_username','whewalla@gmail.com',
    'odoo_password','admin'
  )
WHERE id = '$TenantId';
"@ 2>&1 | Out-Null

# --- 4. Optional live Odoo sync smoke ---
if (-not $SkipOdooSync) {
    Write-Host "`n[4/6] Testing Odoo sync (requires Odoo on :8069)..." -ForegroundColor Yellow
    try {
        $loginBody = '{"email":"Ahmed@nour","password":"admin"}'
        $login = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
            -Method POST -ContentType "application/json" -Body $loginBody -TimeoutSec 30
        $headers = @{
            Authorization = "Bearer $($login.data.access_token)"
            "X-Tenant-ID"  = $TenantId
        }
        $sync = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/sync/run" `
            -Method POST -ContentType "application/json" -Body '{"entity":"manufacturing_orders"}' `
            -Headers $headers -TimeoutSec 120
        if ($sync.success) {
            $mo = $sync.data.manufacturing_orders
            Write-Host "  Odoo MO sync OK: updated=$($mo.updated) synced=$($mo.synced) skipped=$($mo.skipped)" -ForegroundColor Green
        } else {
            Write-Host "  Odoo sync returned error (continue with seed-only): $($sync.error.message)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  Odoo sync skipped/failed (seed demo still OK): $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "  Start Odoo before demo for Act 0 hybrid segment." -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[4/6] Skipping Odoo sync (-SkipOdooSync)" -ForegroundColor DarkGray
}

# --- 5. Pre-warm Copilot ---
Write-Host "`n[5/6] Pre-warming Copilot (optional)..." -ForegroundColor Yellow
try {
    if (-not $login) {
        $loginBody = '{"email":"Ahmed@nour","password":"admin"}'
        $login = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
            -Method POST -ContentType "application/json" -Body $loginBody -TimeoutSec 30
    }
    $headers = @{
        Authorization = "Bearer $($login.data.access_token)"
        "X-Tenant-ID"  = $TenantId
    }
    $body = '{"query":"Which manufacturing orders are at risk this week?","agent_role":"planner"}'
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/copilot/query" `
        -Method POST -ContentType "application/json" -Body $body -Headers $headers -TimeoutSec 180 | Out-Null
    Write-Host "  Copilot pre-warm OK" -ForegroundColor Green
} catch {
    Write-Host "  Copilot pre-warm failed - use Resolution Center backup in Act 4" -ForegroundColor Yellow
}

# --- 6. Full demo validation ---
if (-not $SkipValidation) {
    Write-Host "`n[6/6] Running 32/32 validation..." -ForegroundColor Yellow
    & (Join-Path $Root "scripts\run-full-demo.ps1") `
        -Profile startrans `
        -ReportPath (Join-Path $Root "docs\demo-data\startrans-pre-demo.txt")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Host "`n[6/6] Skipping validation (-SkipValidation)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "=== HYBRID DEMO READY ===" -ForegroundColor Green
Write-Host "  Runbook: docs\demo-data\STARTRANS-DEMO-180MIN-HYBRID-RUNBOOK.md" -ForegroundColor Cyan
Write-Host "  UI:      http://localhost:8082/login" -ForegroundColor Cyan
Write-Host "  Login:   Ahmed@nour / admin" -ForegroundColor Cyan
Write-Host "  Profile: FULL (default npm run dev - NOT release1)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Next terminal:" -ForegroundColor Yellow
Write-Host "    cd apps\web; npm run dev" -ForegroundColor White
Write-Host ""
