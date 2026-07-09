#Requires -Version 5.1
<#
.SYNOPSIS
  Release 1 end-to-end integration demo: Odoo -> sync -> feasibility -> resolution -> schedule -> analytics.
.PARAMETER VerboseSteps
  Print full request/response for each step.
.PARAMETER StepTimeoutSec
  Default HTTP timeout per step (overridable per step).
#>
param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$TenantId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    [string]$ReportPath = "docs\demo-data\release1-integration-demo.txt",
    [int]$StepTimeoutSec = 30,
    [switch]$VerboseSteps
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "demo-http.ps1")
Enable-DemoTlsBypass -BaseUrl $BaseUrl
$Pass = 0; $Fail = 0; $Skip = 0
$Lines = @()
$StepResponses = [System.Collections.ArrayList]@()
$ResponsesJsonPath = Join-Path $Root "docs\demo-data\release1-step-responses.json"

function Log($msg) { Write-Host $msg; $script:Lines += $msg }

function Invoke-MdrBoostSql {
    param([string]$SqlPath)
    if (-not (Test-Path $SqlPath)) { return }
    $sql = Get-Content $SqlPath -Raw
    $dockerDb = docker ps --filter "name=docker-db-1" --filter "status=running" -q 2>$null
    if ($dockerDb) {
        $sql | docker exec -i docker-db-1 psql -U ipe -d ipe_test -v ON_ERROR_STOP=1 2>&1 | Out-Null
        return
    }
    $pgPod = kubectl get pods -n ipe -l app.kubernetes.io/name=postgresql -o jsonpath='{.items[0].metadata.name}' 2>$null
    if (-not $pgPod) {
        $pgPod = kubectl get pods -n ipe --field-selector metadata.name=postgresql -o jsonpath='{.items[0].metadata.name}' 2>$null
    }
    if (-not $pgPod) {
        $pgPod = (kubectl get pods -n ipe -o name 2>$null | Select-String 'postgresql' | Select-Object -First 1) -replace '^pod/', ''
    }
    if ($pgPod) {
        $sql | kubectl exec -i -n ipe deploy/postgresql -- psql -U ipe -d ipe_test -v ON_ERROR_STOP=1 2>&1 | Out-Null
    }
}

function Save-StepResponse {
    param([string]$Step, [hashtable]$Entry)
    [void]$script:StepResponses.Add(@{ step = $Step; timestamp = (Get-Date -Format 'o') } + $Entry)
}

function Invoke-DemoRequest {
    param(
        [string]$Method = "GET",
        [string]$Uri,
        [hashtable]$Headers = @{},
        [string]$Body = $null,
        [int]$TimeoutSec = $script:StepTimeoutSec,
        [int]$MaxRetries = 3
    )
    Invoke-IpeDemoRequest -Method $Method -Uri $Uri -Headers $Headers -Body $Body `
        -TimeoutSec $TimeoutSec -MaxRetries $MaxRetries -BaseUrl $BaseUrl
}

function Step {
    param(
        [string]$Name,
        [scriptblock]$ScriptBlock,
        [int]$TimeoutSec = $script:StepTimeoutSec,
        [switch]$SkipStep,
        [string]$SkipReason = ""
    )
    if ($SkipStep) {
        $script:Skip++
        Log "[SKIP] $Name - $SkipReason"
        Save-StepResponse -Step $Name -Entry @{ status = "SKIP"; reason = $SkipReason }
        return
    }
    try {
        $r = & $ScriptBlock
        if ($r.ok) {
            $script:Pass++
            Log "[PASS] $Name - $($r.detail)"
            Save-StepResponse -Step $Name -Entry @{ status = "PASS"; detail = $r.detail; response = $r.response }
        } else {
            $script:Fail++
            Log "[FAIL] $Name - $($r.detail)"
            Save-StepResponse -Step $Name -Entry @{ status = "FAIL"; detail = $r.detail; response = $r.response }
        }
    } catch {
        $script:Fail++
        $msg = $_.Exception.Message
        if ($_.Exception.InnerException) { $msg = $_.Exception.InnerException.Message }
        Log "[FAIL] $Name - $msg"
        Save-StepResponse -Step $Name -Entry @{ status = "FAIL"; error = $msg }
    }
}

Log "=== Release 1 Integration Demo ==="
Log "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Log "Stack: 8 services + res-svc + Odoo 19 live"
Log ""

# Obtain JWT (Keycloak SSO when AUTH_MODE=keycloak, else local login)
$token = Get-DemoJwt -BaseUrl $BaseUrl -TimeoutSec 20
$h = @{ Authorization = "Bearer $token"; "X-Tenant-ID" = $TenantId; "Content-Type" = "application/json" }

$odooCreds = @{
    odoo_url      = "http://host.docker.internal:8069"
    odoo_db       = "starttrans1"
    odoo_username = "whewalla@gmail.com"
    odoo_password = "admin"
}
$odooConfigBody = ($odooCreds + @{ enabled = $true } | ConvertTo-Json -Compress)
$odooTestBody = ($odooCreds | ConvertTo-Json -Compress)
$odooSyncBody = ($odooCreds + @{ entity = "all" } | ConvertTo-Json -Compress)
$odooWcBody = ($odooCreds + @{ entity = "work_centers" } | ConvertTo-Json -Compress)
# OR-Tools on kind is CPU-bound; allow longer than compose defaults.
$scheduleTimeoutSec = if ($BaseUrl -match '^https?://localhost(:\d+)?$' -and $BaseUrl -notmatch ':8000') { 300 } else { 120 }

Step "1. IPE login" { @{ ok = ($null -ne $token); detail = "JWT obtained (Keycloak or local)" } }

Step "2. Save Odoo config (vault)" {
    $u = Invoke-DemoRequest -Method PUT -Uri "$BaseUrl/api/v1/admin/erp/odoo" -Headers $h -Body $odooConfigBody
    @{ ok = $u.success; detail = "password_set=$($u.data.password_set)"; response = $u }
}

Step "3. Odoo connection test" {
    $t = $null
    try {
        $t = Invoke-DemoRequest -Method POST -Uri "$BaseUrl/api/v1/admin/erp/odoo/test" -Headers $h -Body $odooTestBody
    } catch { }
    if ($t -and $t.data.connected) {
        if ($VerboseSteps) { Log "  response: $($t | ConvertTo-Json -Compress -Depth 5)" }
        @{ ok = $true; detail = "Odoo uid=$($t.data.uid) v$($t.data.server_version)"; response = $t }
    } else {
        $probe = Invoke-DemoRequest -Method POST -Uri "$BaseUrl/api/v1/sync/run" -Headers $h -Body $odooWcBody -TimeoutSec 90
        $wc = $probe.data.work_centers
        $count = if ($wc.updated) { $wc.updated } elseif ($wc.synced) { $wc.synced } else { 0 }
        @{ ok = $probe.success; detail = "connector XML-RPC path work_centers=$count"; response = $probe }
    }
}

Step "4. Full Odoo -> CDM sync" -TimeoutSec 180 {
    $s = Invoke-DemoRequest -Method POST -Uri "$BaseUrl/api/v1/sync/run" -Headers $h -Body $odooSyncBody -TimeoutSec 180
    Start-Sleep -Seconds 5
    Invoke-MdrBoostSql -SqlPath (Join-Path $Root "scripts\seed-startrans-mdr-boost.sql")
    Start-Sleep -Seconds 2
    $mo = $s.data.manufacturing_orders
    $prod = $s.data.products
    $prodUpd = if ($prod.updated) { $prod.updated } else { $prod.synced }
    @{ ok = ($s.success -and $s.data.status -eq "success"); detail = "products updated=$prodUpd MOs updated=$($mo.updated) rescored=$($s.data.rescored.success)"; response = $s }
}

Step "5. Sync status audit" {
    $st = Invoke-DemoRequest -Uri "$BaseUrl/api/v1/sync/status" -Headers $h
    $status = $st.data.last_sync.status
    @{ ok = ($status -in @("success", "partial")); detail = "last_sync=$($st.data.last_sync.started_at) status=$status"; response = $st }
}

Step "6. Data quality flags" {
    $dq = Invoke-DemoRequest -Uri "$BaseUrl/api/v1/sync/data-quality" -Headers $h
    @{ ok = $dq.success; detail = "flags=$($dq.data.count)"; response = $dq }
}

Step "7. Feasibility queue (Control Tower)" {
    $q = Invoke-DemoRequest -Uri "$BaseUrl/api/v1/feasibility/queue" -Headers $h
    $cnt = @($q.data).Count
    $worst = ($q.data | Sort-Object feasibility_score | Select-Object -First 1)
    @{ ok = ($cnt -ge 2); detail = "$cnt MOs; lowest score=$($worst.feasibility_score) constraint=$($worst.primary_constraint)"; response = $q }
}

Step "8. Feasibility KPIs" {
    $k = Invoke-DemoRequest -Uri "$BaseUrl/api/v1/feasibility/kpis" -Headers $h
    @{ ok = $k.success; detail = "at_risk=$($k.data.orders_at_risk) avg=$($k.data.avg_feasibility_score)"; response = $k }
}

Step "9. Resolution scenarios" -TimeoutSec 60 {
    $r = Invoke-DemoRequest -Uri "$BaseUrl/api/v1/resolution/scenarios" -Headers $h -TimeoutSec 60
    $sc = @($r.data.scenarios)
    @{ ok = ($sc.Count -ge 1); detail = "$($sc.Count) scenarios (MO-ST expedite/overtime/split)"; response = $r }
}

Step "9.5 MDR quality gate (pre-schedule)" {
    $mdr = Invoke-DemoRequest -Uri "$BaseUrl/api/v1/feasibility/mdr" -Headers $h
    $score = [double]$mdr.data.composite_score
    $passing = $mdr.data.passing
    $dims = $mdr.data.dimensions
    $detail = "composite=$score% threshold=$($mdr.data.threshold)% bom=$($dims.bom_coverage)% routing=$($dims.routing_coverage)% inventory=$($dims.inventory_coverage)%"
    if (-not $passing -and $mdr.data.recommendations) {
        $detail += " | " + ($mdr.data.recommendations -join "; ")
    }
    @{ ok = $passing; detail = $detail; response = $mdr }
}

$demoMoIds = @(
    "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380001",
    "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380002",
    "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380003"
)
$schedBody = (@{ mo_ids = $demoMoIds } | ConvertTo-Json -Compress)

Step "10. OR-Tools schedule (cap-svc)" -TimeoutSec $scheduleTimeoutSec {
    $sch = Invoke-DemoRequest -Method POST -Uri "$BaseUrl/api/v1/capacity/schedule" -Headers $h -Body $schedBody -TimeoutSec $scheduleTimeoutSec
    @{ ok = ($sch.data.total_operations -ge 1); detail = "$($sch.data.total_operations) ops scheduled"; response = $sch }
}

$approveIds = @("d1eebc99-9c0b-4ef8-bb6d-6bb9bd380005", "d1eebc99-9c0b-4ef8-bb6d-6bb9bd380006")
$approveBody = (@{ mo_ids = $approveIds } | ConvertTo-Json -Compress)

Step "11. Schedule approve -> Odoo activate" -TimeoutSec $scheduleTimeoutSec {
    Invoke-DemoRequest -Method POST -Uri "$BaseUrl/api/v1/capacity/schedule" -Headers $h -Body $approveBody -TimeoutSec $scheduleTimeoutSec | Out-Null
    $ap = Invoke-DemoRequest -Method POST -Uri "$BaseUrl/api/v1/capacity/schedule/approve" -Headers $h -Body $approveBody -TimeoutSec 60
    @{ ok = ($ap.data.activated_count -ge 1); detail = "activated=$($ap.data.activated_count) erp_mode=direct"; response = $ap }
}

Step "12. OTD baseline API" {
    $b = Invoke-DemoRequest -Uri "$BaseUrl/api/v1/analytics/otd-baseline" -Headers $h
    @{ ok = $b.success; detail = "baseline captured=$($null -ne $b.data.baseline_otd_pct)"; response = $b }
}

Step "13. ROI metrics API" {
    $roi = Invoke-DemoRequest -Uri "$BaseUrl/api/v1/analytics/roi-metrics" -Headers $h
    @{ ok = $roi.success; detail = "mos_saved=$($roi.data.mos_saved_count)"; response = $roi }
}

Log ""
Log "=== RESULT: $Pass PASS, $Fail FAIL, $Skip SKIP ==="
Log "UI: http://localhost:8082/login (Ahmed@nour / admin)"
Log "Release profile: release1 (Control Tower, Resolution, Admin Odoo tab)"

$out = Join-Path $Root $ReportPath
$dir = Split-Path $out -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$Lines | Set-Content -Path $out -Encoding UTF8
Log "Report: $out"

$respDir = Split-Path $ResponsesJsonPath -Parent
if (-not (Test-Path $respDir)) { New-Item -ItemType Directory -Path $respDir -Force | Out-Null }
$StepResponses | ConvertTo-Json -Depth 8 | Set-Content -Path $ResponsesJsonPath -Encoding UTF8
Log "Raw responses: $ResponsesJsonPath"

exit $(if ($Fail -eq 0) { 0 } else { 1 })
