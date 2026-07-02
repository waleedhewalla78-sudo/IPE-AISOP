# Odoo Connector Install Guide — IPE Release 1

**Target:** Odoo 17 with Manufacturing (`mrp`) module  
**Customer reference:** Star Trans

---

## 1. Prerequisites

- Odoo 17 instance (staging + production)
- Admin access to install custom modules
- Outbound HTTPS from Odoo server to IPE API **or** LAN access for on-prem IPE
- Service account user: `ipe_sync` with Manufacturing Manager rights (minimum)

---

## 2. Install IPE Connector module

1. Copy `ipe/ipe_connector/` to Odoo addons path:
   ```bash
   cp -r ipe_connector /opt/odoo/custom-addons/
   ```
2. Update `odoo.conf`:
   ```ini
   addons_path = /opt/odoo/addons,/opt/odoo/custom-addons
   ```
3. Restart Odoo, enable Developer Mode
4. Apps → Update Apps List → search **IPE Connector** → Install
5. Settings → IPE Connector:
   - **IPE API URL:** `https://ipe.startrans.example` (Kong gateway)
   - **API Secret:** generate 32+ char secret (store in IPE tenant + Odoo config)
   - **Tenant ID:** UUID from IPE admin

---

## 3. IPE tenant configuration

Set on `cdm_tenant` (via Platform Admin or SQL):

| Field | Example |
|-------|---------|
| `erp_type` | `odoo` |
| `erp_version` | `17.0` |
| `erp_base_url` | `https://odoo.startrans.local` |
| `api_secret` | HMAC secret (matches Odoo) |
| `config.odoo_db` | `startrans_prod` |
| `config.odoo_username` | `ipe_sync` |
| `config.odoo_password` | *(vault — not plain text in prod)* |

---

## 4. Verify connection

```powershell
# From IPE host
$body = @{
  odoo_url = "https://odoo.startrans.local"
  odoo_db = "startrans_prod"
  odoo_username = "ipe_sync"
  odoo_password = "<secret>"
  entity = "products"
} | ConvertTo-Json

Invoke-RestMethod -Method POST `
  -Uri "http://localhost:8000/api/v1/sync/run" `
  -Headers @{ Authorization = "Bearer <jwt>"; "X-Tenant-ID" = "<tenant-uuid>" } `
  -Body $body -ContentType "application/json"
```

Expected: `{ success: true, data: { products: { synced: N, total: M } } }`

---

## 5. Scheduled sync

Release 1 connector runs sync every **15 minutes** when `IPE_RELEASE_PROFILE=release1`.

Manual trigger: same `POST /api/v1/sync/run` with `entity: "all"`.

---

## 6. Write-back (schedule approve)

When planner approves schedule in IPE:

1. IPE calls Odoo XML-RPC to update `mrp.production` dates
2. Odoo `ipe_connector` receives optional Kafka/HMAC actions for confirm/reschedule
3. Chatter message posted on MO: "Schedule updated by IPE AI"

Verify in Odoo: MO → Planned Date fields updated after approve.

---

## 7. Troubleshooting

| Issue | Check |
|-------|-------|
| Authentication failed | User/password, database name, URL |
| SSL error | Use `http` on LAN or install cert |
| Module not found | addons_path, restart Odoo |
| HMAC mismatch | api_secret identical both sides |

See `docs/runbooks/R1-SUPPORT-RUNBOOK.md`.
