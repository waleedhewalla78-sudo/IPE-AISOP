# Star Trans Demo Dataset — Excel Workbook Schema

Authoring template for reusable client demo loads. **Today:** use SQL overlay + Schedule CSV; full multi-sheet import is POST-demo.

---

## Workbook: `StarTrans-Demo-Workbook.xlsx`

| Sheet | Purpose |
|-------|---------|
| `00_README` | Tenant ID, version, instructions |
| `01_Products` | Transformer catalog |
| `02_WorkCenters` | Shop resources |
| `03_BOM_Routing` | Operations per product |
| `04_ManufacturingOrders` | MO queue + feasibility |
| `05_DemandHistory` | Weekly demand for sense cycle |
| `06_ProjectPlan` | Live Schedule upload (see below) |

---

## Sheet 01 — Products

| Column | Required | Example |
|--------|----------|---------|
| PRODUCT_CODE | Yes | PROD001 |
| NAME | Yes | Distribution Transformer 500 kVA |
| TYPE | Yes | distribution / pad-mount / power |
| UOM | Yes | unit |
| FG_QTY | No | 120 |

**Star Trans mapping:** PROD001–PROD005 map to existing seed codes (do not change codes without migration).

---

## Sheet 04 — ManufacturingOrders

| Column | Required | Example |
|--------|----------|---------|
| MO_ID | Yes | MO-ST-001 |
| PRODUCT_CODE | Yes | PROD001 |
| QTY | Yes | 500 |
| FEASIBILITY | Yes | 52.0 |
| PRIMARY_CONSTRAINT | No | material_shortage |
| STATUS | Yes | in_progress |

Minimum **10 rows**; at least **2** with feasibility &lt; 70.

---

## Sheet 06 — ProjectPlan (live upload)

Same schema as [PROJECT-PLAN-EXCEL-SCHEMA.md](../PROJECT-PLAN-EXCEL-SCHEMA.md).

**Sample file:** [startrans/project-plan-startrans-w12.csv](./startrans/project-plan-startrans-w12.csv)

| Column | Star Trans example |
|--------|-------------------|
| PLAN_CODE | PLAN-STARTRANS-W12 |
| PLAN_NAME | Star Trans Week 12 Production |
| MO_ID | MO-ST-001 |
| OPERATION_NAME | Wind LV/HV Coils |
| WORK_CENTER_CODE | WC002 |

**Rules:**
- MO_ID must exist in sheet 04 / database
- WORK_CENTER_CODE must be WC001, WC002, or WC003
- Save sheet 06 as `.xlsx` for Schedule page upload

---

## Load methods (trade-offs)

| Method | When | Command |
|--------|------|---------|
| **SQL overlay** (today) | Before meeting | `.\scripts\seed-startrans-demo.ps1` |
| **Schedule xlsx only** | Live demo | Schedule → Upload project plan |
| **Full workbook import** | Future | POST-demo Python importer |

---

## Integrity checklist

- [ ] All MO-ST-xxx in ProjectPlan exist in MO sheet / DB  
- [ ] Product names match Copilot cheat sheet  
- [ ] Work center codes unchanged (WC001–003)  
- [ ] Run `run-full-demo.ps1 -Profile startrans` after load
