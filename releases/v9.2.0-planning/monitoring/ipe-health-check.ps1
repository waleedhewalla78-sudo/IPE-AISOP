<#
.SYNOPSIS
  IPE Health Check (Windows) — service /health endpoints + PostgreSQL
.PARAMETER LogPath
  Log file path (default: C:\ipe\logs\health.log)
.PARAMETER ComposeFile
  docker-compose.yml path (default: deploy/star-trans)
.EXAMPLE
  .\ipe-health-check.ps1
  .\ipe-health-check.ps1 -LogPath D:\logs\ipe-health.log
#>
[CmdletBinding()]
param(
    [string]$LogPath = "C:\ipe\logs\health.log",
    [string]$ComposeFile = ""
)

$Services = @(
    @{ Name = "dpe-svc"; Port = 8001 },
    @{ Name = "fea-svc"; Port = 8004 },
    @{ Name = "res-svc"; Port = 8005 },
    @{ Name = "cap-svc"; Port = 8003 },
    @{ Name = "mat-svc"; Port = 8002 },
    @{ Name = "connector"; Port = 8009 }
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ComposeFile) {
    $Candidate = Join-Path $ScriptDir "..\..\deploy\star-trans\docker-compose.yml"
    if (Test-Path $Candidate) { $ComposeFile = (Resolve-Path $Candidate).Path }
    else { $ComposeFile = "docker-compose.yml" }
}

$logDir = Split-Path -Parent $LogPath
if ($logDir -and -not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-HealthLog([string]$Message) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Add-Content -Path $LogPath -Value $line
    Write-Host $line
}

$fail = 0
foreach ($svc in $Services) {
    $ok = $false
    foreach ($path in @("/api/v1/health", "/healthz")) {
        try {
            $uri = "http://localhost:$($svc.Port)$path"
            $resp = Invoke-WebRequest -Uri $uri -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            if ($resp.StatusCode -eq 200) { $ok = $true; break }
        } catch {
            # try next path
        }
    }
    if (-not $ok) {
        Write-HealthLog "WARN: $($svc.Name) unhealthy"
        $fail++
    }
}

try {
    docker compose -f $ComposeFile exec -T db pg_isready -U ipe 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-HealthLog "WARN: PostgreSQL down"
        $fail++
    }
} catch {
    Write-HealthLog "WARN: PostgreSQL check failed — $_"
    $fail++
}

if ($fail -eq 0) {
    Write-HealthLog "OK"
}

if ($env:IPE_HEALTH_WEBHOOK -and $fail -gt 0) {
    try {
        Invoke-RestMethod -Method Post -Uri $env:IPE_HEALTH_WEBHOOK -ContentType "application/json" `
            -Body (@{ text = "IPE health WARN failures=$fail" } | ConvertTo-Json) | Out-Null
    } catch { }
}

exit $fail
