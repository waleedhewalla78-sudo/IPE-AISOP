# IPE Upload Templates (aligned to upload-svc)

**Regenerated:** 2026-07-18
**Source of truth:** `services/upload-svc/app/core/validator.py` `FILE_SCHEMAS`

## Important — superseded 2026-07-12 pack

The July 12 templates used CDM/seed-style **UPPER_SNAKE** headers (`PRODUCT_CODE`, …).
Data Upload Center / upload-svc requires **lowercase** headers (`product_code`, …).
This pack matches upload-svc **Phases 1–5 + Phase 8** types.

## How data loads

| Path | Mechanism | Persists? |
|------|-----------|-----------|
| Data Upload Center | `POST /api/v1/upload/{file_type}` | Validate + wizard state (**not** full CDM row import) |
| Project plan | Schedule UI → `.xlsx` | **Yes** (cap-svc) |
| SQL seed | `seed-data.ps1` / `seed-startrans-demo.ps1` | **Yes** |
| Odoo sync | Platform → Odoo Connections | **Yes** when live (PH1-02 OPEN → mock) |
| Tariff matrix | Template only | **No HTTP upload** |

## Template index

| File | file_type | Phase | Required columns |
|------|-----------|-------|------------------|
| `product_master_upload_template.xlsx` | `product_master` | 1 | product_code, name, type, uom, name_ar |
| `customer_master_upload_template.xlsx` | `customer_master` | 1 | customer_code, name, tier, credit_limit |
| `supplier_master_upload_template.xlsx` | `supplier_master` | 1 | supplier_code, name, reliability_pct, lead_time_days |
| `work_centre_master_upload_template.xlsx` | `work_centre_master` | 1 | work_centre_code, name, capacity_hrs_day |
| `bom_upload_template.xlsx` | `bom` | 2 | product_code, component_code, quantity, scrap_pct |
| `routing_upload_template.xlsx` | `routing` | 2 | product_code, operation_seq, work_centre_code, run_minutes |
| `capacity_calendar_upload_template.xlsx` | `capacity_calendar` | 3 | work_centre_code, date, shift, available_hours |
| `lead_time_upload_template.xlsx` | `lead_time` | 3 | product_code, supplier_code, lead_time_days |
| `cost_data_upload_template.xlsx` | `cost_data` | 3 | product_code, unit_cost, currency |
| `inventory_upload_template.xlsx` | `inventory` | 4 | product_code, on_hand, location, reserved |
| `production_orders_upload_template.xlsx` | `production_orders` | 4 | mo_number, product_code, quantity, planned_start, planned_end, status, priority |
| `sales_orders_upload_template.xlsx` | `sales_orders` | 4 | order_number, customer_code, product_code, quantity, order_date, requested_delivery, status |
| `purchase_orders_upload_template.xlsx` | `purchase_orders` | 4 | po_number, supplier_code, product_code, quantity, unit_price, expected_delivery |
| `historical_otd_upload_template.xlsx` | `historical_otd` | 5 | mo_number, planned_end, actual_end, delay_days |
| `demand_forecast_upload_template.xlsx` | `demand_forecast` | 8 | product_code, period, forecast_qty, source |
| `quality_results_upload_template.xlsx` | `quality_results` | 8 | mo_number, inspection_date, result, measured_value, defect_type |
| `sop_sales_input_upload_template.xlsx` | `sop_sales_input` | 8 | product_family, period, sales_forecast_qty, rationale |
| `project_plan_upload_template.xlsx` | `project_plan (cap-svc)` | Schedule UI | MO_ID, OPERATION_SEQ, WORK_CENTER_CODE, PLANNED_START, PLANNED_END, DURATION_HRS |

| `tariff_matrix_upload_template.xlsx` | *(unwired)* | — | Parser only |
| `odoo_sync_entities_reference.xlsx` | *(reference)* | — | Not an upload |

## UI

1. Open http://localhost:8082 → login `Ahmed@nour` / `admin`
2. **Platform → Data Upload** — pick file_type matching the template
3. **Planning → Schedule** — Upload Project Plan (`project_plan_upload_template.xlsx`)

## Regenerator

```powershell
cd E:\AISOP\ipe
.\.venv\Scripts\python.exe scripts\generate_upload_templates.py
```

