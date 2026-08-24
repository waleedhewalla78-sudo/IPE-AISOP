# Seed a load-test tenant (BATCH1-5) — NOT run against Star Trans lab graph by default.
# Creates documentation-only parameters. Do not execute on production.
param([int]$MoCount = 500, [switch]$Force)
Write-Host "BATCH1-5 load seed is a template. MoCount=$MoCount"
if (-not $Force) {
  Write-Host "Refusing: pass -Force only on an isolated empty database. Lab Star Trans graph stays at 28 MOs."
  exit 2
}
Write-Host "Force path not implemented — avoid destroying lab seed."
exit 1
