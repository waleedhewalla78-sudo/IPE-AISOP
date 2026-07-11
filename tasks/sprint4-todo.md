# Sprint 4 — Wave 1 Feature Delivery

## Group A: Odoo Config v2 (W1-03, W1-04, W1-05)

- [ ] A1: Read connector service structure — find existing models, API routers, main.py, mapper patterns
- [ ] A2: Create Alembic migration for `cdm_erp_connection` and `cdm_erp_connection_log` tables
- [ ] A3: Create SQLAlchemy models for both tables in connector service
- [ ] A4: Create password encryption module using `cryptography.Fernet`
- [ ] A5: Create ERP connections API router — CRUD endpoints
- [ ] A6: Create test-connection endpoint
- [ ] A7: Create activate and sync-now endpoints
- [ ] A8: Register router in connector main.py
- [ ] A9: Create tests — test_erp_connections.py
- [ ] A10: Create OdooConnections.tsx frontend page
- [ ] A11: Add Arabic i18n keys for Odoo Config
- [ ] A12: Add route to Admin section in R1+R2 nav profiles
- [ ] A13: git commit — "feat(w1): Odoo Config v2 — schema, encrypted API, admin wizard (W1-03/04/05)"

## Group B: OTD Analytics Dashboard (W1-06, W1-07, W1-08)

- [ ] B1: Check if cdm_otd_snapshot table already exists (search migrations). If not, create migration.
- [ ] B2: Read dpe-svc structure — find existing analytics, models, API patterns
- [ ] B3: Create OTD aggregator service layer in dpe-svc
- [ ] B4: Create OTD analytics API endpoints in dpe-svc
- [ ] B5: Create Pydantic response schemas for all OTD endpoints
- [ ] B6: Register OTD router in dpe-svc main.py
- [ ] B7: Create tests — test_otd_analytics.py
- [ ] B8: Create OTDDashboard.tsx frontend page
- [ ] B9: Add Arabic i18n keys for OTD Dashboard
- [ ] B10: Add OTD Dashboard route to BOTH R1 and R2 nav profiles
- [ ] B11: git commit — "feat(w1): OTD Dashboard — aggregation, API, frontend (W1-06/07/08)"

## Closure

- [ ] C1: Update CHANGELOG.md with Wave 1 entries
- [ ] C2: Update PRODUCT-STATUS.md — add Odoo Config v2 and OTD Dashboard rows
- [ ] C3: Update specs/017-* main file — mark W1-03 through W1-08 as DONE
- [ ] C4: git commit — "chore(w1): Wave 1 complete — 8/8 items DONE"
- [ ] C5: git push
