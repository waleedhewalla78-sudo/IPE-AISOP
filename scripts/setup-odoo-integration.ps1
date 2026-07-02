# Setup full Odoo ↔ IPE integration (local Windows)
# Usage:
#   .\scripts\setup-odoo-integration.ps1
#   .\scripts\setup-odoo-integration.ps1 -OdooPassword "yourpassword"

param(
    [string]$OdooUrl = "http://localhost:8069",
    [string]$OdooDb = "starttrans1",
    [string]$OdooUser = "whewalla@gmail.com",
    [string]$OdooPassword = "admin",
    [string]$TenantId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    [switch]$SkipDeploy,
    [switch]$SkipSeed
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host "=== IPE + Odoo Integration Setup ===" -ForegroundColor Cyan
Write-Host "Odoo: $OdooUrl  DB: $OdooDb  User: $OdooUser"

# 1. Verify Odoo reachable
Write-Host "`n[1/6] Testing Odoo connection..." -ForegroundColor Yellow
python -c @"
import xmlrpc.client, sys
url = '$OdooUrl'
db = '$OdooDb'
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
print('Odoo version:', common.version().get('server_version'))
uid = common.authenticate(db, '$OdooUser', '$OdooPassword', {})
if not uid:
    print('AUTH_FAILED: admin credentials rejected for database', db)
    print('Available databases:', xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/db').list())
    sys.exit(1)
print('Auth OK uid=', uid)
"@ 
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nFix: Use correct database name (likely starttrans1 not strtrans1) and password." -ForegroundColor Red
    Write-Host "Reset Odoo admin password in Odoo UI: Settings -> Users -> admin -> Change Password" -ForegroundColor Red
    exit 1
}

# 2. Seed Odoo master data
if (-not $SkipSeed) {
    Write-Host "`n[2/6] Seeding Odoo Star Trans data..." -ForegroundColor Yellow
    python scripts/seed-odoo-startrans.py --url $OdooUrl --db $OdooDb --user $OdooUser --password $OdooPassword
    if ($LASTEXITCODE -ne 0) { exit 1 }
} else {
    Write-Host "`n[2/6] Skipping Odoo seed" -ForegroundColor DarkGray
}

# 3. Deploy release1 stack
if (-not $SkipDeploy) {
    Write-Host "`n[3/6] Deploying release1 Docker stack..." -ForegroundColor Yellow
    & "$Root\scripts\deploy-release1.ps1"
    if ($LASTEXITCODE -ne 0) { exit 1 }
} else {
    Write-Host "`n[3/6] Skipping deploy" -ForegroundColor DarkGray
}

# 4. Configure tenant Odoo credentials in IPE DB
Write-Host "`n[4/6] Configuring tenant Odoo credentials..." -ForegroundColor Yellow
$odooHostUrl = $OdooUrl -replace "localhost", "host.docker.internal"
python -c @"
import json, subprocess, sys
tenant_id = '$TenantId'
config = {
    'odoo_url': '$odooHostUrl',
    'odoo_db': '$OdooDb',
    'odoo_username': '$OdooUser',
    'odoo_password': '$OdooPassword',
}
sql = f"""
UPDATE cdm_tenant SET
  name = 'Star Trans — Electrical Transformer Technology',
  erp_type = 'odoo',
  erp_version = '19.0',
  erp_base_url = '{config['odoo_url']}',
  config = COALESCE(config, '{{}}'::jsonb) || '{json.dumps(config)}'::jsonb
WHERE id = '{tenant_id}';
"""
container = subprocess.check_output(['docker','ps','--format','{{.Names}}'], text=True).splitlines()
db = next((c for c in container if 'db' in c.lower()), None)
if not db:
    sys.exit('No docker db container')
subprocess.run(['docker','exec','-i',db,'psql','-U','ipe','-d','ipe_test','-q'], input=sql, text=True, check=True)
print('Tenant configured')
"@

# 5. Run full sync via connector API
Write-Host "`n[5/6] Running full Odoo sync..." -ForegroundColor Yellow
$syncBody = @{
    odoo_url      = $OdooUrl -replace "localhost", "host.docker.internal"
    odoo_db       = $OdooDb
    odoo_username = $OdooUser
    odoo_password = $OdooPassword
    entity        = "all"
} | ConvertTo-Json

$headers = @{
    "Content-Type" = "application/json"
    "X-Tenant-ID"  = $TenantId
}

try {
    $resp = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/sync/run" -Method POST -Headers $headers -Body $syncBody -TimeoutSec 120
    if ($resp.success) {
        Write-Host "  Sync OK:" -ForegroundColor Green
        $resp.data | ConvertTo-Json -Depth 5
    } else {
        Write-Host "  Sync failed:" ($resp.error | ConvertTo-Json) -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  Sync request failed: $_" -ForegroundColor Red
    Write-Host "  Try: curl http://localhost:8000/api/v1/health" -ForegroundColor DarkGray
    exit 1
}

# 6. Sync status + data quality
Write-Host "`n[6/6] Sync status..." -ForegroundColor Yellow
$status = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/sync/status" -Headers @{"X-Tenant-ID"=$TenantId}
$status.data | ConvertTo-Json -Depth 5

$dq = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/sync/data-quality" -Headers @{"X-Tenant-ID"=$TenantId}
Write-Host "  Data quality flags: $($dq.data.count)" -ForegroundColor $(if ($dq.data.count -eq 0) {"Green"} else {"Yellow"})

Write-Host "`n=== Integration setup complete ===" -ForegroundColor Green
Write-Host "Web UI: cd apps\web; `$env:VITE_RELEASE_PROFILE='release1'; npm run dev" -ForegroundColor DarkGray
Write-Host "Login: Ahmed@nour / admin  |  Tenant: $TenantId" -ForegroundColor DarkGray
