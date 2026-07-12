# IPE QA Upload Templates

**Generated:** 2026-07-12  
**Tenant (demo):** `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11`  
**Aligned to:** CDM seed schemas, Star Trans CSV spec, connector Odoo mapper, cap-svc project-plan upload

## How data actually loads today

| Path | Mechanism | UI? |
|------|-----------|-----|
| Master data (products, WC, BOM, MO, demand, suppliers, inventory) | SQL via `scripts/seed-data.ps1` + `seed-startrans-demo.ps1` | No |
| Project plan | `POST /api/v1/capacity/project-plans/upload` (`.xlsx` only) | Yes — Schedule → Upload |
| Odoo ERP | Connector XML-RPC sync (`/api/v1/sync/run`, `/erp/connections/{id}/sync-now`) | Platform → Odoo Config |
| Tariff matrix | Parser exists in cap/dpe code; **no HTTP upload wired** | No |

These `.xlsx` files are **QA upload templates** matching field names used by seeds/APIs. Use them for isolated testing prep, customer data collection, and future importers. Each workbook has a `README` sheet with type/validation hints; header cells also carry Excel comments.

## Template index

| File | Entity / CDM | Sample rows | Load path |
|------|--------------|-------------|-----------|
| `products_upload_template.xlsx` | `cdm_product` | 3 | SQL seed / Odoo `product.product` sync |
| `work_centers_upload_template.xlsx` | `cdm_work_center` | 3 | SQL seed / Odoo `mrp.workcenter` |
| `bom_routing_upload_template.xlsx` | `cdm_bill_of_material`, `cdm_bom_line`, `cdm_routing_operation` | 3 | SQL seed / Odoo `mrp.bom` |
| `mrp_orders_upload_template.xlsx` | `cdm_manufacturing_order` | 3 | SQL seed / Odoo `mrp.production` |
| `demand_lines_upload_template.xlsx` | `cdm_demand_line` | 3 | SQL seed / Odoo `sale.order.line` |
| `suppliers_upload_template.xlsx` | `cdm_supplier` | 3 | SQL seed / Odoo `res.partner` (supplier) |
| `customers_upload_template.xlsx` | `cdm_customer` | 3 | SQL seed / Odoo partner (customer) |
| `inventory_upload_template.xlsx` | `cdm_inventory_position` | 3 | SQL seed (Odoo quants map to product safety_stock today) |
| `supply_orders_upload_template.xlsx` | `cdm_supply_order` | 3 | SQL seed / Odoo `purchase.order.line` |
| `operators_upload_template.xlsx` | `cdm_operator` | 3 | SQL seed |
| `project_plan_upload_template.xlsx` | Project plan (cap-svc) | 3 | **UI upload** Schedule page |
| `tariff_matrix_upload_template.xlsx` | Tariff shock input | 3 | Parser ready; **no upload API** |
| `odoo_sync_entities_reference.xlsx` | Field map reference | 10 | Not an upload — mapping doc |

## Related artifacts

- Star Trans CSV originals: `docs/demo-data/startrans/*.csv`
- Spec: `docs/demo-data/STARTRANS-CSV-UPLOAD-SPEC.md`
- Project plan schema: `docs/PROJECT-PLAN-EXCEL-SCHEMA.md`
- Generator for demo plan: `scripts/generate-project-plan-template.py`

## Recommended load order (SQL / future importer)

1. Products → Work centers → Operators → Customers → Suppliers  
2. BOM/routing → Inventory → Supply orders  
3. Manufacturing orders → Demand lines  
4. Project plan (`.xlsx` via Schedule UI after MOs exist)

## Validation tips

- `MO_ID` in project plan must match `erp_mo_id` already in DB (`MO-ST-*` after Star Trans seed).
- `WORK_CENTER_CODE` must match seeded WC codes (`WC001`…).
- Project plan max size 5 MB; sheet name preferably `ProjectPlan`.
- Do not invent live Odoo connectivity for COM/PH1-02 — use `mock-odoo-api` (:8010) or SQL seed for eng tests.
