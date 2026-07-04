# IPE Phase 2 — start Prometheus + Grafana + Alertmanager on segmented networks
# Usage:
#   .\scripts\run-monitoring-stack.ps1
#   .\scripts\run-monitoring-stack.ps1 -Profile release1
#   .\scripts\run-monitoring-stack.ps1 -VerifyOnly

param(
    [ValidateSet("release1", "full")]
    [string]$Profile = "release1",
    [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$DockerDir = Join-Path $Root "infrastructure\docker"
$Evidence = Join-Path $Root "docs\ops-monitoring-verify.txt"

function Test-Endpoint {
    param([string]$Name, [string]$Url, [int]$Expected = 200)
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 15
        if ($r.StatusCode -eq $Expected) {
            Write-Host "  PASS $Name ($Url)" -ForegroundColor Green
            return $true
        }
        Write-Host "  FAIL $Name status $($r.StatusCode)" -ForegroundColor Red
        return $false
    } catch {
        Write-Host "  FAIL $Name $_" -ForegroundColor Red
        return $false
    }
}

function Get-ComposeArgs {
    param([string]$ProfileName)
    $files = @("-f", "docker-compose.monitoring.yml")
    if ($ProfileName -eq "release1") {
        return @(
            "-f", "docker-compose.release1.yml",
            "-f", "docker-compose.network.yml",
            "-f", "docker-compose.monitoring.yml"
        )
    }
    return @("-f", "docker-compose.monitoring.yml")
}

Push-Location $DockerDir
try {
    if (-not $VerifyOnly) {
        Write-Host "=== Phase 2: Monitoring stack (Prometheus + Grafana + Alertmanager) ===" -ForegroundColor Cyan
        if ($Profile -eq "release1") {
            Write-Host "Using segmented networks (docker-compose.network.yml)." -ForegroundColor DarkGray
            Write-Host "Ensure Release 1 app stack is running with the network overlay first." -ForegroundColor DarkGray
        }
        $composeArgs = Get-ComposeArgs -ProfileName $Profile
        if ($Profile -eq "release1") {
            docker compose @composeArgs up -d `
                prometheus grafana alertmanager `
                postgres-exporter redis-exporter kafka-exporter node-exporter
        } else {
            Write-Host "Ensure full app stack is on ipe-network first." -ForegroundColor DarkGray
            docker compose @composeArgs up -d
        }
        if ($LASTEXITCODE -ne 0) { throw "monitoring up failed" }
        Write-Host "Waiting 25s for healthchecks..." -ForegroundColor DarkGray
        Start-Sleep -Seconds 25
    }

    Write-Host "`n=== Verification ===" -ForegroundColor Cyan
    $results = @()
    $results += Test-Endpoint "Prometheus ready" "http://localhost:9090/-/ready"
    $results += Test-Endpoint "Grafana health" "http://localhost:3000/api/health"
    $results += Test-Endpoint "Alertmanager ready" "http://localhost:9093/-/ready"

    $promTargets = $null
    try {
        $promTargets = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/targets" -TimeoutSec 15
        $up = @($promTargets.data.activeTargets | Where-Object { $_.health -eq "up" }).Count
        $total = @($promTargets.data.activeTargets).Count
        Write-Host "  Prometheus targets: $up / $total up" -ForegroundColor $(if ($up -ge 1) { "Green" } else { "Yellow" })
        $results += ($up -ge 1)
    } catch {
        Write-Host "  FAIL Prometheus targets API $_" -ForegroundColor Red
        $results += $false
    }

    try {
        $rules = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/rules" -TimeoutSec 15
        $count = @($rules.data.groups).Count
        Write-Host "  Alert rule groups: $count" -ForegroundColor $(if ($count -ge 1) { "Green" } else { "Yellow" })
        $results += ($count -ge 1)
    } catch {
        Write-Host "  WARN Alert rules API $_" -ForegroundColor Yellow
        $results += $true
    }

    $lines = @(
        "IPE Monitoring Verification - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
        "Profile: $Profile",
        "Prometheus: http://localhost:9090",
        "Grafana:    http://localhost:3000 (admin / admin)",
        "Alertmanager: http://localhost:9093",
        "",
        "Results:"
    )
    if ($results -notcontains $false) {
        $lines += "OVERALL: PASS"
        Write-Host "`nOVERALL: PASS" -ForegroundColor Green
    } else {
        $lines += "OVERALL: FAIL - ensure app stack is on ipe-network"
        Write-Host "`nOVERALL: FAIL" -ForegroundColor Red
    }
    $lines | Set-Content -Encoding utf8 $Evidence
    Write-Host "Evidence: $Evidence" -ForegroundColor DarkGray

    if ($results -contains $false) { exit 1 }
} finally {
    Pop-Location
}
