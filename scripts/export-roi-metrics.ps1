#Requires -Version 5.1
<#
.SYNOPSIS
  Export weekly OTD ROI metrics CSV for Star Trans / Release 1 customers.
#>
param(
    [string]$OutputPath = "docs\qa\roi-metrics-weekly.csv",
    [string]$DbHost = "localhost",
    [int]$DbPort = 5433,
    [string]$DbUser = "ipe",
    [string]$DbPassword = "ipe_test_pass",
    [string]$DbName = "ipe_test",
    [string]$TenantId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
)

$env:PGPASSWORD = $DbPassword
$sql = @"
COPY (
  SELECT
    date_trunc('week', mo.updated_at)::date AS week_start,
    COUNT(*) FILTER (WHERE mo.status = 'completed') AS completed_mos,
    COUNT(*) FILTER (WHERE mo.actual_end IS NOT NULL AND mo.planned_end IS NOT NULL AND mo.actual_end <= mo.planned_end) AS on_time,
    ROUND(AVG(mo.feasibility_score)::numeric, 1) AS avg_feasibility,
    COUNT(*) FILTER (WHERE mo.feasibility_score < 70) AS at_risk_count
  FROM cdm_manufacturing_order mo
  WHERE mo.tenant_id = '$TenantId'
  GROUP BY 1
  ORDER BY 1 DESC
  LIMIT 13
) TO STDOUT WITH CSV HEADER
"@

$dir = Split-Path $OutputPath -Parent
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

docker exec docker-db-1 psql -U $DbUser -d $DbName -c $sql 2>$null | Out-File -FilePath $OutputPath -Encoding utf8
if (-not (Test-Path $OutputPath)) {
    psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -c $sql | Out-File -FilePath $OutputPath -Encoding utf8
}
Write-Host "ROI metrics exported to $OutputPath"
