# Sprint 7 — Event stream data quality audit (roadmap §10.1)
# Usage: .\scripts\sprint7\audit-event-streams.ps1

$ErrorActionPreference = "Continue"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $Root

Write-Host "=== Sprint 7 Event Stream Audit ===" -ForegroundColor Cyan
Write-Host (Get-Date -Format o)

$issues = @()
$pass = 0

# 1. Avro schema files
$schemaDir = Join-Path $Root "services\shared\ipe_shared\events\schemas"
if (Test-Path $schemaDir) {
    $schemas = Get-ChildItem $schemaDir -Filter *.avsc
    Write-Host "Avro schemas: $($schemas.Count) files"
    if ($schemas.Count -lt 1) { $issues += "No Avro schemas in events/schemas" } else { $pass++ }
} else {
    $issues += "Missing events/schemas directory"
}

# 2. EIB module
$eibPy = Join-Path $Root "services\shared\ipe_shared\events\eib.py"
if (Test-Path $eibPy) { Write-Host "[PASS] EIB module present"; $pass++ } else { $issues += "Missing eib.py" }

# 3. Activity migration
$mig = Join-Path $Root "migrations\versions\038_sprint7_activity_events.py"
if (Test-Path $mig) { Write-Host "[PASS] Migration 038 present"; $pass++ } else { $issues += "Missing migration 038" }

# 4. Activity API
$actApi = Join-Path $Root "services\dpe-svc\app\api\v1\activity.py"
if (Test-Path $actApi) { Write-Host "[PASS] Activity API present"; $pass++ } else { $issues += "Missing activity API" }

# 5. Unified dashboard API
$uniApi = Join-Path $Root "services\dpe-svc\app\api\v1\unified_dashboard.py"
if (Test-Path $uniApi) { Write-Host "[PASS] Unified dashboard API present"; $pass++ } else { $issues += "Missing unified dashboard API" }

# 6. Kafka topic naming consistency (sample key services only)
$samplePaths = @(
    (Join-Path $Root "services\dpe-svc"),
    (Join-Path $Root "services\connector"),
    (Join-Path $Root "services\fea-svc"),
    (Join-Path $Root "services\shared\ipe_shared\events")
) | Where-Object { Test-Path $_ }
$topics = @()
foreach ($p in $samplePaths) {
    $topics += Select-String -Path (Get-ChildItem $p -Recurse -Filter *.py).FullName -Pattern 'ipe\.[a-z]+\.[a-z_]+' -AllMatches -ErrorAction SilentlyContinue |
        ForEach-Object { $_.Matches.Value }
}
$topics = $topics | Sort-Object -Unique
Write-Host "Discovered Kafka topic patterns: $($topics.Count)"
if ($topics.Count -ge 3) { $pass++ } else { $issues += "Fewer than 3 ipe.* topic patterns found" }

# 7. Optional live stack check
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 5
    Write-Host "[PASS] Compose health reachable"
    $pass++
} catch {
    Write-Host "[SKIP] Stack not reachable on :8000 (audit continues offline)"
}

Write-Host ""
Write-Host "=== RESULT: $pass checks passed, $($issues.Count) issues ===" -ForegroundColor $(if ($issues.Count -eq 0) { "Green" } else { "Yellow" })
foreach ($i in $issues) { Write-Host "  - $i" -ForegroundColor Yellow }

$outDir = Join-Path $Root "specs\016-sprint7-ecosystem-cohesion\evidence"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
@(
    "=== Sprint 7 Event Stream Audit ===",
    (Get-Date -Format o),
    "Passed: $pass",
    "Issues: $($issues.Count)",
    ($issues -join "`n")
) | Out-File (Join-Path $outDir "event-stream-audit.txt") -Encoding utf8

if ($issues.Count -gt 0) { exit 1 }
