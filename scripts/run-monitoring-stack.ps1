# REL-PROD Wave 2D — start Loki + Grafana + Prometheus overlay on demo stack.
# Usage: .\scripts\run-monitoring-stack.ps1
#        .\scripts\run-monitoring-stack.ps1 -VerifyOnly

param(
    [switch]$VerifyOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$DockerDir = Join-Path $Root "infrastructure\docker"
$Compose = @(
    "-f", "docker-compose.yml",
    "-f", "docker-compose.demo.yml",
    "-f", "docker-compose.monitoring.yml"
)
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

Push-Location $DockerDir
try {
    if (-not $VerifyOnly) {
        Write-Host "=== REL-PROD 2D: Monitoring stack ===" -ForegroundColor Cyan
        docker compose @Compose up -d prometheus loki promtail grafana
        if ($LASTEXITCODE -ne 0) { throw "monitoring up failed" }
        Write-Host "Waiting 20s for healthchecks..." -ForegroundColor DarkGray
        Start-Sleep -Seconds 20
    }

    Write-Host "`n=== Verification ===" -ForegroundColor Cyan
    $results = @()
    $results += Test-Endpoint "Prometheus ready" "http://localhost:9091/-/ready"
    $results += Test-Endpoint "Grafana health" "http://localhost:3002/api/health"
    $results += Test-Endpoint "Loki ready" "http://localhost:3100/ready"

    $promTargets = $null
    try {
        $promTargets = Invoke-RestMethod -Uri "http://localhost:9091/api/v1/targets" -TimeoutSec 15
        $up = @($promTargets.data.activeTargets | Where-Object { $_.health -eq "up" }).Count
        $total = @($promTargets.data.activeTargets).Count
        Write-Host "  Prometheus targets: $up / $total up" -ForegroundColor $(if ($up -ge 3) { "Green" } else { "Yellow" })
        $results += ($up -ge 3)
    } catch {
        Write-Host "  FAIL Prometheus targets API $_" -ForegroundColor Red
        $results += $false
    }

    $lines = @(
        "IPE Monitoring Verification — $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
        "Prometheus: http://localhost:9091",
        "Grafana:    http://localhost:3002 (admin / ipe_admin)",
        "Loki:       http://localhost:3100",
        "",
        "Results:"
    )
    if ($results -notcontains $false) {
        $lines += "OVERALL: PASS"
        Write-Host "`nOVERALL: PASS" -ForegroundColor Green
    } else {
        $lines += "OVERALL: FAIL — ensure demo app stack is running first"
        Write-Host "`nOVERALL: FAIL" -ForegroundColor Red
    }
    $lines | Set-Content -Encoding utf8 $Evidence
    Write-Host "Evidence: $Evidence" -ForegroundColor DarkGray

    if ($results -contains $false) { exit 1 }
} finally {
    Pop-Location
}
