# BATCH1-6 — Integration verification

**Date:** 2026-08-24  
**Branch:** `batch1-foundation-hardening`  
**Did not** `docker compose down -v` (would wipe lab `r2_db_data` / Star Trans 28 MOs).

## 1. Prerequisites

| Prompt | Commit | Verdict |
|--------|--------|---------|
| BATCH1-1 | `06bb661` | YELLOW |
| BATCH1-2 | `f7d590f` | YELLOW |
| BATCH1-3 | `fed2465` | YELLOW |
| BATCH1-4 | `2c1bf14` | YELLOW |
| BATCH1-5 | `2ebab1a` | YELLOW |

No RED. All YELLOW (documented). COM OPEN.

## 2. Fresh rebuild

**Skipped** volume purge. Stack already warm (T090). Alembic head **086**.

## 3. Walkthrough

API/SPA smoke from BATCH1-1 still valid (web 200, kong health 200, 28 MOs). Playwright 8/8 not re-run.

## 4. RLS

`cdm_ingest_*` FORCE RLS; `cdm_copilot_audit` FORCE RLS; `cdm_data_quality_report` FORCE RLS. Isolation tests used `ipe_rls_app` (lab `ipe` is SUPERUSER+BYPASSRLS).

## 5. Odoo smoke

Wave 1 CLI vs mock-odoo `:8010` ok=True (BATCH1-2). PH1-02 OPEN.

## 6–7. Copilot / DQ

Audit + DQ modules exist; UI routes not mounted from dirty web/dpe routers.

## 8. Performance

No k6 re-baseline (BATCH1-5 YELLOW).

## 9. Tests (prompt-local)

- RLS promotion 8/8
- ingest sheets 4/4
- odoo wave1 10/10
- copilot audit 8/8
- DQ engine 8/8

Full-repo suite **not** re-run (dirty tree).

## 10. PR

Opened against `033-phase9-wave9a` if `gh` succeeds this session. **Do not merge.**

## VERDICT

**YELLOW** — Batch 1 ENG landed as 5 YELLOW commits + this note; not ready-to-merge without human review. COM OPEN. Not GREEN.
