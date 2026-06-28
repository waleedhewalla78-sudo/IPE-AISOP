# IPE Product Status — Closed Topics Summary

**Version:** v8.2.0  
**Date:** 2026-06-28  
**Repository:** [IPE-AISOP](https://github.com/waleedhewalla78-sudo/IPE-AISOP)

---

## Executive verdict

| Phase | Status |
|-------|--------|
| **v7 core (APS, V6 features, hub consolidation)** | ✅ Complete — historical 20/20 demo, 6/6 chaos |
| **v8 Phase 1 (U1–U3)** | ✅ Validated — demand, scenario, role copilot |
| **v8 Phase 2 (U4–U6)** | ✅ Validated — supply, orders, equipment |
| **v8 Phase 3 (U7–U8)** | ✅ Validated — design AI, procurement |
| **v8.2.0 closure** | ✅ P1/P2 closed, POST-B scaffolds ready |
| **Staging / UAT / Demo** | ✅ Ready — **32/32** demo checkpoints |
| **Production deployment** | ❌ POST-B — Keycloak, secrets vault, Stripe live, SAP/D365 live |

---

## v8 feature matrix (SAP gap upgrade)

| Stream | Capability | Service | Port | Unit/API tests | Demo CP |
|--------|------------|---------|------|----------------|---------|
| **U1** | Role-based Copilot + sessions | `nlp-svc` | 8007 | ✅ | CP30 |
| **U2** | Demand sensing & forecasting (SES/Prophet/LSTM) | `demand-svc` | 8040 | ✅ 10+ tests | CP21–22 |
| **U3** | Scenario workbench | `scenario-svc` | 8050 | ✅ 6 tests | CP23–24 |
| **U4** | Multi-echelon supply (4 plants, 6 lanes seeded) | `supply-svc` | 8060 | ✅ 5 tests | CP25 |
| **U5** | Order management / ATP | `order-svc` | 8070 | ✅ 5 tests | CP26 |
| **U6** | Equipment intelligence | `equipment-svc` | 8061 | ✅ 5 tests | CP27 |
| **U7** | Product Design AI | `material-svc` | 8090 | ✅ 6 tests | CP28 |
| **U8** | Responsible procurement | `procurement-svc` | 8100 | ✅ 8 tests | CP29 |
| **Ext** | Sustainability dashboard | `sustain-svc` | 8012 | ✅ | CP31 |
| **Ext** | Quality intelligence | `quality-svc` | 8013 | ✅ | CP32 |

**Migrations:** 029–031 (v8 phases), 032 (head merge), 033 (v8 RLS WITH CHECK), **034** (supply seed), **035** (legacy RLS INSERT)

---

## Platform snapshot

| Item | Value |
|------|-------|
| Speckit readiness | **100/100** |
| Demo checkpoints | **32/32** |
| Microservices | 22 Kong-routed backends |
| API gateway | Kong @ `:8000` |
| Web app | Vite React @ `:8082` |
| Database | PostgreSQL 16 + RLS (WITH CHECK on legacy tables) |
| Events | Kafka — includes `ipe.supply.adjusted` feedback topic |
| **dpe-svc tests** | **~180** |
| Backend tests (all services) | **870+** |
| Frontend Vitest | **28/28** |
| Playwright E2E | **4 specs** — `apps/web/e2e/login`, `copilot`, `demand-tab`, `supply-tab` |
| v8 integration | **5/5** — `tests/integration/test_v8_e2e.py` |
| Demo script | `scripts/run-full-demo.ps1` |

---

## Validation evidence

| Check | Result | Artifact |
|-------|--------|----------|
| Demo 32/32 | PASS | `docs/qa-e2e-demo-v8.2.0-closure.txt` |
| Demo post-chaos | PASS (target) | `docs/qa-e2e-demo-v8.2.0-post-chaos.txt` |
| Chaos C1–C6 post-v8 | PASS (target) | `docs/chaos/chaos-post-v8-output.txt` |
| v8 integration | 5/5 | `tests/integration/test_v8_e2e.py` |
| RLS INSERT legacy | PASS | `tests/integration/test_rls_insert_legacy.py` |
| Supply feedback consumer | PASS | `services/demand-svc/tests/test_supply_feedback_e2e.py` |
| Full test suite | PASS | `docs/qa/full-test-suite-v8.2.0.txt` |
| Playwright E2E | PASS | `docs/qa/playwright-v8.2.0.txt` |

---

## Production blockers (POST-B activation)

| ID | Item | Scaffold |
|----|------|----------|
| C-007 | Keycloak SSO | `ipe_shared/auth/keycloak.py` |
| SEC-P0 | Secrets vault | `config/secrets_manager.py` |
| BILL-P1 | Stripe live | `ipe_shared/billing/stripe_adapter.py` |
| RLS-P1 | Prod RLS verify | migration **035** |
| ERP-P2 | SAP/D365 live | `connector/app/erp/base.py` |

See `docs/DEPLOYMENT-READINESS-v8.2.0.md`.

---

## How to run

```powershell
cd E:\AISOP\ipe
.\scripts\wait-for-healthy-stack.ps1
.\scripts\run-full-demo.ps1 -ReportPath docs\qa-e2e-demo-v8.2.0-closure.txt
uv run pytest tests/integration/test_v8_e2e.py -m integration -v
cd apps\web; npx playwright test e2e/login.spec.ts --reporter=list
```
