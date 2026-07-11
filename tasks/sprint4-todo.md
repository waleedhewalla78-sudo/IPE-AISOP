# Sprint 4 — Wave 1 Feature Delivery

## Group A: Odoo Config v2 (W1-03, W1-04, W1-05)

- [x] A1: Read connector service structure — find existing models, API routers, main.py, mapper patterns
- [x] A2: Create Alembic migration for `cdm_erp_connection` and `cdm_erp_connection_log` tables
- [x] A3: Create SQLAlchemy models for both tables in connector service
- [x] A4: Create password encryption module using `cryptography.Fernet`
- [x] A5: Create ERP connections API router — CRUD endpoints
- [x] A6: Create test-connection endpoint
- [x] A7: Create activate and sync-now endpoints
- [x] A8: Register router in connector main.py
- [x] A9: Create tests — test_erp_connections.py
- [x] A10: Create OdooConnections.tsx frontend page
- [x] A11: Add Arabic i18n keys for Odoo Config
- [x] A12: Add route to Admin section in R1+R2 nav profiles
- [x] A13: git commit — "feat(w1): Odoo Config v2 — schema, encrypted API, admin wizard (W1-03/04/05)"

## Group B: OTD Analytics Dashboard (W1-06, W1-07, W1-08)

- [x] B1: Check if cdm_otd_snapshot table already exists (search migrations). If not, create migration.
- [x] B2: Read dpe-svc structure — find existing analytics, models, API patterns
- [x] B3: Create OTD aggregator service layer in dpe-svc
- [x] B4: Create OTD analytics API endpoints in dpe-svc
- [x] B5: Create Pydantic response schemas for all OTD endpoints
- [x] B6: Register OTD router in dpe-svc main.py
- [x] B7: Create tests — test_otd_analytics.py
- [x] B8: Create OTDDashboard.tsx frontend page
- [x] B9: Add Arabic i18n keys for OTD Dashboard
- [x] B10: Add OTD Dashboard route to BOTH R1 and R2 nav profiles
- [x] B11: git commit — "feat(w1): OTD Dashboard — aggregation, API, frontend (W1-06/07/08)"

## Closure

- [x] C1: Update CHANGELOG.md with Wave 1 entries
- [x] C2: Update PRODUCT-STATUS.md — add Odoo Config v2 and OTD Dashboard rows
- [x] C3: Update specs/017-* main file — mark W1-03 through W1-08 as DONE
- [x] C4: git commit — "chore(w1): Wave 1 complete — 8/8 items DONE"
- [x] C5: git push

## Residuals / COM (not Wave 1 eng blockers)

- [ ] #70 / T021 feasibility queue seed — OPEN (IPE Docker not up)
- [x] #71 / T022 write-back activate path — fixed + ARB
- [ ] #72 / T023 re-validate — OPEN (needs stack)
- [ ] OQ-7 / OQ-1 / PH1-02 / G-R2-04 — OPEN human/COM (do not fake)
