#Requires -Version 5.1
<#
.SYNOPSIS
  Smoke test Release 2 stack — R1 APIs + nlp/demand/scenario health and Kong routes.
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

function Assert-Health($name, $url) {
    try {
        $r = Invoke-RestMethod -Uri $url -TimeoutSec 10
        Assert $name ($r.status -eq "ok" -or $r.status -eq "degraded")
    } catch {
        Assert $name $false
    }
}

Write-Host "=== Release 2 smoke test ===" -ForegroundColor Cyan

# Direct container health (R2 services)
Assert-Health "nlp-svc container" "http://localhost:8007/api/v1/health"
Assert-Health "demand-svc container" "http://localhost:8040/api/v1/health"
Assert-Health "scenario-svc container" "http://localhost:8050/api/v1/health"

# R1 core containers (direct)
Assert-Health "dpe-svc container" "http://localhost:8020/api/v1/health"
Assert-Health "fea-svc container" "http://localhost:8004/api/v1/health"
Assert-Health "res-svc container" "http://localhost:8005/api/v1/health"
Assert-Health "cap-svc container" "http://localhost:8003/api/v1/health"
Assert-Health "connector container" "http://localhost:8016/api/v1/health"

try {
    $loginBody = @{ email = $Email; password = $Password } | ConvertTo-Json
    $login = Invoke-RestMethod -Method POST -Uri "$BaseUrl/api/v1/auth/login" -Body $loginBody -ContentType "application/json"
    $token = $login.data.access_token
    Assert "Login via Kong" ($null -ne $token)
} catch {
    Assert "Login via Kong" $false
    Write-Host $_.Exception.Message
    Write-Host "`nResult: $pass passed, $fail failed" -ForegroundColor Yellow
    exit 1
}

$headers = @{
    Authorization = "Bearer $token"
    "X-Tenant-ID" = $TenantId
}

try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/api/v1/health" -Headers $headers
    Assert "Kong health" ($health.status -eq "ok")
} catch { Assert "Kong health" $false }

try {
    $sync = Invoke-RestMethod -Uri "$BaseUrl/api/v1/sync/status" -Headers $headers
    Assert "Sync status (R1)" ($sync.success -eq $true)
} catch { Assert "Sync status (R1)" $false }

try {
    $queue = Invoke-RestMethod -Uri "$BaseUrl/api/v1/feasibility/queue" -Headers $headers
    Assert "Feasibility queue (R1)" ($queue.success -eq $true)
} catch { Assert "Feasibility queue (R1)" $false }

try {
    $nlp = Invoke-RestMethod -Uri "http://localhost:8007/api/v1/health" -Headers $headers
    Assert "nlp-svc authenticated health" ($nlp.status -in @("ok", "degraded"))
} catch { Assert "nlp-svc authenticated health" $false }

try {
    $scenarios = Invoke-RestMethod -Uri "$BaseUrl/api/v1/scenario" -Headers $headers
    Assert "Kong scenario route" ($scenarios.success -eq $true)
} catch { Assert "Kong scenario route" $false }

try {
    $accuracy = Invoke-RestMethod -Uri "$BaseUrl/api/v1/demand/accuracy" -Headers $headers
    Assert "Kong demand route" ($accuracy.success -eq $true)
} catch { Assert "Kong demand route" $false }

Write-Host "`nResult: $pass passed, $fail failed" -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Yellow" })
if ($fail -gt 0) { exit 1 }
