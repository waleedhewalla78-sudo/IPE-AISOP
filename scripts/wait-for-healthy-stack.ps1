# Waits for IPE stack health via Kong before demo or CI gates.
# Usage: .\scripts\wait-for-healthy-stack.ps1 [-BaseUrl http://localhost:8000] [-MaxWaitSeconds 120]

param(
    [string]$BaseUrl = "http://localhost:8000",
    [int]$MaxWaitSeconds = 120
)

$ErrorActionPreference = "Stop"
$Tenant = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
$loginBody = '{"email":"Ahmed@nour","password":"admin"}'

Write-Host "Waiting for IPE stack at $BaseUrl (max ${MaxWaitSeconds}s)..."

$elapsed = 0
while ($elapsed -lt $MaxWaitSeconds) {
    try {
        $login = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method POST `
            -ContentType "application/json" -Body $loginBody -TimeoutSec 10
        if (-not $login.success) { throw "Login not successful" }
        $token = $login.data.access_token
        $h = @{
            Authorization = "Bearer $token"
            "X-Tenant-ID" = $Tenant
        }
        $checks = @(
            "$BaseUrl/api/v1/demand/forecast?horizon=short",
            "$BaseUrl/api/v1/supply/network",
            "$BaseUrl/api/v1/scenario",
            "$BaseUrl/api/v1/copilot/agents",
            "$BaseUrl/api/v1/sustainability/dashboard",
            "$BaseUrl/api/v1/quality-events/dashboard"
        )
        $ok = $true
        foreach ($url in $checks) {
            $r = Invoke-WebRequest -Uri $url -Headers $h -TimeoutSec 10 -UseBasicParsing
            if ($r.StatusCode -ne 200) { $ok = $false; break }
        }
        if ($ok) {
            Write-Host "All services healthy after ${elapsed}s"
            exit 0
        }
    } catch {
        # Kong or upstream still starting
    }
    Start-Sleep -Seconds 3
    $elapsed += 3
}

Write-Host "Timeout - stack not healthy after ${MaxWaitSeconds}s"
exit 1
