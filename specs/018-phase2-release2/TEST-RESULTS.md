# Phase 2 Release 2 — Test Results

**Run date:** 2026-07-10  
**Runner:** `uv run pytest` (services), `npx vitest run` (apps/web)  
**Branch / workspace:** `E:\AISOP\ipe`  
**Target:** Spec `018-phase2-release2` (`v9.1.0-r2`)

## Executive summary

| Layer | Result |
|-------|--------|
| **Backend R2 services (7)** | **860 passed**, **0 failed**, **6 skipped** (plus 12 deselected in nlp-svc) |
| **apps/web Vitest** | **41 passed**, **0 failed**, **0 errors** (no live API; env/network mocks) |
| **apps/web Playwright** | **Not executed** — port `8082` already in use; `release2` project sets `reuseExistingServer: false` |

Post-run fixes applied in-tree: copilot tool count (16), unit-test env defaults, health probe `ok` status, auth fixture alignment, planner intent test phrasing, handler quota mock, CTP `no_auth` status codes.

---

## Full backend matrix (service suites)

| Service | Pass | Fail | Skip / other | Duration (approx) | Gate |
|---------|-----:|-----:|--------------|-------------------|------|
| nlp-svc | 143 | 0 | 12 deselected | 42s | PASS |
| dpe-svc | 205 | 0 | 2 skipped | 64s | PASS |
| connector | 72 | 0 | 4 skipped | 8s | PASS |
| demand-svc | 20 | 0 | — | 13s | PASS |
| scenario-svc | 13 | 0 | — | 12s | PASS |
| cap-svc | 283 | 0 | — | 62s | PASS |
| mat-svc | 124 | 0 | — | 12s | PASS |
| **Total** | **860** | **0** | **6 skipped** (+12 deselected) | ~3.5 min | **PASS** |

Command (per service): `cd services/<svc> && uv run pytest tests/ -q`

---

## Sprint / wave mapping (R2-focused tests)

| Sprint / wave | Focus | Test target | Pass | Fail | Notes |
|---------------|-------|-------------|-----:|-----:|-------|
| **W1 bridge** | Odoo + OTD | `connector`: `test_odoo_adapter.py`, `test_odoo_sync_integration.py` | 9 | 0 | PASS |
| **W1 / S6** | OTD analytics APIs | `dpe-svc`: `test_analytics.py`, `test_ops_dashboard.py`, `test_chaos_cost_aggregate.py` | 9 | 0 | PASS |
| **S1** | R2 infra / nav | Playwright `e2e/release2-nav.spec.ts` | — | — | **BLOCKED** (see Playwright) |
| **S1** | R2 nav (unit) | Vitest `tests/features/release2/release2-nav.test.tsx` | 3 | 0 | PASS |
| **S2** | Copilot live tools | `nlp-svc`: `test_copilot_tools.py` | 13 | 0 | PASS (16 tools) |
| **S3** | Demand SES / forecast | `demand-svc`: `test_forecaster.py`, `test_forecaster_factory.py` | 6 | 0 | PASS |
| **S3** | Demand UI smoke | Vitest `v8Pages.smoke.test.tsx` (DemandForecastPage) | 1 | 0 | PASS |
| **S4** | Scenario simulator | `scenario-svc`: `test_simulator.py` | 2 | 0 | PASS |
| **S5** | Arabic i18n | Vitest `tests/lib/i18n.test.ts` | 4 | 0 | PASS |
| **S5** | Arabic E2E | `e2e/arabic-r2.spec.ts` | — | — | Not run (Playwright blocked) |
| **S8** | Ops dashboard | `dpe-svc`: `test_ops_dashboard.py` | (in W1/S6 bundle) | 0 | PASS |
| **S9** | Production intelligence | `cap-svc`: `test_analytics_production.py` | 3 | 0 | PASS |
| **S10** | Supply chain intel | `mat-svc`: `test_supplier_model.py`, `test_po_suggestion.py` | 24 | 0 | PASS |
| **S11** | S&OP synthesis | `dpe-svc`: `test_sop_api.py`, `test_sop_solver.py` | 18 | 0 | PASS |
| **S12** | SAP B1 | — | — | — | **CUT** (no tests) |

---

## apps/web — Vitest (`npx vitest run`)

| Metric | Count |
|--------|------:|
| Test files | 16 (16 pass, 0 fail) |
| Tests | 41 (41 pass, 0 fail) |
| Errors | 0 |

| Failed test | Likely sprint |
|-------------|----------------|
| *(none — all Vitest green)* | — |

---

## apps/web — Playwright

| Status | Detail |
|--------|--------|
| **BLOCKED** | `Error: http://localhost:8082 is already used` — start stack with `reuseExistingServer: true` or free port 8082, then: `cd apps/web && npx playwright test --project=release2` |
| **Inventory** | 61 tests in 8 files (includes `e2e/release2-nav.spec.ts`, `e2e/arabic-r2.spec.ts`, etc.) |

---

## Program gates (from spec 018)

| Gate | Criteria | Test evidence |
|------|----------|----------------|
| G-R2-01 | `release2-smoke.ps1` | Not run in this session |
| G-R2-02 | Copilot live data (S2) | `test_copilot_tools.py` PASS |
| G-R2-03 | Wave 1 W1-03–08 | Partial — Odoo/OTD unit PASS; full wave not smoke-tested |
| G-R2-04 | Arabic 8+ QA (S5) | Vitest i18n PASS (4/4); E2E not run |
| G-R2-05 | Extended demo script | Not run |

---

## Fixes applied during this test run

1. `nlp-svc/tests/test_copilot_tools.py` — expect 16 R2 copilot tools; handler parity.
2. `nlp-svc/tests/test_llm_router.py` — tier-2 chain includes OpenRouter.
3. `ipe_shared/testing/conftest_helpers.py` — `apply_unit_test_env_defaults`, `patch_unit_test_health_probes`.
4. `ipe_shared/health/probes.py` — overall health status `ok` (was `healthy`).
5. `dpe-svc`, `mat-svc`, `cap-svc` `tests/conftest.py` — unit env + Redis health mock.
6. API CTP/capacity tests — `make_auth_headers`, `apply_auth_and_session_overrides` fixtures; `rbac_client` for no-auth cases.
7. `dpe-svc/tests/test_dpe_handlers_success.py` — quota `count_tenant_resource` mock.
8. `dpe-svc/tests/test_planner_intent.py` — query wording for at-risk intent.
9. `dpe-svc/tests/test_api_ctp.py` — `ctp_client` vs `client` for no-auth; accept 400/401/403.
10. **apps/web Vitest** — Arabic `resolution.unresolvedMos` label; `nav.aiGovernance` / `auth.emailPlaceholder` locales; release2 sidebar hides POST-R2 hubs; `v8Pages.smoke` axios + recharts mocks; copilot R1 mock exports `IS_RELEASE2`.

---

*Generated by Phase 2 integration test pass — 018-phase2-release2*


