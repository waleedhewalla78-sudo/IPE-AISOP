# Implementation Log — Spec 018 Phase 2 Release 2

**Date**: 2026-07-10  
**Scope**: `/speckit.implement` — executed vs pending per sprint  
**Authority**: Repo audit + sprint reports in `sprints/`

---

## Wave 1 bridge (W1)

| Task | Status | Implementation | Tests / evidence |
|------|--------|----------------|------------------|
| W1-03 Odoo Config schema + API | ✅ | `services/connector/app/api/v1/odoo_config.py`, `core/odoo_config_service.py`, `schemas/odoo_config_v2.py` | `services/connector/tests/test_odoo_config_v2.py` |
| W1-04 Connection test <5s | ✅ | `POST /admin/odoo-config/test-connection` | Same test module |
| W1-05 Multi-entity + versioning | ✅ | `GET/POST /admin/odoo-config`, `/{entity_key}/versions`, rollback | Same test module |
| W1-06 Odoo Config React UI | ✅ | `apps/web/src/features/odoo-config/components/OdooConfigPage.tsx` | en + ar i18n keys |
| W1-07 OTD aggregation (5 KPIs) | ✅ | `services/dpe-svc/app/api/v1/otd_analytics.py` → `/analytics/otd/kpis` | `services/dpe-svc/app/core/otd_aggregation.py` |
| W1-08 OTD dashboard UI | ✅ | `apps/web/src/features/otd-analytics/OTDDashboardPage.tsx` | Recharts + filters |
| M-043 Odoo config migration | ✅ | `migrations/versions/043_odoo_config_versioning.py` | RLS on `cdm_odoo_config_version` |

**Wave 1 gate**: Odoo RLS + OTD tenant isolation — **unit tests pass**; integration smoke TBD

---

## Sprint S1 — R2 infrastructure ✅

| Task | Status | Implementation | Tests / evidence |
|------|--------|----------------|------------------|
| S1-01 R2 compose | ✅ | `infrastructure/docker/docker-compose.release2.yml` | — |
| S1-02 Kong R2 routes | ✅ | `infrastructure/docker/kong.release2.yml` | copilot, nlp, demand, scenario |
| S1-03 release2 profile | ✅ | `apps/web/src/lib/releaseProfile.ts` (`RELEASE2_HUBS`) | `Sidebar.tsx` |
| S1-04 Deploy scripts | ✅ | `scripts/deploy-release2.ps1`, `deploy-release2.sh` | — |
| S1-05 Smoke test | ✅ | `scripts/release2-smoke.ps1` | **docker run TBD** |
| S1-06 E2E nav | ✅ | `apps/web/e2e/release2-nav.spec.ts`, `tests/features/release2/release2-nav.test.tsx` | vitest PASS |

**Report**: `sprints/S1-report.md` · **Gate G-R2-01**: script ready, live PASS pending

---

## Sprint S2 — Copilot live data ✅

| Task | Status | Implementation | Tests / evidence |
|------|--------|----------------|------------------|
| S2-01 Planning tools (7 APIs) | ✅ | `services/nlp-svc/app/core/copilot_tools.py` — `get_mo_status`, `get_feasibility_queue`, `get_schedule`, `get_otd_metrics`, `get_material_availability`, `get_sync_status`, `get_resolution_scenarios` | httpx to dpe/fea/cap/mat/connector/res |
| S2-02 Shadow mode default | ✅ | `services/nlp-svc/app/core/copilot_agent.py` — `DEFAULT_SHADOW_MODE = True`, `COPILOT_SHADOW_MODE` setting | — |
| S2-03 LLM fallback chain | ✅ | `llm_client.py` + Ollama/Anthropic/OpenRouter backends | existing nlp-svc tests |
| S2-04 Copilot panel | ✅ | Copilot route + tenant header (inherits R1 W1-02) | `verify-copilot-r1-smoke.ps1` 12/12 |
| S2-05 Unit tests | ✅ | `services/nlp-svc/tests/test_copilot_tools_r2.py` | 7 mocked httpx tests |

**Gate G-R2-02**: ✅ engineering complete · live MO query smoke optional

---

## Sprint S3 — Demand (SES-first) ✅

| Task | Status | Implementation | Tests / evidence |
|------|--------|----------------|------------------|
| S3-01 SES forecaster | ✅ | `services/demand-svc/app/core/forecaster.py` | 7/14/30d horizons |
| S3-02 Forecast API | ✅ | `GET /api/v1/demand/forecast`, `/accuracy` | demand-svc router |
| S3-03 Control Tower overlay | ✅ | `ForecastOverlayWidget.tsx` in Control Tower | — |
| S3-04 Demand tab UI | ✅ | `DemandForecastPage.tsx` | Recharts + MAPE |
| S3-05 Tests | ✅ | `services/demand-svc/tests/test_forecaster_r2.py` | 7 passed |

**Report**: `sprints/S3-report.md`

---

## Sprint S4 — Scenario workbench ✅

| Task | Status | Implementation | Tests / evidence |
|------|--------|----------------|------------------|
| S4-01 Simulator KPI delta | ✅ | `services/scenario-svc/app/core/simulator.py` | demand %, delay days, capacity % |
| S4-02 simulate/list/get API | ✅ | `services/scenario-svc/app/api/v1/scenarios.py` | POST simulate, GET list/detail/compare |
| S4-03 Scenarios UI | ✅ | `ScenarioWorkbenchPage.tsx` | up to 3 saved scenarios |
| S4-04 Tests | ✅ | `services/scenario-svc/tests/test_simulator_r2.py` | 7 passed |

**Report**: `sprints/S4-report.md`

---

## Sprint S5 — Arabic 8+ screens ⬜

| Task | Status | Implementation | Tests / evidence |
|------|--------|----------------|------------------|
| S5-01 Expand `ar.json` | 🟡 partial | `apps/web/src/locales/ar.json` (~4.4k lines, baseline parity) | Not R2-screen-validated |
| S5-02 RTL layout validation | ⬜ | — | — |
| S5-03 Language toggle persistence | 🟡 partial | Existing i18n toggle | — |
| S5-04 `arabic-qa-r2.md` | ⬜ | **missing** | — |
| S5-05 `e2e/arabic-r2.spec.ts` | ⬜ | **missing** | — |

**Gate G-R2-04**: ⬜ blocked on native speaker sign-off

---

## Sprint S6 — OTD analytics extended 🟡 ~85%

| Task | Status | Implementation | Tests / evidence |
|------|--------|----------------|------------------|
| S6-01 OTD trend API | ✅ | `GET /analytics/otd/trend` | `otd_analytics.py` |
| S6-02 Root-cause API | ✅ | `GET /analytics/otd/root-cause` | — |
| S6-03 Cost-of-chaos API | ✅ | `GET /analytics/otd/cost-of-chaos` | `chaos_cost.py` |
| S6-04 Baseline comparison | ✅ | `GET /analytics/otd/baseline` + 014 `/otd-baseline` | — |
| S6-05 OTDDashboard + export | ✅ | `OTDDashboardPage.tsx` | PDF export TBD |
| S6-06 Migration 039 | ⬜ | **`039_cdm_otd_snapshot.py` missing** | — |

---

## Sprint S7 — Odoo admin polish 🟡 ~75%

| Task | Status | Implementation | Tests / evidence |
|------|--------|----------------|------------------|
| S7-01 DQ flags dashboard | ✅ | `OdooConfigPanel.tsx` — DQ flags table | admin i18n |
| S7-02 Sync history (last 10) | ✅ | `admin/api.ts` → `/sync/history` | — |
| S7-03 Partner wizard polish | 🟡 partial | Admin page scaffolding | UX review TBD |

> Core Odoo UI delivered in W1-06; S7 = extended guide scope.

---

## Sprint S8 — Multi-tenant ops ✅

| Task | Status | Implementation | Tests / evidence |
|------|--------|----------------|------------------|
| S8-01 Tenant health API | ✅ | `services/dpe-svc/app/api/v1/ops.py` → `/ops/tenants/health` | admin role |
| S8-02 Tenant alerts API | ✅ | `/ops/tenants/alerts` | sync failures |
| S8-03 OpsDashboard UI | ✅ | `apps/web/src/features/platform/components/OpsDashboard.tsx` | — |
| S8-04 Tests | ✅ | `services/dpe-svc/tests/test_ops_dashboard.py` | — |
| S8-05 Migration 040 | ✅ | `migrations/versions/040_cdm_tenant_health.py` | RLS |

---

## Sprint S9 — Production intelligence ✅

| Task | Status | Implementation | Tests / evidence |
|------|--------|----------------|------------------|
| S9-01 cap-svc analytics API | ✅ | `services/cap-svc/app/api/v1/analytics.py` | bottlenecks, utilisation, changeover |
| S9-02 Copilot quality tool | ✅ | `analyze_quality_patterns` in `copilot_tools.py` | — |
| S9-03 Tests | ✅ | `services/cap-svc/tests/test_analytics_production.py` | — |

---

## Sprint S10 — Supply chain intelligence ✅

| Task | Status | Implementation | Tests / evidence |
|------|--------|----------------|------------------|
| S10-01 Supplier risk API | ✅ | `services/mat-svc/app/api/v1/supply_chain.py` | — |
| S10-02 Inventory ABC / slow-moving | ✅ | `/supply-chain/inventory-abc`, `/slow-moving` | — |
| S10-03 Copilot SC tools | ✅ | `get_supplier_risk`, `get_inventory_abc`, etc. | — |
| S10-04 Tests | ✅ | `services/mat-svc/tests/test_supply_chain_intel.py` | — |
| S10-05 Migration 041 | ✅ | `migrations/versions/041_cdm_supplier_score.py` | RLS |

---

## Sprint S11 — S&OP synthesis ✅

| Task | Status | Implementation | Tests / evidence |
|------|--------|----------------|------------------|
| S11-01 `sop_report.py` | ✅ | `services/nlp-svc/app/core/sop_report.py` | — |
| S11-02 Reports API | ✅ | `services/nlp-svc/app/api/v1/reports.py` | POST/GET SOP |
| S11-03 SOPReport UI | ✅ | `apps/web/src/features/command-center/components/SOPReport.tsx` | PDF TBD |
| S11-04 Tests | ✅ | `services/nlp-svc/tests/test_sop_reports.py` | — |
| S11-05 Migration 042 | ✅ | `migrations/versions/042_cdm_sop_report.py` | RLS |

---

## Sprint S12 — SAP B1 — CUT ✅

| Task | Status | Reason |
|------|--------|--------|
| S12-ALL | **CUT** | Spec 017 §5; Strategy Assessment — no R2 implementation |

---

## Spec 014 overlap (already executed)

| 014 deliverable | Maps to 018 | Evidence |
|-----------------|-------------|----------|
| Planner-assist (T140–144) | S2 conversational access | `planner_assist.py`, `PlannerAssistPanel.tsx` |
| Outcomes dashboard (T120–122) | W1-08 / executive OTD proof | `OutcomesPage.tsx` |
| OTD baseline (T121) | W1-07 / S6-04 | `/analytics/otd-baseline` |
| `run-release2-demo.ps1` (T160) | G-R2-05 | `scripts/run-release2-demo.ps1` |

---

## NOT executed (pending)

| Area | Tasks | Blocker |
|------|-------|---------|
| S5 Arabic R2 QA | S5-04, S5-05, native sign-off | PH1-05 commercial |
| S6 migration | S6-06 migration 039 | alembic authoring |
| Migration reconcile | C-017: 043 vs 040–042 branch | P0 before prod migrate |
| Gate validation | G-R2-01 smoke, G-R2-05 demo extension | docker stack up |
| Tag | G-R2-TAG `v9.1.0-r2` | gates + S5 |

---

## Implement commands (next session)

```powershell
cd E:\AISOP\ipe

# G-R2-01 — R2 stack smoke
.\scripts\deploy-release2.ps1
.\scripts\release2-smoke.ps1

# Migration reconcile (C-017) — inspect heads first
cd migrations
alembic heads
# Create merge revision if 043 and 042 both present

# S5 starter
# Create docs/qa/arabic-qa-r2.md from PH1-05 checklist
```

---

*Implement v1.0 — 2026-07-10*
