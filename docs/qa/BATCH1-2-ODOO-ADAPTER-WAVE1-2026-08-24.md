# BATCH1-2 — Odoo Adapter Wave 1 (read-only)

**Date:** 2026-08-24  
**Branch:** `batch1-foundation-hardening`  
**PH1-02:** **OPEN** — not live production / Star Trans Odoo.

## 1. Existing connector

XML-RPC client (`app/odoo/client.py`), REST adapter (`app/erp/odoo_adapter.py`), sync engine, lab **mock-odoo-api** on `:8010`. Migrations 046/050 already exist for connector schema.

## 2. Architecture

10 master adapters in `services/connector/app/wave1/` (`fetch` / `transform` / `upsert`). Orchestrator runs Plants → Calendars → WCs → Products → Materials → BOMs → Routings → Suppliers → Customers → Employees. Failures are isolated. SyncReport JSON under `docs/qa/`. Upsert target is `cdm_ingest_*` with `source_system=odoo` in payload. No write-back.

## 3–4. Tests

`pytest services/connector/tests/test_odoo_adapter_wave1.py -v` → **10/10 PASS**.

## 5. Demo instance

Did **not** start `odoo:17` (would claim a production-like instance). Lab mock-odoo XML-RPC `python -m app.wave1.cli sync` against `http://localhost:8010`: **ok=True**; WC=1, BOM=2; other Wave 1 models empty on the running mock image (warehouse/partner samples added in source, image not rebuilt).

## 6. Limitations

- Read-only masters only  
- Operational entities are Wave 2  
- No production Odoo  
- In-memory upsert in unit tests; live DB upsert not wired in this prompt (payload-ready)  
- `sync_reports` table not added (Alembic 084 already used for ingest sheets; 085–086 reserved)

## VERDICT

**YELLOW** — ENG adapters + 10/10 unit tests; mock-odoo smoke ok; PH1-02 OPEN; not production Odoo.
