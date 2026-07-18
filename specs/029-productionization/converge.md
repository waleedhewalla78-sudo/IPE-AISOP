# Converge — Spec 029 Productionization

**Date**: 2026-07-18 · **Verdict**: **ENG COMPLETE Wave 1** (stack-dependent + COM residuals OPEN)

## Closed by engineering

- Kong `/api/v1/enterprise` declarative route (R2 + deploy mirrors)
- Andon dual-write to `cdm_andon_alert`
- RLS migration 068 (gap tables)
- MPS/MRP persistence migration 069 + optional API persist
- S&OP stage-gate scaffold APIs
- Speckit artifacts + constitution 1.4.1 pointers
- Unit/API tests: **27 passed** (spec029 + phase7 ops/api)

## Remaining (honest)

| ID | Item | Owner | Status |
|----|------|-------|--------|
| ENG-01..03 | #70/#72/#110 validate after seed | ENG | **OPEN — stack down this run** |
| QA-01 | k6 p95 under load | ENG | **OPEN — notes only** |
| QA-02 | Playwright flakes | ENG | **OPEN — notes + stub** |
| C-01 | OQ-7 pricing | COM | **OPEN** |
| C-02 | SOW send | COM | **OPEN** |
| C-03 | PH1-02 Odoo staging | CUST/OPS | **OPEN** |
| C-04 | G-R2-04 Arabic | HUMAN | **OPEN** (gates `v9.1.1-r2`) |
| C-05 | OQ-1 Odoo 17/19 | CUST | **OPEN** |
| REL-02 | Never push `v9.1.0-r2` | ENG | Policy enforced |

## Next Speckit

None required for Wave 1. Optional follow-on: live Kong enterprise smoke after `docker compose …release2.yml up -d` healthy; validate campaign; k6 re-tune.
