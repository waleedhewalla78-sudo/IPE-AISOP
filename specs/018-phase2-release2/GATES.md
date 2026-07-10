# Phase 2 Release 2 — Program Gates (G-R2)

**Feature**: `018-phase2-release2`  
**Date**: 2026-07-10 (live re-verified)  
**Target tag**: `v9.1.0-r2`  
**Authority**: `specs/018-phase2-release2/spec.md`, `docs/PHASE2-IMPLEMENTATION-GUIDE.md`

| Gate | Criteria | Status | Evidence |
|------|----------|--------|----------|
| **G-R2-01** | `scripts/release2-smoke.ps1` - R1+R2 container health + Kong login/routes | **PASS** | `docs/qa/release2-smoke-2026-07-10.txt` — 15/15 PASS (2026-07-10) after release2 compose up --build, alembic head, seed |
| **G-R2-02** | Copilot live-data tools (S2): unit `services/nlp-svc/tests/test_copilot_tools_r2.py` | **PASS** | CI/local pytest; smoke: `docs/qa/copilot-r1-smoke.txt` |
| **G-R2-03** | Wave 1 bridge W1-03–W1-08 (Odoo v2 + OTD) | **PASS (engineering)** | Live Odoo staging still PH1-02; mock-odoo XML-RPC wired for local sync E2E |
| **G-R2-04** | Arabic 8+ screens (S5) | **PASS (engineering)** · native sign-off ⬜ | `docs/qa/arabic-qa-r2.md` — **human native reviewer required** (cannot fake) |
| **G-R2-05** | `scripts/run-release2-demo.ps1` — Outcomes/sync/Copilot + Kind | **PASS** (7/7, 0 SKIP) | `docs/demo-data/release2-demo-g-r2-05.txt` |

## Gate notes

### G-R2-01 (smoke)
- Smoke requires Release 2 compose (`infrastructure/docker/docker-compose.release2.yml`).
- **2026-07-10**: **PASS** — `scripts/release2-smoke.ps1` Result: 15 passed, 0 failed. Evidence: `docs/qa/release2-smoke-2026-07-10.txt`.
- Deploy notes: stopped conflicting keycloak/minio/vault on 8180/9000/8200; compose up --build (PyPI retries); alembic upgrade head (036–042); seed via running db container; `AUTH_MODE=local` for R2 JWT smoke path.
### G-R2-05 (demo) — FIXED 2026-07-10
- mock-odoo-api XML-RPC added to R2 compose; sync/run returns real `rescored`.
- Resolution step proposes from feasibility queue `mo_id` when list empty.
- Demo JWT uses `-AuthMode local` with Keycloak fallback.

### G-R2-04
- Engineering complete; **native Arabic sign-off remains open** — blocks formal G-R2-04 PASS for release managers who require human QA.

## Tag gate

| Gate | Criteria | Status |
|------|----------|--------|
| **G-R2-TAG** | Git tag `v9.1.0-r2` on green matrix | **HOLD** — engineering gates 01/02/03/05 green; **G-R2-04 human sign-off open**; tag `v9.1.0-r2` already exists locally from prior cut — do not move; push existing tag only after policy decision, or cut `v9.1.1-r2` after Arabic sign-off |

## Test rollup

See **`TEST-RESULTS.md`**: backend **860/860** pass; Vitest **41/41** pass.  
Live: smoke **15/15**, demo **7/7**.

## Open inventory

See **`OPEN-ITEMS-PROJECT.md`** (whole project + Section B last phase).
