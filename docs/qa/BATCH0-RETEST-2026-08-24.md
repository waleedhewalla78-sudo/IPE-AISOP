# BATCH 0 Retest — 2026-08-24

**Branch:** `batch1-foundation-hardening`  
**Compose:** `ipe/infrastructure/docker/docker-compose.release2.yml` (service **`db`**, not postgres)  
**Lab DB:** `ipe_test` @ localhost:**5433**  
**Date/time:** 2026-08-24 ~14:47–14:55 UTC  
**Honesty:** COM **OPEN** (PH1-02 / G-R2-04 / OQ-7 / C-01…C-08). Not fake-closed.

This is an **ops smoke retest**, not a Batch 0 re-implementation. No product code was changed for this report.

---

## 1. Stack (`docker compose ps`)

**20 containers Up.** Port **5433** is held by IPE `docker-db-1` (`postgres:16`), not a foreign process. No al-azhar stop was required.

| Demo-critical | Status | Host port |
|---------------|--------|-----------|
| kong | Up (healthy) | 8000 |
| web-ui | Up (healthy) | 8082 |
| dpe-svc | Up (no compose health flag) | 8020 |
| fea-svc | Up (no compose health flag) | 8004 |
| cap-svc | Up (no compose health flag) | 8003 |
| upload-svc | Up (healthy) | 8120 |
| mat-svc | Up (healthy) | 8002 |
| res-svc | Up (healthy) | 8005 |
| db | Up (healthy) | 5433 |
| redis | Up (healthy) | 6380 |

Also Up: connector:8016, demand-svc, keycloak, keycloak-db, minio, mock-odoo-api:8010, nlp-svc, scenario-svc, sop-svc, vault.

`up -d` was **not** needed (stack already warm from T090 / Batch 1).

---

## 2. HTTP smoke

| Check | Result |
|-------|--------|
| `GET http://localhost:8082` | **200** (len 1179) |
| Kong `GET http://localhost:8000/api/v1/health` | **200** `dpe-svc` status ok; db/redis/vault up |
| dpe `GET http://localhost:8020/health` | **200** `{"status":"ok"}` |
| upload `GET http://localhost:8120/health` | **200** `{"status":"ok"}` |
| fea `GET http://localhost:8004/health` | **200** `{"status":"ok"}` |

---

## 3. Alembic head

```sql
SELECT version_num FROM alembic_version;
```

**Actual: `086`** (not 082). Historical Batch 0 expect was 082; Batch 1 applied **083–086** on this lab. Reported as-is.

---

## 4. Kong upload preview (no /commit)

File: `e:\AISOP\ipe\docs\demo-data\startrans\IPE_Data_Template_StarTrans_v1.xlsx` (78056 bytes).  
Downloads `(2).xlsx` was not present; repo template used.

```
POST http://localhost:8000/api/v1/data/upload  files=@…xlsx
```

| Field | Result |
|-------|--------|
| HTTP | **200** |
| `valid` | true |
| `sheets_found` | **24** (README + 23 data) |
| `sheets_missing` / `errors` | empty |
| `will_insert` | **69** |
| `will_fail` | 0 |

Matches T091 expectation (24 sheets / ~69 insert rows). `/commit` was **not** called.

Lab Kong still allows unauthenticated POST on `/api/v1/data` (same YELLOW as T091). Not fixed in this retest (Batch 0 forbids Kong edits).

---

## 5. Manufacturing orders

```sql
SELECT COUNT(*) FROM cdm_manufacturing_order;
```

**28** (lab seed retained; T092 was 20, overlay later brought this to 28).

---

## 6. Optional e2e / k6 / Playwright

| Suite | Result |
|-------|--------|
| `python scripts/e2e/critical_path_test.py` | **5/5 PASS** (fea 81.4% queued_for_planner; res-svc 32 scenarios) |
| `scripts/run-k6-slo.ps1` | **FAIL** — k6 v2.0.0; 525 req; error rate **0.00%**; P95 **1035ms** (target &lt;500ms). Thresholds crossed: `api_latency`, `http_req_duration{api:feasibility}`, `http_req_duration{api:health}`. Exit 99. **Not faked PASS.** |
| Playwright `e2e/home-role.spec.ts` desktop | **FAIL (infra)** — package 1.61.0 present; Chromium binary missing in this agent sandbox (`npx playwright install` required). **Not a product FAIL; not a fake PASS.** UI HTTP 200 is the only UI evidence this session. |

---

## 7. Checks table

| # | Check | Pass/Fail |
|---|-------|-----------|
| 1 | Demo-critical containers Up | **PASS** |
| 2 | Port 5433 is IPE `db` | **PASS** |
| 3 | Web :8082 200 | **PASS** |
| 4 | Kong /api/v1/health 200 | **PASS** |
| 5 | dpe :8020 health 200 | **PASS** |
| 6 | upload :8120 health 200 | **PASS** |
| 7 | fea :8004 health 200 | **PASS** |
| 8 | Alembic head reported (086) | **PASS** (value shifted vs Batch0 082) |
| 9 | Kong upload 24 sheets / 69 rows | **PASS** |
| 10 | MO count queried (28) | **PASS** |
| 11 | critical_path_test.py 5/5 | **PASS** |
| 12 | k6 SLO | **FAIL** (P95 1035ms &gt; 500ms; errors 0%) |
| 13 | Playwright home-role desktop | **FAIL** (browser binary missing) |
| 14 | Kong JWT on /api/v1/data | **FAIL** (lab unauth 200 — inherited YELLOW) |
| 15 | COM PH1-02 / G-R2-04 / OQ-7 / C-01…C-08 | **OPEN** (not a Batch 0 close) |

---

## VERDICT

**YELLOW**

Ops smoke is live: stack up, health 200s, upload preview **24/69**, **28** MOs, alembic **086**, e2e **5/5**. Not GREEN because (1) lab Kong JWT still off `/api/v1/data`, (2) dpe/fea/cap lack compose `healthy`, (3) Playwright browsers missing this session, (4) k6 SLO **FAIL** (P95 1035ms), (5) COM remains OPEN.

Proceed to Batch 1 retest / Batch 2 **only with these caveats**. No RED blocker on the required smoke path.
