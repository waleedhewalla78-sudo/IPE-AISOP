#Requires -Version 5.1
<#
.SYNOPSIS
  Smoke test Release 1 APIs after deploy.
#>
param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$TenantId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    [string]$Email = "Ahmed@nour",
    [string]$Password = "admin"
)

$ErrorActionPreference = "Stop"
$pass = 0
$fail = 0

function Assert($name, $cond) {
    if ($cond) { Write-Host "[PASS] $name" -ForegroundColor Green; $script:pass++ }
    else { Write-Host "[FAIL] $name" -ForegroundColor Red; $script:fail++ }
}

Write-Host "=== Release 1 smoke test ===" -ForegroundColor Cyan

try {
    $loginBody = @{ email = $Email; password = $Password } | ConvertTo-Json
    $login = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/v1/auth/login" -Body $loginBody -ContentType "application/json"
    $token = $login.data.access_token
    Assert "Login" ($null -ne $token)
} catch {
    Assert "Login" $false
    Write-Host $_.Exception.Message
    exit 1
}

$headers = @{
    Authorization = "Bearer $token"
    "X-Tenant-ID" = $TenantId
}

try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/api/v1/health" -Headers $headers
    Assert "Health" ($health.status -eq "ok")
} catch { Assert "Health" $false }

try {
    $sync = Invoke-RestMethod -Uri "$BaseUrl/api/v1/sync/status" -Headers $headers
    Assert "Sync status endpoint" ($sync.success -eq $true)
} catch { Assert "Sync status endpoint" $false }

try {
    $queue = Invoke-RestMethod -Uri "$BaseUrl/api/v1/feasibility/queue" -Headers $headers
    Assert "Feasibility queue" ($queue.success -eq $true)
} catch { Assert "Feasibility queue" $false }

try {
    $kpis = Invoke-RestMethod -Uri "$BaseUrl/api/v1/feasibility/kpis" -Headers $headers
    Assert "Feasibility KPIs" ($kpis.success -eq $true)
} catch { Assert "Feasibility KPIs" $false }

try {
    $baseline = Invoke-RestMethod -Uri "$BaseUrl/api/v1/analytics/otd-baseline" -Headers $headers
    Assert "OTD baseline endpoint" ($baseline.success -eq $true)
} catch { Assert "OTD baseline endpoint" $false }

try {
    $roi = Invoke-RestMethod -Uri "$BaseUrl/api/v1/analytics/roi-metrics" -Headers $headers
    Assert "ROI metrics endpoint" ($roi.success -eq $true)
} catch { Assert "ROI metrics endpoint" $false }

Write-Host "`nResult: $pass passed, $fail failed" -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Yellow" })
if ($fail -gt 0) { exit 1 }
