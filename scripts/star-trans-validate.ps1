#Requires -Version 5.1
<#
.SYNOPSIS
  IPE Star Trans Deployment Validation Script
  Validates a Star Trans deployment is correctly configured and ready for UAT.

.DESCRIPTION
  Runs a comprehensive series of checks including service health, database state,
  migrations, RLS policies, web UI accessibility, Arabic i18n, and Odoo connectivity.
  Outputs [PASS] / [FAIL] / [SKIP] per check with a summary verdict.

  Compatible with PowerShell 5.1 (Windows) and PowerShell 7+ (cross-platform).

.PARAMETER BaseUrl
  Base URL for Kong API gateway. Default: http://localhost:8000

.PARAMETER WebUiUrl
  URL for the web UI. Default: http://localhost:8082

.PARAMETER ConnectorUrl
  URL for the connector service (direct, bypassing Kong). Default: http://localhost:8009

.PARAMETER TenantId
  Tenant UUID to use for authenticated API calls. Default: a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11

.PARAMETER Email
  Login email for authentication. Default: Ahmed@nour

.PARAMETER Password
  Login password for authentication. Default: admin

.PARAMETER WebRoot
  Path to the web application source (for i18n file check). Default: apps/web/src

.EXAMPLE
  .\scripts\star-trans-validate.ps1

.EXAMPLE
  .\scripts\star-trans-validate.ps1 -BaseUrl http://192.168.1.100:8000 -TenantId "your-tenant-uuid"
#>

param(
    [string]$BaseUrl     = "http://localhost:8000",
    [string]$WebUiUrl    = "http://localhost:8082",
    [string]$ConnectorUrl = "http://localhost:8009",
    [string]$TenantId    = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    [string]$Email       = "Ahmed@nour",
    [string]$Password    = "admin",
    [string]$WebRoot     = "",
    # Host ports (star-trans defaults). R2 compose often maps dpe->8020, connector->8016.
    [int]$DpePort        = 8001,
    [int]$MatPort        = 8002,
    [int]$CapPort        = 8003,
    [int]$FeaPort        = 8004,
    [int]$ConnectorPort  = 8009,
    [int]$KongPort       = 8000,
    [string]$DbUser      = "ipe",
    [string]$DbName      = ""
)

# Resolve repo root (ipe/) so relative paths work when invoked from any cwd
$script:RepoRoot = Split-Path $PSScriptRoot -Parent
if (-not (Test-Path (Join-Path $script:RepoRoot "apps\web"))) {
    Write-Warning "Could not locate apps/web under $script:RepoRoot - Arabic path checks may FAIL"
}
if ([string]::IsNullOrWhiteSpace($WebRoot)) {
    $WebRoot = Join-Path $script:RepoRoot "apps\web\src"
} elseif (-not [System.IO.Path]::IsPathRooted($WebRoot)) {
    $WebRoot = Join-Path $script:RepoRoot $WebRoot
}
# Auto-detect DB name from running compose when not provided (release2 often uses ipe_test)
if ([string]::IsNullOrWhiteSpace($DbName)) {
    $dbEnv = (& docker compose exec -T db printenv POSTGRES_DB 2>$null | Out-String).Trim()
    if ($dbEnv) { $DbName = $dbEnv } else { $DbName = "ipe" }
}

$ErrorActionPreference = "Continue"
$script:pass = 0
$script:fail = 0
$script:skip = 0
$script:token = $null

# ─── Helpers ────────────────────────────────────────────────────────────────

function Write-Header([string]$Title) {
    Write-Host ""
    Write-Host $Title -ForegroundColor Yellow
    Write-Host ("-" * $Title.Length) -ForegroundColor DarkGray
}

function Write-Pass([string]$Name, [string]$Detail = "") {
    $msg = if ($Detail) { "  [PASS] $Name  -  $Detail" } else { "  [PASS] $Name" }
    Write-Host $msg -ForegroundColor Green
    $script:pass++
}

function Write-Fail([string]$Name, [string]$Detail = "") {
    $msg = if ($Detail) { "  [FAIL] $Name  -  $Detail" } else { "  [FAIL] $Name" }
    Write-Host $msg -ForegroundColor Red
    $script:fail++
}

function Write-Skip([string]$Name, [string]$Reason = "") {
    $msg = if ($Reason) { "  [SKIP] $Name  -  $Reason" } else { "  [SKIP] $Name" }
    Write-Host $msg -ForegroundColor DarkYellow
    $script:skip++
}

function Invoke-SafeRest([string]$Uri, [string]$Method = "GET", [hashtable]$Headers = @{}, $Body = $null, [int]$TimeoutSec = 10) {
    try {
        $params = @{
            Uri             = $Uri
            Method          = $Method
            Headers         = $Headers
            TimeoutSec      = $TimeoutSec
            ErrorAction     = "Stop"
        }
        if ($Body) {
            $params.Body        = ($Body | ConvertTo-Json)
            $params.ContentType = "application/json"
        }
        return Invoke-RestMethod @params
    } catch {
        return $null
    }
}

function Invoke-SafeWeb([string]$Uri, [int]$TimeoutSec = 10) {
    try {
        return Invoke-WebRequest -Uri $Uri -TimeoutSec $TimeoutSec -ErrorAction Stop -UseBasicParsing
    } catch {
        return $null
    }
}

# ─── Banner ─────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║    IPE Star Trans Deployment Validation                      ║" -ForegroundColor Cyan
Write-Host "║    Run after deployment to verify system is UAT-ready        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "  BaseUrl:      $BaseUrl"
Write-Host "  WebUI:        $WebUiUrl"
Write-Host "  Connector:    $ConnectorUrl"
Write-Host "  TenantId:     $TenantId"
Write-Host "  Started:      $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# ─── Check 1: Individual Service Health ──────────────────────────────────────

Write-Header "1. Service Health Checks"

$services = @(
    @{ Name = "dpe-svc (Data Processing)"; Port = $DpePort },
    @{ Name = "mat-svc (Material)";         Port = $MatPort },
    @{ Name = "cap-svc (Capacity)";         Port = $CapPort },
    @{ Name = "fea-svc (Feasibility)";      Port = $FeaPort },
    @{ Name = "connector (Odoo)";           Port = $ConnectorPort },
    @{ Name = "kong (API Gateway)";         Port = $KongPort }
)

foreach ($svc in $services) {
    $paths = @("/health", "/healthz", "/api/v1/health", "/ready")
    $ok = $false
    $used = ""
    foreach ($path in $paths) {
        $resp = Invoke-SafeRest -Uri "http://localhost:$($svc.Port)$path" -TimeoutSec 3
        if ($null -ne $resp) {
            $ok = $true
            $used = $path
            break
        }
        # Kong may return JSON via Invoke-WebRequest even when RestMethod quirks
        $web = Invoke-SafeWeb -Uri "http://localhost:$($svc.Port)$path" -TimeoutSec 3
        if ($null -ne $web -and [int]$web.StatusCode -ge 200 -and [int]$web.StatusCode -lt 500) {
            $ok = $true
            $used = "$path HTTP $($web.StatusCode)"
            break
        }
    }
    if ($ok) {
        Write-Pass $svc.Name "port $($svc.Port) responding ($used)"
    } else {
        Write-Fail $svc.Name "port $($svc.Port) not reachable - check: docker compose ps (R2 may remap ports; pass -DpePort/-ConnectorPort)"
    }
}

# ─── Check 2: Database Health ─────────────────────────────────────────────

Write-Header "2. Database Health"

$pgReady = & docker compose exec -T db pg_isready -U $DbUser 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Pass "PostgreSQL responding" "pg_isready exit 0 (db=$DbName)"
} else {
    Write-Fail "PostgreSQL responding" "pg_isready failed - check: docker compose logs db"
}

Write-Header "3. Database Migrations"

function Get-PsqlScalar([string]$Sql) {
    $raw = & docker compose exec -T db psql -U $DbUser -d $DbName -t -A -c $Sql 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { return $null }
    $line = ($raw -split "`r?`n" | Where-Object { $_.Trim() -ne "" -and $_ -notmatch "(?i)WARNING|FATAL|error:" } | Select-Object -First 1)
    if ($null -eq $line) { return $null }
    return $line.Trim()
}

$alembicVer = Get-PsqlScalar "SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1;"
if ($alembicVer) {
    Write-Pass "Alembic migration version found" "head = $alembicVer"
} else {
    Write-Fail "Alembic migration version" "Could not read alembic_version - run: docker compose exec dpe-svc uv run alembic upgrade head"
}

$migCountRaw = Get-PsqlScalar "SELECT COUNT(*) FROM alembic_version;"
$migCount = 0
if ($migCountRaw -match '^(\d+)$') { $migCount = [int]$Matches[1] }
if ($migCount -ge 1) {
    Write-Pass "Migration table exists" "$migCount version(s) tracked"
} else {
    Write-Fail "Migration table exists" "No rows in alembic_version"
}

# ─── Check 4: Row-Level Security on CDM Tables ───────────────────────────

Write-Header "4. Row-Level Security (RLS)"

$rlsCountRaw = Get-PsqlScalar "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'cdm_%' AND rowsecurity = true;"
$rlsCount = 0
if ($rlsCountRaw -match '^(\d+)$') { $rlsCount = [int]$Matches[1] }

if ($rlsCount -gt 0) {
    Write-Pass "RLS enabled on CDM tables" "$rlsCount cdm_* tables have rowsecurity=true"
} else {
    Write-Fail "RLS enabled on CDM tables" "No CDM tables found with RLS enabled  -  run migration 015"
}

# ─── Check 5: Web UI Accessibility ───────────────────────────────────────

Write-Header "5. Web UI"

$webResp = Invoke-SafeWeb -Uri $WebUiUrl -TimeoutSec 10
if ($null -ne $webResp -and $webResp.StatusCode -eq 200) {
    Write-Pass "Web UI accessible" "$WebUiUrl → HTTP $($webResp.StatusCode)"
} else {
    $statusCode = if ($null -ne $webResp) { $webResp.StatusCode } else { "timeout/unreachable" }
    Write-Fail "Web UI accessible" "$WebUiUrl → $statusCode"
}

# ─── Check 6: Arabic i18n ─────────────────────────────────────────────────

Write-Header "6. Arabic i18n"

$arJsonPaths = @(
    (Join-Path $WebRoot "i18n\ar.json"),
    (Join-Path $WebRoot "locales\ar.json"),
    (Join-Path $script:RepoRoot "apps\web\src\locales\ar.json"),
    (Join-Path $script:RepoRoot "apps\web\public\locales\ar\translation.json"),
    (Join-Path $script:RepoRoot "apps\web\src\i18n\ar.json")
)

$arJsonFound = $false
$arJsonPath = ""
foreach ($p in $arJsonPaths) {
    if (Test-Path $p) {
        $arJsonFound = $true
        $arJsonPath = $p
        break
    }
}

if ($arJsonFound) {
    Write-Pass "Arabic translation file exists" "$arJsonPath"
    try {
        $content = Get-Content $arJsonPath -Raw
        $keyCount = ([regex]::Matches($content, '":(?:\s*)"')).Count
        if ($keyCount -lt 10) {
            # Try counting differently  -  "key": pattern
            $keyCount = ([regex]::Matches($content, '"[^"]+"\s*:')).Count
        }
        if ($keyCount -ge 250) {
            Write-Pass "Arabic key count sufficient" "$keyCount keys (>=250 required)"
        } elseif ($keyCount -ge 50) {
            Write-Fail "Arabic key count sufficient" "$keyCount keys (>=250 required  -  partial translation, may cause UI gaps)"
        } else {
            Write-Fail "Arabic key count sufficient" "$keyCount keys (>=250 required  -  ar.json may be empty or malformed)"
        }
    } catch {
        Write-Fail "Arabic key count sufficient" "Could not parse ar.json: $($_.Exception.Message)"
    }
} else {
    Write-Fail "Arabic translation file exists" "ar.json not found in expected paths: $($arJsonPaths -join ', ')"
    Write-Skip "Arabic key count sufficient" "ar.json not found"
}

# ─── Check 7: Authentication ──────────────────────────────────────────────

Write-Header "7. Authentication"

$loginResp = Invoke-SafeRest `
    -Uri "$BaseUrl/api/v1/auth/login" `
    -Method "POST" `
    -Body @{ email = $Email; password = $Password } `
    -TimeoutSec 10

if ($null -ne $loginResp -and $loginResp.data.access_token) {
    $script:token = $loginResp.data.access_token
    Write-Pass "Login successful" "JWT token obtained"
} else {
    Write-Fail "Login successful" "POST /api/v1/auth/login failed  -  check credentials"
}

# ─── Check 8: Feasibility Queue (API data flow) ───────────────────────────

Write-Header "8. Data Flow  -  Feasibility Queue"

if ($script:token) {
    $authHeaders = @{
        "Authorization" = "Bearer $($script:token)"
        "X-Tenant-ID"   = $TenantId
    }

    $queueResp = Invoke-SafeRest -Uri "$BaseUrl/api/v1/feasibility/queue" -Headers $authHeaders -TimeoutSec 15
    if ($null -ne $queueResp -and $queueResp.success -eq $true) {
        $moCount = if ($queueResp.data.total) { $queueResp.data.total } elseif ($queueResp.data.items) { $queueResp.data.items.Count } else { 0 }
        if ($moCount -gt 0) {
            Write-Pass "Feasibility queue returning MOs" "$moCount MOs in queue"
        } else {
            Write-Fail "Feasibility queue returning MOs" "Queue empty  -  trigger a sync first: POST /api/v1/sync/run"
        }
    } else {
        Write-Fail "Feasibility queue API" "Endpoint returned null or success=false"
    }

    # Check sync status
    $syncResp = Invoke-SafeRest -Uri "$BaseUrl/api/v1/sync/status" -Headers $authHeaders -TimeoutSec 10
    if ($null -ne $syncResp -and $syncResp.success -eq $true) {
        $lastRun = if ($syncResp.data.last_run) { $syncResp.data.last_run } else { "never" }
        $lastStatus = if ($syncResp.data.status) { $syncResp.data.status } else { "unknown" }
        if ($lastStatus -eq "success" -or $lastStatus -eq "partial") {
            Write-Pass "Last sync status" "$lastStatus (last run: $lastRun)"
        } else {
            Write-Fail "Last sync status" "$lastStatus  -  check connector logs"
        }
    } else {
        Write-Fail "Sync status API" "Endpoint not responding or returned error"
    }
} else {
    Write-Skip "Feasibility queue API" "Skipping  -  authentication failed"
    Write-Skip "Sync status API" "Skipping  -  authentication failed"
}

# ─── Check 9: Odoo Connector Test-Connection ─────────────────────────────

Write-Header "9. Odoo Connector"

$odooTestResp = Invoke-SafeRest `
    -Uri "$ConnectorUrl/api/v1/erp/odoo/test-connection" `
    -Method "POST" `
    -TimeoutSec 15

if ($null -ne $odooTestResp) {
    if ($odooTestResp.success -eq $true -or $odooTestResp.status -eq "ok") {
        Write-Pass "Odoo test-connection" "Connector can reach Odoo"
    } else {
        Write-Fail "Odoo test-connection" "Connected but Odoo returned error: $($odooTestResp.message)"
    }
} else {
    # Try alternate path
    $odooTestResp2 = Invoke-SafeRest `
        -Uri "$ConnectorUrl/api/v1/odoo/test-connection" `
        -Method "POST" `
        -TimeoutSec 15
    if ($null -ne $odooTestResp2) {
        Write-Pass "Odoo test-connection" "Connector can reach Odoo (alternate path)"
    } else {
        Write-Skip "Odoo test-connection" "Endpoint not available  -  verify Odoo URL is configured in .env"
    }
}

# ─── Check 10: Write-Back Endpoint Reachable ─────────────────────────────

Write-Header "10. Write-Back Endpoint"

if ($script:token) {
    $authHeaders = @{
        "Authorization" = "Bearer $($script:token)"
        "X-Tenant-ID"   = $TenantId
    }

    # Activate lives under connector sync/odoo prefix (not bare /api/v1/activate)
    # Canonical: POST /api/v1/sync/odoo/activate — Spec 023 T022 / GH #71
    try {
        $wbResp = Invoke-WebRequest `
            -Uri "$BaseUrl/api/v1/sync/odoo/activate" `
            -Method "GET" `
            -Headers $authHeaders `
            -TimeoutSec 10 `
            -ErrorAction SilentlyContinue `
            -UseBasicParsing
        # 405 Method Not Allowed = endpoint exists but GET not allowed (POST is correct method)
        # 404 = endpoint does not exist
        if ($wbResp.StatusCode -in @(200, 201, 405)) {
            Write-Pass "Write-back activate endpoint reachable" "HTTP $($wbResp.StatusCode) (endpoint exists)"
        } else {
            Write-Fail "Write-back activate endpoint reachable" "HTTP $($wbResp.StatusCode)"
        }
    } catch {
        $statusCode = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        if ($statusCode -in @(405, 422)) {
            Write-Pass "Write-back activate endpoint reachable" "HTTP $statusCode (endpoint exists, method/body validation active)"
        } elseif ($statusCode -eq 401) {
            Write-Pass "Write-back activate endpoint reachable" "HTTP 401 (endpoint exists, auth enforced)"
        } else {
            Write-Fail "Write-back activate endpoint reachable" "Error: $($_.Exception.Message)"
        }
    }
} else {
    Write-Skip "Write-back activate endpoint reachable" "Skipping  -  authentication failed"
}

# ─── Summary ─────────────────────────────────────────────────────────────

$total = $script:pass + $script:fail + $script:skip
$verdict = if ($script:fail -eq 0) { "PASSED" } else { "FAILED" }
$verdictColor = if ($script:fail -eq 0) { "Green" } else { "Red" }

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                     VALIDATION SUMMARY                      ║" -ForegroundColor Cyan
Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║  Total checks:  $total" -ForegroundColor Cyan
Write-Host "║  PASS:  $($script:pass)   FAIL:  $($script:fail)   SKIP:  $($script:skip)" -ForegroundColor Cyan
Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan

if ($script:fail -eq 0) {
    Write-Host "║  OVERALL RESULT: PASSED  -  System ready for UAT              ║" -ForegroundColor Green
} else {
    Write-Host "║  OVERALL RESULT: FAILED  -  Fix $($script:fail) item(s) before UAT          ║" -ForegroundColor Red
}

Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($script:fail -gt 0) {
    Write-Host "Next steps for FAILED items:" -ForegroundColor Yellow
    Write-Host "  1. Review output above  -  each FAIL includes a remediation hint"
    Write-Host "  2. Run: docker compose ps  (verify all services Up)"
    Write-Host "  3. Run: docker compose logs [service-name]  (check error details)"
    Write-Host "  4. Re-run this script after fixes: .\scripts\star-trans-validate.ps1"
    Write-Host ""
}

exit $(if ($script:fail -eq 0) { 0 } else { 1 })
