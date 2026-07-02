# Odoo Local Integration — Quick Start

**Your Odoo:** `http://localhost:8069` · **Database:** `starttrans1` (not `strtrans1`)  
**Odoo version detected:** 19.0 (IPE connector supports 17–19 field fallbacks)

---

## Before you run setup

### 1. Fix admin password

XML-RPC auth with `admin` / `admin` **failed** on database `starttrans1`.

In Odoo UI:

1. Open `http://localhost:8069/web/login?db=starttrans1`
2. Log in with your actual password
3. **Settings → Users → admin → Change Password** → set to a known value
4. Re-run setup with that password:

```powershell
cd E:\AISOP\ipe
.\scripts\setup-odoo-integration.ps1 -OdooPassword "YOUR_PASSWORD"
```

### 2. Install Odoo apps (if not already)

From `http://localhost:8069/odoo/apps` install:

- **Sales**
- **Inventory** (stock)
- **Purchase**
- **Manufacturing** (mrp)

The seed script can install these automatically once auth works.

### 3. Optional: IPE Connector module (write-back + events)

```powershell
# Copy module to Odoo custom addons (create folder if needed)
$addons = "C:\Program Files\Odoo 19.0.20260629\server\odoo\addons"
Copy-Item -Recurse E:\AISOP\ipe\ipe_connector "$addons\ipe_connector"

# Add to odoo.conf addons_path, restart Odoo Windows service, then:
# Apps → Update Apps List → Install "IPE Connector"
# Settings → IPE: API URL http://localhost:8000, Tenant ID a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11
```

Batch sync works **without** `ipe_connector`; write-back uses XML-RPC directly.

---

## One-command setup (after password fixed)

```powershell
cd E:\AISOP\ipe
.\scripts\setup-odoo-integration.ps1 -OdooPassword "YOUR_PASSWORD"
```

This will:

1. Verify Odoo auth  
2. Seed Star Trans products, work centers, BOM, MOs, sale order, purchase order  
3. Deploy release1 Docker stack (8 services)  
4. Configure tenant `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11` with Odoo creds  
5. Run full sync (products, WC, customers, suppliers, BOM lines, routing, MOs, demands, supply)  
6. Post-sync feasibility rescore  

---

## What syncs (full ERP path)

| Odoo module | Odoo models | IPE CDM |
|-------------|-------------|---------|
| Products | `product.product` | `cdm_product` (+ qty_available → safety_stock) |
| Inventory | via product qty | on-hand proxy |
| Manufacturing | `mrp.workcenter` | `cdm_work_center` |
| MRP | `mrp.bom`, `mrp.bom.line` | `cdm_bill_of_material`, `cdm_bom_line` |
| MRP | `mrp.routing.workcenter` | `cdm_routing_operation` |
| MRP | `mrp.production` | `cdm_manufacturing_order` |
| Sales | `sale.order.line` | `cdm_demand_line` + customer link |
| Purchase | `purchase.order.line` | `cdm_supply_order` + supplier link |
| Partners | `res.partner` | `cdm_customer`, `cdm_supplier` |

---

## Manual sync (after setup)

```powershell
$headers = @{ "X-Tenant-ID" = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"; "Content-Type" = "application/json" }
$body = '{"entity":"all"}'
Invoke-RestMethod -Uri http://localhost:8000/api/v1/sync/run -Method POST -Headers $headers -Body $body
```

---

## Web UI

```powershell
cd apps\web
$env:VITE_RELEASE_PROFILE = "release1"
$env:VITE_DEFAULT_LOCALE = "ar"
npm run dev
```

Login: `Ahmed@nour` / `admin` · Control Tower should show Odoo MOs after sync.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `AUTH_FAILED` | Wrong password — reset in Odoo UI |
| `database strtrans1 does not exist` | Use **`starttrans1`** |
| Sync can't reach Odoo from Docker | Connector uses `host.docker.internal:8069` |
| All MOs "Cannot score" | Run seed script; BOM needs routing operations |
| MO dates not writing back | Odoo 19 uses `date_start`/`date_finished` (fixed in activate) |

---

*See also: `docs/integration/ODOO-CONNECTOR-INSTALL.md`*
