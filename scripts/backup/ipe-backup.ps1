<#
.SYNOPSIS
  IPE Daily PostgreSQL Backup (Windows)
.DESCRIPTION
  Runs pg_dump (custom format) via docker compose, retains 7 days of dumps.
  Compatible with Windows Task Scheduler.
.PARAMETER BackupDir
  Destination folder for .dump files (default: C:\ipe\backups)
.PARAMETER ComposeFile
  Path to docker-compose.yml (default: deploy/star-trans relative to repo)
.EXAMPLE
  .\ipe-backup.ps1
  .\ipe-backup.ps1 -BackupDir D:\backups\ipe
#>
[CmdletBinding()]
param(
    [string]$BackupDir = "C:\ipe\backups",
    [string]$ComposeFile = ""
)

$ErrorActionPreference = "Stop"
$Date = Get-Date -Format "yyyy-MM-dd"
$Filename = "ipe-backup-$Date.dump"
$LogFile = Join-Path $BackupDir "backup.log"
$RetentionDays = 7

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ComposeFile) {
    $Candidate = Join-Path $ScriptDir "..\..\deploy\star-trans\docker-compose.yml"
    if (Test-Path $Candidate) {
        $ComposeFile = (Resolve-Path $Candidate).Path
    } else {
        $ComposeFile = Join-Path (Get-Location) "docker-compose.yml"
    }
}

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

function Write-BackupLog([string]$Message) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Add-Content -Path $LogFile -Value $line
    Write-Host $line
}

Write-BackupLog "Starting backup..."

$OutPath = Join-Path $BackupDir $Filename
try {
    $dump = docker compose -f $ComposeFile exec -T db pg_dump -U ipe -Fc ipe 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump exit code $LASTEXITCODE : $dump"
    }
    [System.IO.File]::WriteAllBytes($OutPath, [byte[]]$dump)
    # Fallback: if docker returned string stream, re-run with redirect
    if (-not (Test-Path $OutPath) -or (Get-Item $OutPath).Length -eq 0) {
        docker compose -f $ComposeFile exec -T db pg_dump -U ipe -Fc ipe | Set-Content -Path $OutPath -AsByteStream -ErrorAction SilentlyContinue
        if (-not (Test-Path $OutPath) -or (Get-Item $OutPath).Length -eq 0) {
            # PowerShell 5.x compatible redirect
            cmd /c "docker compose -f `"$ComposeFile`" exec -T db pg_dump -U ipe -Fc ipe > `"$OutPath`""
        }
    }
    if (-not (Test-Path $OutPath) -or (Get-Item $OutPath).Length -eq 0) {
        throw "Backup file missing or empty: $OutPath"
    }
    $sizeMB = [math]::Round((Get-Item $OutPath).Length / 1MB, 2)
    Write-BackupLog "SUCCESS: $Filename (${sizeMB} MB)"
} catch {
    Write-BackupLog "ERROR: Backup failed — $_"
    exit 1
}

# Cleanup older than retention
$cutoff = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -Path $BackupDir -Filter "ipe-backup-*.dump" -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-BackupLog "Deleted old backup: $($_.Name)"
    }
Write-BackupLog "Cleaned backups older than $RetentionDays days"
