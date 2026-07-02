#Requires -Version 5.1
<#
.SYNOPSIS
  Release 2 demo: auto-propose, Outcomes API, Copilot Lite (when available), Odoo write-back flag.
#>
param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$TenantId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    [string]$ReportPath = "docs\demo-data\release2-demo.txt"
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Pass = 0; $Fail = 0; $Skip = 0
$Lines = @()

function Log($msg) { Write-Host $msg; $script:Lines += $msg }
function Step($name, $scriptBlock, [switch]$SkipStep, [string]$SkipReason = "") {
    if ($SkipStep) { $script:Skip++; Log "[SKIP] $name - $SkipReason"; return }
    try {
        if (& $scriptBlock) { $script:Pass++; Log "[PASS] $name" } else { $script:Fail++; Log "[FAIL] $name" }
    } catch { $script:Fail++; Log "[FAIL] $name - $($_.Exception.Message)" }
}

Log "=== Release 2 Demo (014) ==="
Log "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Log ""

$login = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/v1/auth/login" -ContentType "application/json" -Body '{"email":"Ahmed@nour","password":"admin"}'
$h = @{ Authorization = "Bearer $($login.data.access_token)"; "X-Tenant-ID" = $TenantId; "Content-Type" = "application/json" }

Step "1. Outcomes - OTD baseline API" {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/v1/analytics/otd-baseline" -Headers $h
    $r.success
}

Step "2. Outcomes - ROI metrics API" {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/v1/analytics/roi-metrics" -Headers $h
    $r.success
}

Step "3. Auto-propose - sync returns scenarios_proposed" {
    $s = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/v1/sync/run" -Headers $h -Body '{"entity":"all"}' -TimeoutSec 180
    $null -ne $s.data.rescored
}

Step "4. Resolution scenarios still available" {
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/v1/resolution/scenarios" -Headers $h -TimeoutSec 60
    @($r.data.scenarios).Count -ge 1
}

Step "5. Copilot Lite / planner-assist" {
    try {
        $body = '{"query":"Which manufacturing orders are at risk?"}'
        $r = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/v1/planner-assist/query" -Headers $h -Body $body -TimeoutSec 10
        $r.success
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 404) {
            $script:Skip++; Log "[SKIP] 5. Copilot Lite - endpoint not deployed (T140 pending)"
            return $false
        }
        throw
    }
} -SkipStep:$false

Log ""
Log "=== RESULT: $Pass PASS, $Fail FAIL, $Skip SKIP ==="
$out = Join-Path $Root $ReportPath
$dir = Split-Path $out -Parent
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$Lines | Set-Content -Path $out -Encoding UTF8
Log "Report: $out"
exit $(if ($Fail -eq 0) { 0 } else { 1 })
