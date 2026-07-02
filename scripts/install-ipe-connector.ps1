# Install ipe_connector into local Odoo 19 addons path
param(
    [string]$OdooAddons = "C:\Program Files\Odoo 19.0.20260629\server\odoo\addons",
    [string]$Source = (Join-Path (Split-Path $PSScriptRoot -Parent) "ipe_connector")
)

$ErrorActionPreference = "Stop"
$dest = Join-Path $OdooAddons "ipe_connector"

Write-Host "Copying ipe_connector to Odoo addons..." -ForegroundColor Cyan
Write-Host "  From: $Source"
Write-Host "  To:   $dest"

if (-not (Test-Path $Source)) {
    Write-Error "Source not found: $Source"
}

if (Test-Path $dest) {
    Remove-Item -Recurse -Force $dest
}
Copy-Item -Recurse $Source $dest

Write-Host "`nDone. Next steps:" -ForegroundColor Green
Write-Host "  1. Restart Odoo Windows service"
Write-Host "  2. Apps -> Update Apps List -> Install 'IPE Connector'"
Write-Host "  3. Set API key in Settings or use default: ipe-local-dev-key-change-in-production"
Write-Host "  4. Test: curl http://localhost:8069/ipe/api/v1/health -H 'X-IPE-API-KEY: ipe-local-dev-key-change-in-production'"
