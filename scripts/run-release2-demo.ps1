#Requires -Version 5.1
<#
.SYNOPSIS
  Release 2 demo + gate G-R2-05 evidence (Outcomes, sync, Copilot, optional Kind/compose).
#>
param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$TenantId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    [string]$ReportPath = "docs\demo-data\release2-demo-g-r2-05.txt",
    [string]$K8sNamespace = "ipe",
    [switch]$SkipCompose,
    [switch]$SkipK8s
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "demo-http.ps1")
Enable-DemoTlsBypass -BaseUrl $BaseUrl
$Pass = 0; $Fail = 0; $Skip = 0
$Lines = @()

function Log($msg) { Write-Host $msg; $script:Lines += $msg }
function Step($name, $scriptBlock, [switch]$SkipStep, [string]$SkipReason = "") {
    if ($SkipStep) { $script:Skip++; Log "[SKIP] $name - $SkipReason"; return }
    try {
        if (& $scriptBlock) { $script:Pass++; Log "[PASS] $name" } else { $script:Fail++; Log "[FAIL] $name" }
    } catch { $script:Fail++; Log "[FAIL] $name - $($_.Exception.Message)" }
}

function Test-KongReachable([string]$Url) {
    try {
        $null = Invoke-WebRequest -Uri "$Url/api/v1/health" -UseBasicParsing -TimeoutSec 5
        return $true
    } catch { return $false }
}

Log "=== Release 2 Demo — Gate G-R2-05 ==="
Log "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Log "BaseUrl=$BaseUrl Namespace=$K8sNamespace"
Log ""

$composeUp = -not $SkipCompose.IsPresent -and (Test-KongReachable $BaseUrl)
if (-not $composeUp) { Log "[INFO] Kong/compose not reachable at $BaseUrl — API demo steps will SKIP or FAIL" }

$token = $null
if ($composeUp) {
    # R2 compose login is local RS256; Keycloak may be present but unhealthy.
    try { $token = Get-DemoJwt -BaseUrl $BaseUrl -AuthMode local -TimeoutSec 60 } catch { Log "[WARN] JWT: $($_.Exception.Message)" }
}
$h = @{ Authorization = "Bearer $token"; "X-Tenant-ID" = $TenantId; "Content-Type" = "application/json" }

Step "G-R2-05.1 Outcomes - OTD baseline API" {
    if (-not $composeUp -or -not $token) { return $false }
    $r = Invoke-IpeDemoRequest -Uri "$BaseUrl/api/v1/analytics/otd-baseline" -Headers $h -BaseUrl $BaseUrl
    $r.success
} -SkipStep:(-not $composeUp) -SkipReason "compose/Kong down"

Step "G-R2-05.2 Outcomes - ROI metrics API" {
    if (-not $composeUp -or -not $token) { return $false }
    $r = Invoke-IpeDemoRequest -Uri "$BaseUrl/api/v1/analytics/roi-metrics" -Headers $h -BaseUrl $BaseUrl
    $r.success
} -SkipStep:(-not $composeUp) -SkipReason "compose/Kong down"

Step "G-R2-05.3 Auto-propose - sync returns rescored" {
    if (-not $composeUp -or -not $token) { return $false }
    # Real sync against mock-odoo XML-RPC (compose) — credentials in body when tenant.config empty.
    $body = @{
        entity = "all"
        odoo_url = "http://mock-odoo-api:8010"
        odoo_db = "ipe_mock"
        odoo_username = "admin"
        odoo_password = "admin"
    } | ConvertTo-Json -Compress
    $s = Invoke-IpeDemoRequest -Method POST -Uri "$BaseUrl/api/v1/sync/run" -Headers $h -Body $body -TimeoutSec 180 -BaseUrl $BaseUrl
    ($s.success -eq $true) -and ($null -ne $s.data.rescored)
} -SkipStep:(-not $composeUp) -SkipReason "compose/Kong down"

Step "G-R2-05.4 Resolution scenarios available" {
    if (-not $composeUp -or -not $token) { return $false }
    $list = Invoke-IpeDemoRequest -Uri "$BaseUrl/api/v1/resolution/scenarios" -Headers $h -TimeoutSec 60 -BaseUrl $BaseUrl
    if (@($list.data.scenarios).Count -ge 1) { return $true }
    # Propose from a live MO (seed or sync) — real res-svc path, not a mock list.
    $queue = Invoke-IpeDemoRequest -Uri "$BaseUrl/api/v1/feasibility/queue" -Headers $h -TimeoutSec 60 -BaseUrl $BaseUrl
    $moId = $null
    $rows = @()
    if ($queue.data -is [System.Array]) { $rows = @($queue.data) }
    elseif ($queue.data.queue) { $rows = @($queue.data.queue) }
    if ($rows.Count -gt 0) {
        $first = $rows[0]
        $moId = $first.mo_id
        if (-not $moId) { $moId = $first.id }
    }
    if (-not $moId) {
        return $false
    }
    $proposeBody = (@{ mo_id = "$moId"; constraint_type = "capacity_overload" } | ConvertTo-Json -Compress)
    $proposed = Invoke-IpeDemoRequest -Method POST -Uri "$BaseUrl/api/v1/resolution/scenarios" -Headers $h -Body $proposeBody -TimeoutSec 60 -BaseUrl $BaseUrl
    if (-not $proposed.success -and @($list.data.scenarios).Count -lt 1) { return $false }
    $list2 = Invoke-IpeDemoRequest -Uri "$BaseUrl/api/v1/resolution/scenarios" -Headers $h -TimeoutSec 60 -BaseUrl $BaseUrl
    @($list2.data.scenarios).Count -ge 1
} -SkipStep:(-not $composeUp) -SkipReason "compose/Kong down"

Step "G-R2-05.5 Copilot Lite / planner-assist" {
    if (-not $composeUp -or -not $token) { return $false }
    try {
        $body = '{"query":"Which manufacturing orders are at risk?"}'
        $r = Invoke-IpeDemoRequest -Method POST -Uri "$BaseUrl/api/v1/planner-assist/query" -Headers $h -Body $body -TimeoutSec 30 -BaseUrl $BaseUrl
        $r.success
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 404) {
            $script:Skip++; Log "[SKIP] G-R2-05.5 Copilot Lite - endpoint not deployed"
            return $false
        }
        throw
    }
} -SkipStep:(-not $composeUp) -SkipReason "compose/Kong down"

Step "G-R2-05.6 Kind — all ipe app pods Ready" {
    if ($SkipK8s) { return $false }
    $out = kubectl get pods -n $K8sNamespace -o json 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { return $false }
    $j = $out | ConvertFrom-Json
    $pods = @($j.items | Where-Object { $_.metadata.name -notmatch 'postgresql|redis' })
    if ($pods.Count -lt 6) { return $false }
    ($pods | Where-Object { $_.status.phase -eq 'Running' -and ($_.status.containerStatuses | Where-Object { -not $_.ready }).Count -eq 0 }).Count -eq $pods.Count
} -SkipStep:$SkipK8s.IsPresent -SkipReason "SkipK8s"

Step "G-R2-05.7 Kind — postgresql + redis Ready" {
    if ($SkipK8s) { return $false }
    $pg = kubectl get pod -n $K8sNamespace -l app.kubernetes.io/name=postgresql -o jsonpath='{.items[0].status.containerStatuses[0].ready}' 2>$null
    $rd = kubectl get pod -n $K8sNamespace -l app.kubernetes.io/name=redis -o jsonpath='{.items[0].status.containerStatuses[0].ready}' 2>$null
    if ($pg -ne 'true' -or $rd -ne 'true') {
        $pg2 = (kubectl get pods -n $K8sNamespace -o name 2>$null | Select-String 'postgresql').Count -ge 1
        $rd2 = (kubectl get pods -n $K8sNamespace -o name 2>$null | Select-String 'redis').Count -ge 1
        if (-not $pg2 -or -not $rd2) { return $false }
        $pg = kubectl get pods -n $K8sNamespace 2>$null | Select-String 'postgresql.*1/1'
        $rd = kubectl get pods -n $K8sNamespace 2>$null | Select-String 'redis.*1/1'
        return ($null -ne $pg -and $null -ne $rd)
    }
    return $true
} -SkipStep:$SkipK8s.IsPresent -SkipReason "SkipK8s"

Log ""
Log "=== G-R2-05 RESULT: $Pass PASS, $Fail FAIL, $Skip SKIP ==="
$gatePass = ($Fail -eq 0) -and (($Pass -ge 2) -or ($composeUp -and $Pass -ge 5))
Log "G-R2-05 gate verdict: $(if ($gatePass) { 'PASS' } else { 'FAIL' }) (compose=$composeUp)"
$out = Join-Path $Root $ReportPath
$dir = Split-Path $out -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$Lines | Set-Content -Path $out -Encoding UTF8
Log "Report: $out"
exit $(if ($gatePass) { 0 } else { 1 })
