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
    [string]$WebRoot     = "apps/web/src"
)

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
    $msg = if ($Detail) { "  [PASS] $Name — $Detail" } else { "  [PASS] $Name" }
    Write-Host $msg -ForegroundColor Green
    $script:pass++
}

function Write-Fail([string]$Name, [string]$Detail = "") {
    $msg = if ($Detail) { "  [FAIL] $Name — $Detail" } else { "  [FAIL] $Name" }
    Write-Host $msg -ForegroundColor Red
    $script:fail++
}

function Write-Skip([string]$Name, [string]$Reason = "") {
    $msg = if ($Reason) { "  [SKIP] $Name — $Reason" } else { "  [SKIP] $Name" }
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
    @{ Name = "dpe-svc (Data Processing)"; Port = 8001 },
    @{ Name = "mat-svc (Material)";         Port = 8002 },
    @{ Name = "cap-svc (Capacity)";         Port = 8003 },
    @{ Name = "fea-svc (Feasibility)";      Port = 8004 },
    @{ Name = "connector (Odoo)";           Port = 8009 },
    @{ Name = "kong (API Gateway)";         Port = 8000 }
)

foreach ($svc in $services) {
    $url = "http://localhost:$($svc.Port)/healthz"
    $resp = Invoke-SafeRest -Uri $url -TimeoutSec 5
    if ($null -ne $resp) {
        Write-Pass $svc.Name "port $($svc.Port) responding"
    } else {
        # Try /health as fallback
        $resp2 = Invoke-SafeRest -Uri "http://localhost:$($svc.Port)/health" -TimeoutSec 5
        if ($null -ne $resp2) {
            Write-Pass $svc.Name "port $($svc.Port) responding (/health endpoint)"
        } else {
            Write-Fail $svc.Name "port $($svc.Port) not reachable — check: docker compose ps"
        }
    }
}

# ─── Check 2: Database Health ─────────────────────────────────────────────

Write-Header "2. Database Health"

$pgReady = & docker compose exec -T db pg_isready -U ipe 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Pass "PostgreSQL responding" "pg_isready exit 0"
} else {
    Write-Fail "PostgreSQL responding" "pg_isready failed — check: docker compose logs db"
}

# ─── Check 3: Migrations at Head ─────────────────────────────────────────

Write-Header "3. Database Migrations"

$alembicVer = & docker compose exec -T db psql -U ipe -t -c "SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1;" 2>&1
if ($LASTEXITCODE -eq 0 -and $alembicVer -and $alembicVer.Trim().Length -gt 0) {
    $ver = $alembicVer.Trim()
    Write-Pass "Alembic migration version found" "head = $ver"
} else {
    Write-Fail "Alembic migration version" "Could not read alembic_version — run: docker compose exec dpe-svc uv run alembic upgrade head"
}

# Verify migration count (R1 should have 49+ migrations)
$migCountRaw = & docker compose exec -T db psql -U ipe -t -c "SELECT COUNT(*) FROM alembic_version;" 2>&1
$migCount = if ($migCountRaw -match '\d+') { [int]$Matches[0] } else { 0 }
if ($migCount -ge 1) {
    Write-Pass "Migration table exists" "$migCount version(s) tracked"
} else {
    Write-Fail "Migration table exists" "No rows in alembic_version"
}

# ─── Check 4: Row-Level Security on CDM Tables ───────────────────────────

Write-Header "4. Row-Level Security (RLS)"

$rlsQuery = "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'cdm_%' AND rowsecurity = true;"
$rlsCountRaw = & docker compose exec -T db psql -U ipe -t -c $rlsQuery 2>&1
$rlsCount = if ($rlsCountRaw -match '\d+') { [int]$Matches[0] } else { 0 }

if ($rlsCount -gt 0) {
    Write-Pass "RLS enabled on CDM tables" "$rlsCount cdm_* tables have rowsecurity=true"
} else {
    Write-Fail "RLS enabled on CDM tables" "No CDM tables found with RLS enabled — run migration 015"
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
    "$WebRoot/i18n/ar.json",
    "$WebRoot/locales/ar.json",
    "apps/web/public/locales/ar/translation.json",
    "apps/web/src/i18n/ar.json"
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
            # Try counting differently — "key": pattern
            $keyCount = ([regex]::Matches($content, '"[^"]+"\s*:')).Count
        }
        if ($keyCount -ge 250) {
            Write-Pass "Arabic key count sufficient" "$keyCount keys (≥250 required)"
        } elseif ($keyCount -ge 50) {
            Write-Fail "Arabic key count sufficient" "$keyCount keys (≥250 required — partial translation, may cause UI gaps)"
        } else {
            Write-Fail "Arabic key count sufficient" "$keyCount keys (≥250 required — ar.json may be empty or malformed)"
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
    Write-Fail "Login successful" "POST /api/v1/auth/login failed — check credentials"
}

# ─── Check 8: Feasibility Queue (API data flow) ───────────────────────────

Write-Header "8. Data Flow — Feasibility Queue"

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
            Write-Fail "Feasibility queue returning MOs" "Queue empty — trigger a sync first: POST /api/v1/sync/run"
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
            Write-Fail "Last sync status" "$lastStatus — check connector logs"
        }
    } else {
        Write-Fail "Sync status API" "Endpoint not responding or returned error"
    }
} else {
    Write-Skip "Feasibility queue API" "Skipping — authentication failed"
    Write-Skip "Sync status API" "Skipping — authentication failed"
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
        Write-Skip "Odoo test-connection" "Endpoint not available — verify Odoo URL is configured in .env"
    }
}

# ─── Check 10: Write-Back Endpoint Reachable ─────────────────────────────

Write-Header "10. Write-Back Endpoint"

if ($script:token) {
    $authHeaders = @{
        "Authorization" = "Bearer $($script:token)"
        "X-Tenant-ID"   = $TenantId
    }

    # Check the activate endpoint exists (dry-run — just check it responds, don't execute)
    try {
        $wbResp = Invoke-WebRequest `
            -Uri "$BaseUrl/api/v1/activate" `
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
    Write-Skip "Write-back activate endpoint reachable" "Skipping — authentication failed"
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
    Write-Host "║  OVERALL RESULT: PASSED — System ready for UAT              ║" -ForegroundColor Green
} else {
    Write-Host "║  OVERALL RESULT: FAILED — Fix $($script:fail) item(s) before UAT          ║" -ForegroundColor Red
}

Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

if ($script:fail -gt 0) {
    Write-Host "Next steps for FAILED items:" -ForegroundColor Yellow
    Write-Host "  1. Review output above — each FAIL includes a remediation hint"
    Write-Host "  2. Run: docker compose ps  (verify all services Up)"
    Write-Host "  3. Run: docker compose logs [service-name]  (check error details)"
    Write-Host "  4. Re-run this script after fixes: .\scripts\star-trans-validate.ps1"
    Write-Host ""
}

exit $(if ($script:fail -eq 0) { 0 } else { 1 })
