# Verify Airflow services in default docker-compose (R4 T043)
param(
    [string]$AirflowUrl = "http://localhost:8080"
)

$ErrorActionPreference = "Continue"
$lines = @("IPE Airflow Verification", "URL: $AirflowUrl", "")

function Test-Line([string]$Name, [scriptblock]$Action) {
    try {
        $ok = & $Action
        if ($ok) {
            $script:lines += "[PASS] $Name"
            return $true
        }
        $script:lines += "[FAIL] $Name"
        return $false
    } catch {
        $script:lines += "[FAIL] $Name — $($_.Exception.Message)"
        return $false
    }
}

$pass = 0
$total = 0

$total++
if (Test-Line "Health endpoint" { (Invoke-WebRequest -Uri "$AirflowUrl/health" -TimeoutSec 10).StatusCode -eq 200 }) { $pass++ }

$total++
if (Test-Line "Web UI reachable" { (Invoke-WebRequest -Uri $AirflowUrl -TimeoutSec 10).StatusCode -eq 200 }) { $pass++ }

$lines += ""
$lines += "DAGs expected: ipe_daily_sop_pipeline, ipe_hourly_schedule_pipeline, ipe_retention_enforcement"
$lines += "Login: admin / admin (dev compose only)"
$lines += ""
$lines += "RESULT: $pass / $total checks passed"

$report = "specs/003-autonomous-planning-v5/evidence/r4/airflow-verify-report.txt"
$dir = Split-Path $report -Parent
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
$lines | Set-Content -Path $report -Encoding UTF8
$lines | ForEach-Object { Write-Host $_ }

exit $(if ($pass -eq $total) { 0 } else { 1 })
