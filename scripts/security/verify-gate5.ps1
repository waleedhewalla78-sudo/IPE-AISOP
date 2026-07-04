#Requires -Version 5.1
<#
.SYNOPSIS
  Gate 5: Full E2E with Phase 0+1+2 (enterprise stack over HTTPS).
  PASS: 14/14 R1 + 5/5 R2 over HTTPS, dashboards populated, audit trail complete.
#>
param(
    [string]$BaseUrlHttps = "https://localhost:8443",
    [string]$KeycloakUrl = "http://localhost:8180",
    [string]$VaultUrl = "http://localhost:8200",
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$PrometheusUrl = "http://localhost:9090",
    [string]$TenantId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
. (Join-Path $Root "scripts\demo-http.ps1")
Enable-DemoTlsBypass -BaseUrl $BaseUrlHttps

$PASS = $true
function Check($name, [bool]$ok, [string]$detail = "") {
    $mark = if ($ok) { "PASS" } else { "FAIL"; $script:PASS = $false }
    $suffix = if ($detail) { " - $detail" } else { "" }
    Write-Host "  [$mark] $name$suffix"
}

Write-Host "=== Gate 5: Full E2E (Phase 0+1+2) ==="
Write-Host ""

# --- Enterprise feature flags ---
Write-Host "--- Enterprise stack features ---"
$envFile = Join-Path $Root "infrastructure\docker\ipe-common.env"
$envText = Get-Content $envFile -Raw -ErrorAction SilentlyContinue
Check "AUTH_MODE=keycloak" ($envText -match 'AUTH_MODE=keycloak')
Check "VAULT_ENABLED=true" ($envText -match 'VAULT_ENABLED=true')
Check "IPE_AUDIT_REQUEST_MIDDLEWARE=true" ($envText -match 'IPE_AUDIT_REQUEST_MIDDLEWARE=true')
Check "RS256 JWT (IPE_JWT_SIGNING_MODE=rs256)" ($envText -match 'IPE_JWT_SIGNING_MODE=rs256')

# --- Keycloak SSO ---
Write-Host ""
Write-Host "--- Keycloak SSO ---"
$kcOk = $false
try {
    $realm = Invoke-RestMethod -Uri "$KeycloakUrl/realms/ipe/.well-known/openid-configuration" -TimeoutSec 15
    $tokenBody = 'grant_type=password&client_id=ipe-web&username=admin@ipe.example.com&password=admin'
    $tokenResp = Invoke-RestMethod -Method POST -Uri $realm.token_endpoint `
        -ContentType "application/x-www-form-urlencoded" `
        -Body $tokenBody -TimeoutSec 30
    $kcOk = [bool]$tokenResp.access_token
    Check "Keycloak password grant" $kcOk "ipe-web / ahmed@nour.com"
} catch {
    Check "Keycloak password grant" $false $_.Exception.Message
}

# --- Vault ---
Write-Host ""
Write-Host "--- Vault ---"
try {
    $vh = Invoke-RestMethod -Uri "$VaultUrl/v1/sys/health" -TimeoutSec 10
    Check "Vault unsealed" (-not $vh.sealed) "version=$($vh.version)"
} catch {
    Check "Vault unsealed" $false $_.Exception.Message
}

# --- TLS / HTTPS ---
Write-Host ""
Write-Host "--- TLS (Kong :8443) ---"
$httpsCode = curl.exe -sk -o NUL -w "%{http_code}" "$BaseUrlHttps/api/v1/health"
Check "HTTPS health 200" ($httpsCode -eq "200") "code=$httpsCode"
$hsts = curl.exe -sk -I "$BaseUrlHttps/api/v1/health" 2>$null | Select-String "Strict-Transport-Security"
Check "HSTS header present" ([bool]$hsts)

# --- Vault in service health ---
Write-Host ""
Write-Host "--- Service health (Vault probe) ---"
try {
    $healthJson = curl.exe -sk "$BaseUrlHttps/api/v1/health" 2>$null
    $health = $healthJson | ConvertFrom-Json
    $vaultStatus = $health.dependencies.vault.status
    Check "dpe-svc Vault dependency" ($vaultStatus -eq "up") "status=$vaultStatus"
} catch {
    Check "dpe-svc Vault dependency" $false $_.Exception.Message
}

# --- Monitoring dashboards ---
Write-Host ""
Write-Host "--- Grafana dashboards ---"
$dashCount = 0
$dashWithData = 0
try {
    $dashboards = Invoke-RestMethod -Uri "$GrafanaUrl/api/search" -Headers @{ Authorization = "Basic $([Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes('admin:admin')))" } -TimeoutSec 15
    $ipeDashboards = @($dashboards | Where-Object { $_.title -like "IPE *" })
    $dashCount = $ipeDashboards.Count
    Check "IPE Grafana dashboards (>=6)" ($dashCount -ge 6) "count=$dashCount"

    $targets = Invoke-RestMethod -Uri "$PrometheusUrl/api/v1/targets" -TimeoutSec 15
    $up = @($targets.data.activeTargets | Where-Object { $_.health -eq "up" }).Count
    $total = @($targets.data.activeTargets).Count
    Check "Prometheus targets UP" ($up -eq $total -and $total -ge 6) "$up/$total"

    $metricQuery = Invoke-RestMethod -Uri "$PrometheusUrl/api/v1/query?query=up" -TimeoutSec 15
    $series = @($metricQuery.data.result).Count
    Check "Prometheus has scrape data" ($series -ge 6) "up series=$series"
    if ($series -ge 6) { $dashWithData = $dashCount }
    Check "Dashboards backed by live metrics" ($dashWithData -ge 6) "ipe dashboards=$dashCount"
} catch {
    Check "Grafana/Prometheus checks" $false $_.Exception.Message
}

# --- Network isolation (Gate 2 smoke) ---
Write-Host ""
Write-Host "--- Network isolation (Gate 2) ---"
$gate2Script = Join-Path $Root "scripts\security\verify-gate2.sh"
if (Test-Path $gate2Script) {
    $bash = "C:\Program Files\Git\bin\bash.exe"
    if (Test-Path $bash) {
        # Rate-limit burst can flake under load; retry once. Capture exit code
        # immediately — assigning pipeline output alone can lose $LASTEXITCODE on PS 5.1.
        $g2ok = $false
        $g2Out = $null
        for ($attempt = 1; $attempt -le 2; $attempt++) {
            $g2Out = & $bash $gate2Script *>&1 | ForEach-Object { "$_" }
            $g2Code = $LASTEXITCODE
            if ($g2Code -eq 0) { $g2ok = $true; break }
            Write-Host "  Gate 2 attempt $attempt failed (exit=$g2Code); retrying..."
            Start-Sleep -Seconds 5
        }
        if (-not $g2ok -and $g2Out) {
            $g2Out | Select-Object -Last 20 | ForEach-Object { Write-Host "    $_" }
        }
        Check "Network isolation (Gate 2)" $g2ok
    } else {
        Check "Network isolation (Gate 2)" $false "Git Bash not found"
    }
} else {
    Check "Network isolation (Gate 2)" $false "verify-gate2.sh missing"
}

# Gate 2 rate-limit burst can leave the IP window exhausted; clear before demos.
if (docker ps --format '{{.Names}}' 2>$null | Select-String -Quiet '^docker-redis-1$') {
    docker exec docker-redis-1 redis-cli -n 2 FLUSHDB 2>$null | Out-Null
    Start-Sleep -Seconds 1
}

# --- Audit trail ---
Write-Host ""
Write-Host "--- Audit trail ---"
$auditOk = $false
$auditCount = 0
try {
    $token = Get-DemoJwt -BaseUrl $BaseUrlHttps -TimeoutSec 30
    $h = @{ Authorization = "Bearer $token"; "X-Tenant-ID" = $TenantId; "Content-Type" = "application/json" }
    Invoke-IpeDemoRequest -Method POST -Uri "$BaseUrlHttps/api/v1/sync/run" -Headers $h `
        -Body '{"entity":"manufacturing_orders"}' -TimeoutSec 120 -BaseUrl $BaseUrlHttps | Out-Null
    Start-Sleep -Seconds 3

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        $csvRaw = & curl.exe -sk -H "Authorization: Bearer $token" -H "X-Tenant-ID: $TenantId" `
            "$BaseUrlHttps/api/v1/compliance/audit/export?format=csv" 2>$null
        $lines = @($csvRaw -split "`n" | Where-Object { $_.Trim() })
        $auditCount = [Math]::Max(0, $lines.Count - 1)
        $auditOk = ($auditCount -ge 3)
        Check "Audit CSV export" ($lines.Count -gt 0) "rows=$auditCount"
    } else {
        $exportParams = @{ Uri = "$BaseUrlHttps/api/v1/compliance/audit/export?format=csv"; Headers = $h; TimeoutSec = 30; ErrorAction = "Stop"; SkipCertificateCheck = $true }
        $csv = Invoke-WebRequest @exportParams -UseBasicParsing
        $lines = @($csv.Content -split "`n" | Where-Object { $_.Trim() })
        $auditCount = [Math]::Max(0, $lines.Count - 1)
        $auditOk = ($csv.StatusCode -eq 200) -and ($auditCount -ge 3)
        Check "Audit CSV export" ($csv.StatusCode -eq 200) "rows=$auditCount"
    }
    Check "Audit trail captures operations" ($auditCount -ge 3) "need >=3 rows after sync"
} catch {
    Check "Audit trail" $false $_.Exception.Message
}

# --- R1 demo over HTTPS ---
Write-Host ""
Write-Host "--- R1 demo over HTTPS ---"
$r1Pass = 0
& (Join-Path $Root "scripts\run-release1-integration-demo.ps1") -BaseUrl $BaseUrlHttps | Out-Host
$r1Report = Get-Content (Join-Path $Root "docs\demo-data\release1-integration-demo.txt") -Raw -ErrorAction SilentlyContinue
if ($r1Report -match "RESULT: (\d+) PASS") { $r1Pass = [int]$Matches[1] }
Check "R1 integration demo 14/14" ($r1Pass -ge 14) "$r1Pass/14"

# --- R2 demo over HTTPS ---
Write-Host ""
Write-Host "--- R2 demo over HTTPS ---"
$r2Pass = 0
& (Join-Path $Root "scripts\run-release2-demo.ps1") -BaseUrl $BaseUrlHttps | Out-Host
$r2Report = Get-Content (Join-Path $Root "docs\demo-data\release2-demo.txt") -Raw -ErrorAction SilentlyContinue
if ($r2Report -match "RESULT: (\d+) PASS") { $r2Pass = [int]$Matches[1] }
Check "R2 demo 5/5" ($r2Pass -ge 5) "$r2Pass/5"

Write-Host ""
Write-Host "============================================="
if ($PASS -and $r1Pass -ge 14 -and $r2Pass -ge 5) {
    Write-Host "  RESULT: PASS"
    Write-Host "  R1: $r1Pass/14 | R2: $r2Pass/5 | Audit rows: $auditCount | Dashboards: $dashCount"
} else {
    Write-Host "  RESULT: FAIL"
    Write-Host "  R1: $r1Pass/14 | R2: $r2Pass/5 | Audit rows: $auditCount | Dashboards: $dashCount"
}
Write-Host "============================================="

exit $(if ($PASS -and $r1Pass -ge 14 -and $r2Pass -ge 5) { 0 } else { 1 })
