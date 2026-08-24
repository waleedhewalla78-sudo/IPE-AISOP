# T091 Kong + `/api/v1/data/upload` live verify — 2026-08-24

**Branch:** `033-phase9-wave9a`  
**Prerequisite:** T090 2026-08-24 YELLOW; stack UP.

## 1. kong.release2.yml routes

Confirmed in `infrastructure/docker/kong.release2.yml`:

- `/api/v1/upload` → upload-svc
- `/api/v1/data` → upload-svc

No Kong `jwt` plugin on those routes (lab compose). Not modified (Batch 0 constraint).

## 2. Kong reload

`docker compose … restart kong` — container Started. Proxy health `GET /api/v1/health` = **200**. `kong health` reports healthy.

Host **8001** is not mapped; admin API is in-container only.

## 3. Auth

`POST /api/v1/auth/login` via PowerShell `curl.exe` returned **HTTP 000** (client/JSON-escaping failure, not a captured 401/200 body). Token not obtained this run. Documented demo passwords were not printed.

## 4. Unauthenticated upload

`POST http://localhost:8000/api/v1/data/upload` with template, no `Authorization`: **HTTP 200**.

Expected by prompt: **401**. Lab Kong does not enforce JWT on `/api/v1/data` — same YELLOW as 2026-08-15.

## 5. Authenticated upload

Skipped (no token). Unauth path already returned a full preview (gateway did not require JWT).

## 6. Preview quality (template through Kong)

File: `docs/demo-data/startrans/IPE_Data_Template_StarTrans_v1.xlsx`

| Field | Result |
|-------|--------|
| HTTP | 200 |
| `valid` | True |
| `sheets_found` | **24** |
| `will_insert` | **69** |
| `will_fail` | 0 |
| Auto-commit | **No** (preview only; `/commit` not called) |

Sheets: README, 01_Plants, 02_WorkCenters, 03a_Calendars, 03b_CalendarShifts, 03c_CalendarExceptions, 04_Products, 05_Materials, 06a_BOMHeaders, 06b_BOMLines, 07a_RoutingHeaders, 07b_RoutingOperations, 08_Suppliers, 09_Customers, 10a_Employees, 10b_EmployeeSkills, 11a_SalesOrderHeaders, 11b_SalesOrderLines, 12_ManufacturingOrders, 13a_PurchaseOrderHeaders, 13b_PurchaseOrderLines, 14_Inventory, 15_Forecasts, 16_ExecutionEvents.

## 7. Non-xlsx

`ipe_bad.txt` via Kong: **HTTP 200**, body `valid=false`, error `Unsupported file type: ipe_bad.txt (expect .xlsx)`. Prompt expected **400**. Source `data_upload.py` raises 400; live image returned 200 envelope — do not treat as PASS.

## 8. VERDICT

**YELLOW** — live preview **24 sheets / 69 rows** through Kong; JWT not enforced (unauth 200); non-xlsx not HTTP 400.

Stack left **UP**.
