# BATCH 1 Retest — 2026-08-24

**Branch:** `batch1-foundation-hardening` (tracks `origin/batch1-foundation-hardening`)  
**Lab DB:** `ipe_test` @ localhost:5433  
**Alembic head:** **086**  
**PR 164:** **OPEN**, not merged — `https://github.com/waleedhewalla78-sudo/IPE-AISOP/pull/164` (base `master`, head `batch1-foundation-hardening`)  
**COM:** **OPEN** — PH1-02 / G-R2-04 / OQ-7 / C-01…C-08 unchanged. PH1-02 stays OPEN even though connector Wave 1 unit tests pass.

Python: `e:\AISOP\ipe\.venv\Scripts\python.exe`

---

## Per-prompt verdicts (this retest)

| Prompt | Commit | Prior | Retest | Notes |
|--------|--------|-------|--------|-------|
| BATCH1-1 promotion + RLS | `06bb661` | YELLOW | **YELLOW** | Tables + 8/8 RLS PASS; COM OPEN |
| BATCH1-2 Odoo Wave 1 | `f7d590f` | YELLOW | **YELLOW** | 10/10 unit PASS; **PH1-02 OPEN**; not live Star Trans Odoo |
| BATCH1-3 Copilot audit | `fed2465` | YELLOW | **YELLOW** | 8/8 PASS; UI route exists in dirty tree, not claimed deployed |
| BATCH1-4 Data quality | `2c1bf14` | YELLOW | **YELLOW** | 8/8 PASS; API/UI mount still YELLOW vs dirty routers |
| BATCH1-5 Performance | `2ebab1a` | YELLOW | **YELLOW** | Optional `run-k6-slo.ps1` re-ran: **FAIL** P95 1035ms (errors 0%). Not a 500-MO baseline. |
| BATCH1-6 Integration | `d76efca` | YELLOW | **YELLOW** | PR 164 still unmerged; not ready-to-merge |

No RED. Not GREEN.

---

## 1. Ingest catalog (`\dt cdm_ingest_*` / `demo_*`)

**27** `cdm_ingest_*` tables. **Zero** `demo_*` relations (`Did not find any relation named "demo_*"`).

README is **not** a table.

`SHEET_TABLE` in `services/upload-svc/app/core/startrans_ingest.py` maps **23** Excel data sheets (all `EXPECTED_SHEETS` except README) to `cdm_ingest_*`. Confirmed by `test_all_data_sheets_mapped` **PASS**.

---

## 2. RLS

```
pytest services/tests/rls/test_batch1_promotion.py -v
```

**8/8 PASS** (7 isolation cases + 084 FORCE-RLS catalog). Runtime 5.12s.

Uses `ipe_rls_app` (NOSUPERUSER, NOBYPASSRLS). Lab role `ipe` remains SUPERUSER+BYPASSRLS — tests do not rely on it for isolation.

---

## 3. Upload-svc workbook / ingest

```
pytest services/upload-svc/tests/test_startrans_ingest_tables.py
       services/upload-svc/tests/test_startrans_workbook.py -v
```

**6/6 PASS** (4 ingest mapping + 2 workbook). Runtime 7.62s.

---

## 4. Connector / Odoo Wave 1

```
pytest services/connector/tests/test_odoo_adapter_wave1.py -v
```

**10/10 PASS**. Runtime 0.44s.

**PH1-02 remains OPEN.** Mock/unit adapters ≠ production / Star Trans Odoo UAT. No production Odoo credentials used.

---

## 5. Copilot audit

```
pytest services/tests/governance/test_copilot_audit.py -v
```

(`PYTHONPATH=services/nlp-svc`) **8/8 PASS**. Runtime 17.46s.

---

## 6. DQ engine

```
pytest services/tests/data_quality/test_dq_engine.py -v
```

(`PYTHONPATH=services/dpe-svc`) **8/8 PASS**. Runtime 22.34s.

---

## 7. UI smoke

| Check | Result |
|-------|--------|
| `GET http://localhost:8082` | **200** |
| Playwright home-role desktop | **FAIL (infra)** — Chromium not installed in agent Playwright cache. Package present (`@playwright/test` 1.61.0). **Not faked.** |

Dirty working tree still contains unrelated web/router edits. This retest does not treat those as merged Batch 1 product.

---

## 8. Commits + PR

On `batch1-foundation-hardening`:

| Commit | Message |
|--------|---------|
| `06bb661` | BATCH1-1.T: promote demo_* to canonical+RLS YELLOW |
| `f7d590f` | BATCH1-2.T: odoo adapter wave1 YELLOW |
| `fed2465` | BATCH1-3.T: copilot audit trail YELLOW |
| `2c1bf14` | BATCH1-4.T: data quality dashboard YELLOW |
| `2ebab1a` | BATCH1-5.T: performance baseline YELLOW |
| `d76efca` | BATCH1-6.T: batch1 integration YELLOW — not ready to merge |

**PR 164 is OPEN. Not merged.** This retest did not merge it.

---

## Checks table

| # | Check | Pass/Fail |
|---|-------|-----------|
| 1 | `\dt cdm_ingest_*` 27 tables | **PASS** |
| 2 | No `demo_*` tables | **PASS** |
| 3 | 23 data sheets in SHEET_TABLE; README skipped | **PASS** |
| 4 | RLS pytest | **PASS 8/8** |
| 5 | upload-svc ingest+workbook | **PASS 6/6** |
| 6 | Odoo Wave 1 pytest | **PASS 10/10** |
| 7 | PH1-02 closed | **FAIL (still OPEN — honest)** |
| 8 | Copilot audit pytest | **PASS 8/8** |
| 9 | DQ engine pytest | **PASS 8/8** |
| 10 | Web :8082 200 | **PASS** |
| 11 | Playwright home-role | **FAIL** (browser binary) |
| 12 | BATCH1-1…6 commits present | **PASS** |
| 13 | PR 164 not merged | **PASS** (still OPEN) |
| 14 | COM C-01…C-08 / OQ-7 / G-R2-04 | **OPEN** |

---

## VERDICT

**YELLOW**

Engineering tests for prompts 1–4 re-ran green. Foundation is **not** merge-ready: PR 164 unmerged, COM OPEN, PH1-02 OPEN, Playwright not re-proven this session, performance baseline still not a 500-MO k6. Matches BATCH1-6 honesty.

**Batch 2 gate:** not RED. User authorized proceeding with documented YELLOW caveats. Batch 2 must **not** treat this as production Hetzner / live Odoo UAT / SOW-countersign independently verified beyond the operator instruction to execute.
