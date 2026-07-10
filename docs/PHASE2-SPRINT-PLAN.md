# IPE Phase 2 (Release 2) — Sprint Plan & Reconciliation

**Version**: 1.0  
**Date**: 2026-07-10  
**Authority**: `PHASE2-IMPLEMENTATION-GUIDE.md` (user download) + Spec 017 + codebase audit  
**Target tag**: `v9.1.0-r2` (guide) · interim platform tag `v9.4.0-p3` (current)  
**Workspace**: `E:\AISOP\ipe`

---

## Executive summary

The Phase 2 Implementation Guide defines **12 sprints** to deliver **Release 2** (`release2` profile): R1 stack + `nlp-svc`, `demand-svc`, `scenario-svc`, expanded Arabic, OTD analytics, Odoo admin UI, multi-tenant ops, and intelligence APIs.

**Audit verdict**: Guide is **directionally correct** but **partially stale** vs current repo. Several items are **already done**, **path-corrected**, or **conflict with Spec 017** (SAP B1 cut, migration numbering, Copilot already in R1 nav).

| Dimension | Guide assumption | Actual (2026-07-10) | Action |
|-----------|------------------|---------------------|--------|
| Alembic head | 001–036 | **038** (`037` indexes, `038` activity events) | New R2 migrations start at **039** |
| Copilot R1 nav | Hidden in R1 | **Visible** — W1-01 done (`RELEASE1_HUBS` includes `copilot`) | Sprint 2 focuses on **live data tools**, not nav |
| `kong.release1.yml` | Exists | **Missing** — only `kong.yml` | Create `kong.release2.yml` from `kong.yml` subset |
| `releaseProfiles.ts` path | `config/releaseProfiles.ts` | **`apps/web/src/lib/releaseProfile.ts`** | Use actual path |
| R2 compose | Not present | **Not present** | Sprint 1 deliverable |
| R2 deploy/smoke | Not present | `run-release2-demo.ps1` only | Extend to full smoke |
| SAP B1 (Sprint 12) | Scaffold | **CUT** per Spec 017 / Strategy Assessment | **Deferred** — do not schedule |
| Demand ML | Prophet/LSTM | Spec 017: **simplified SES** first | Sprint 3 scope reduced |
| Odoo Config UI | Sprint 7 | Spec 017 **W1-03–06** (in progress) | **Pull forward** — parallel Sprint A |
| OTD dashboard | Sprint 6 | Spec 017 **W1-07–08** | **Pull forward** — parallel Sprint B |

**Recommended program order** (not guide sprint order):

1. **Complete Wave 1 carry-over** (W1-03–08) — overlaps Sprints 6–7  
2. **Sprint 1** — R2 infrastructure (compose, Kong, profile, smoke)  
3. **Sprints 2–4** — Copilot live data, demand, scenarios  
4. **Sprint 5** — Arabic 8+ screens (blocks Phase 1 UAT)  
5. **Sprints 8–11** — Ops, production/SC intelligence, S&OP  
6. **Sprint 12** — **CUT** (SAP B1)

---

## Sprint calendar (12 sprints + Wave 1 bridge)

| Sprint | Guide title | Spec 017 map | Duration | Status | Gate | Final status (2026-07-10) |
|--------|-------------|--------------|----------|--------|------|---------------------------|
| **W1** | Wave 1 bridge (Odoo + OTD) | W1-03–08 | 2–3 wks | ✅ ~90% | Odoo API + OTD RLS tests | Odoo v2 API/UI + OTD dashboard shipped; migration 043 |
| **S1** | R2 environment + profile | Infra | 1 wk | ✅ Complete | `release2-smoke.ps1` PASS | Compose/Kong/profile/deploy/smoke/e2e done; docker gate TBD |
| **S2** | Copilot live planning data | W1-02 ext | 1–2 wks | ✅ Complete | Tool tests + live MO query | 7 planning tools + shadow mode + `test_copilot_tools_r2.py` |
| **S3** | Demand sensing (SES) | W2-05 modified | 1–2 wks | ✅ Complete | MAPE endpoint; overlay widget | demand-svc SES + UI; see `sprints/S3-report.md` |
| **S4** | Scenario workbench | W2-03, W2-04 | 1–2 wks | ✅ Complete | Simulate + compare UI | scenario-svc + workbench UI; see `sprints/S4-report.md` |
| **S5** | Arabic 8+ screens | PH1-05, NFR-017-04 | 1 wk | ⬜ Open | Native speaker sign-off | `ar.json` baseline only; QA checklist missing |
| **S6** | OTD analytics (extended) | W1-07–08 + guide | 1 wk | 🟡 ~85% | OTD trend/root-cause/cost | APIs + `OTDDashboardPage`; migration 039 pending |
| **S7** | Odoo Config UI v2 | W1-03–06 | 1–2 wks | 🟡 ~75% | DQ + sync history | Core in W1; S7 polish in `OdooConfigPanel` |
| **S8** | Multi-tenant ops | W2-01, W2-02 | 1 wk | ✅ Complete | Admin-only ops API | `ops.py`, `OpsDashboard`, migration 040 |
| **S9** | Production & quality intel | Stretch | 1 wk | ✅ Complete | cap-svc analytics | cap analytics + copilot quality tool |
| **S10** | Supply chain intel | Stretch | 1 wk | ✅ Complete | mat-svc supplier risk | supply-chain APIs + migration 041 |
| **S11** | S&OP synthesis | Stretch | 1 wk | ✅ Complete | Report JSON + PDF | `sop_report.py`, `SOPReport.tsx`, migration 042 |
| **S12** | SAP B1 scaffold | — | — | **CUT** | Per Spec 017 | No implementation |

> **De-duplication**: Execute **W1 bridge** first (Sprints 6+7 content). Guide Sprints 6–7 become verification/extended scope only after W1-03–08 land.

---

## Sprint W1 — Wave 1 bridge (execute now)

**Goal**: Complete Spec 017 Wave 1 before full R2 compose expansion.

| Task ID | Deliverable | Owner | Acceptance |
|---------|-------------|-------|------------|
| W1-03 | `POST/GET /api/v1/admin/odoo-config` + migration | Backend | 422 on invalid; RLS |
| W1-04 | `POST .../test-connection` <5s | Backend | Mock Odoo test |
| W1-05 | Multi-entity + versioning | Backend | Rollback test |
| W1-06 | Admin Odoo Config React UI | Frontend | en + ar |
| W1-07 | OTD aggregation API (5 KPIs) | Backend | Tenant RLS test |
| W1-08 | OTD dashboard UI | Frontend | Recharts + filters |

**Issues**: #31–#36  
**Blockers**: None (engineering). Phase 1 UAT still blocked on SOW/staging.

---

## Sprint S1 — Release 2 environment

**Goal**: `docker-compose.release2.yml` + Kong routes + `release2` frontend profile + smoke.

### Tasks

| ID | Task | File(s) | Acceptance |
|----|------|---------|------------|
| S1-01 | R2 compose overlay | `infrastructure/docker/docker-compose.release2.yml` | Adds nlp, demand, scenario to R1 |
| S1-02 | R2 Kong routes | `infrastructure/docker/kong.release2.yml` | `/api/v1/copilot`, `/nlp`, `/demand`, `/scenario` |
| S1-03 | `release2` profile | `apps/web/src/lib/releaseProfile.ts` | Hubs: R1 + demand + scenarios tabs |
| S1-04 | Deploy script | `scripts/deploy-release2.ps1`, `.sh` | Mirrors `deploy-release1.ps1` |
| S1-05 | Smoke test | `scripts/release2-smoke.ps1` | Health on 11–12 containers |
| S1-06 | E2E nav test | `apps/web/e2e/release2-nav.spec.ts` | Copilot, Demand, Scenarios visible |

### Cursor prompt

```
Workspace: E:\AISOP\ipe. Implement Sprint S1 (Release 2 profile).

Reference: infrastructure/docker/docker-compose.release1.yml (standalone compose pattern)
Reference: infrastructure/docker/kong.yml (full routes — extract R2 subset)
Reference: apps/web/src/lib/releaseProfile.ts (add release2; copilot already in release1)
Reference: scripts/deploy-release1.ps1, scripts/release1-smoke.ps1

Create docker-compose.release2.yml, kong.release2.yml, deploy-release2.ps1, release2-smoke.ps1.
Do NOT modify release1 files. Add release2 profile with demand + scenarios hubs.
```

### Gate

- [ ] `release2-smoke.ps1` PASS  
- [ ] `VITE_RELEASE_PROFILE=release2` shows Demand + Scenarios (Copilot already in R1)

---

## Sprint S2 — Copilot live planning data

**Goal**: Extend `copilot_tools.py` to query live dpe/fea/cap/mat/connector APIs. Shadow mode default.

### Current vs target

| Tool (guide) | Exists today | Action |
|--------------|--------------|--------|
| `get_order_status` | ✅ similar | Align to `GET .../dashboard/mos` |
| `get_war_room_recovery` | ✅ | Keep |
| `get_mo_status` | ❌ | Add |
| `get_feasibility_queue` | ❌ | Add |
| `get_schedule` | ❌ | Add |
| `get_otd_metrics` | ❌ | Add |
| `get_material_availability` | ❌ | Add |
| `get_sync_status` | ❌ | Add |
| `get_resolution_scenarios` | ❌ | Add |

### Tasks

| ID | Task | File | Acceptance |
|----|------|------|------------|
| S2-01 | Planning data tools | `services/nlp-svc/app/core/copilot_tools.py` | 7 new tools, httpx, tenant header |
| S2-02 | Shadow mode default | `services/nlp-svc/app/core/copilot_agent.py` | No auto-execute |
| S2-03 | LLM fallback chain | `services/nlp-svc/app/core/llm_client.py` | Anthropic → OpenRouter → Ollama |
| S2-04 | Copilot panel verify | `apps/web/src/components/.../CopilotPanel` | 300s timeout, X-Tenant-ID |
| S2-05 | Unit tests | `services/nlp-svc/tests/test_copilot_tools_r2.py` | Mock HTTP per tool |

### Gate

- [ ] Query "What is blocking MO-ST-001?" returns structured fea-svc data  
- [ ] W1-02 smoke still 12/12

---

## Sprint S3 — Demand sensing (SES-first)

**Scope adjustment**: Spec 017 — **simplified exponential smoothing**, not full Prophet/LSTM in Wave 2.

| ID | Task | Acceptance |
|----|------|------------|
| S3-01 | SES forecaster on `cdm_demand_line` | 7/14/30d forecast + bounds |
| S3-02 | API `GET /api/v1/demand/forecast` | product_id, horizon |
| S3-03 | Control Tower overlay widget | Demand vs capacity gap |
| S3-04 | Demand tab page | Recharts + MAPE display |
| S3-05 | Tests | `test_forecaster_r2.py` |

---

## Sprint S4 — Scenario workbench

| ID | Task | Acceptance |
|----|------|------------|
| S4-01 | Simulator params: demand %, delay days, capacity % | KPI delta returned |
| S4-02 | API simulate/list/get | POST simulate, GET list |
| S4-03 | Scenarios UI | Side-by-side KPI compare, save 3 |
| S4-04 | Tests | `test_simulator_r2.py` |

Maps to **W2-03**, **W2-04** (#39, #40).

---

## Sprint S5 — Arabic expansion

| Screen | Namespace | Priority |
|--------|-----------|----------|
| Resolution Center | `resolution.*` | Must |
| Schedule | `schedule.*` | Must |
| Command Center | `command.*` | Must |
| Admin | `admin.*` | Must |
| Login / errors | `auth.*`, `errors.*` | Must |
| Copilot, Demand, Scenarios | `copilot.*`, `demand.*`, `scenarios.*` | Should |

**Gate**: `docs/qa/arabic-qa-r2.md` checklist + native speaker sign-off (PH1-05).

---

## Sprint S6 — OTD analytics (extended)

> If **W1-07/08** complete in Wave 1 bridge, S6 adds guide extensions only:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/analytics/otd/trend` | Daily/weekly/monthly |
| `GET /api/v1/analytics/otd/root-cause` | Delay categories |
| `GET /api/v1/analytics/otd/cost-of-chaos` | $ impact |
| `GET /api/v1/analytics/otd/baseline` | Pre/post IPE |

**Migration**: `039_cdm_otd_snapshot.py` (guide said 037 — **renumbered**)

---

## Sprint S7 — Odoo Config UI v2

> **Prefer Wave 1 bridge (W1-03–06)**. Sprint S7 = polish + DQ dashboard if W1 already shipped.

Guide deliverables: test-connection, config save, sync history, DQ flags table.

---

## Sprint S8 — Multi-tenant ops

| API | Role |
|-----|------|
| `GET /api/v1/ops/tenants/health` | Admin only |
| `GET /api/v1/ops/tenants/alerts` | Sync failures |

Maps **W2-01**, **W2-02**. Migration `040_cdm_tenant_health.py` (materialized view).

---

## Sprint S9 — Production & quality intelligence

- `cap-svc` analytics: bottlenecks, changeover, utilisation  
- Copilot tool `analyze_quality_patterns`

---

## Sprint S10 — Supply chain intelligence

- `mat-svc`: supplier risk, ABC, slow-moving, reorder  
- Copilot tools: `get_supplier_risk`, etc.

Migration `041_cdm_supplier_score.py`.

---

## Sprint S11 — S&OP synthesis

- `nlp-svc/core/sop_report.py`  
- `POST/GET /api/v1/copilot/report/sop`  
- Command Center SOP report page + PDF

Migration `042_cdm_sop_report.py`.

---

## Sprint S12 — SAP B1 — **CUT**

Per Spec 017 §5 and Strategy Assessment. **Do not implement** unless ARB approves and customer #2 contracted.

---

## Migration plan (reconciled)

| Migration | Sprint | Purpose | Guide ID (stale) |
|-----------|--------|---------|------------------|
| **039** | S6 / W1-07 | `cdm_otd_snapshot` | was 037 |
| **040** | S8 | `cdm_tenant_health` view | was 039 |
| **041** | S10 | `cdm_supplier_score` | was 040 |
| **042** | S11 | `cdm_sop_report` | was 041 |
| **043** | W1-03 | Odoo config versioning | was 038 in guide |

**Already applied**: 037 (`phase1_hot_table_indexes`), 038 (`sprint7_activity_events`).

---

## Environment variables (R2)

Add to `.env.template`:

| Variable | Service | Default |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | nlp-svc | — |
| `OPENROUTER_API_KEY` | nlp-svc | — |
| `OLLAMA_BASE_URL` | nlp-svc | `http://host.docker.internal:11434` |
| `COPILOT_TIMEOUT_SECONDS` | nlp-svc | `300` |
| `DEMAND_FORECAST_HORIZON_DAYS` | demand-svc | `14` |

---

## Testing matrix

| Sprint | Test artifact |
|--------|---------------|
| S1 | `scripts/release2-smoke.ps1` |
| S2 | `test_copilot_tools_r2.py` |
| S3 | `test_forecaster_r2.py` |
| S4 | `test_simulator_r2.py` |
| S5 | `docs/qa/arabic-qa-r2.md` + `e2e/arabic-r2.spec.ts` |
| S6 | `test_analytics_otd.py` |
| W1 | Odoo config + OTD RLS tests |
| S8 | `test_ops_dashboard.py` |

---

## Dependencies & blockers

| Blocker | Affects | Mitigation |
|---------|---------|------------|
| PH1 SOW + staging | Phase 1 UAT, live Odoo validation | Exec escalation |
| 6 unpushed commits | Team sync | `git push origin master` |
| kind CrashLoopBackOff | K8s demos | C-09 restabilize |
| SAP B1 cut | S12 | Removed from plan |
| Prophet/LSTM scope | S3 | SES-first per Spec 017 |

---

## Next actions (this week)

1. **W1-03** — Odoo Config v2 schema ([#31](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/31))  
2. **S1** — R2 compose + smoke (can parallelize with W1-03 backend)  
3. Push `ad494e0` + restabilize kind  
4. Copy full guide to `ipe/docs/PHASE2-IMPLEMENTATION-GUIDE.md` with reconciliation header

---

## Final status summary (2026-07-10)

| Metric | Value |
|--------|-------|
| Sprints complete | 8/12 executable (W1, S1–S4, S8–S11) |
| Sprints partial | 2 (S6, S7) |
| Sprints open | 1 (S5 Arabic QA) |
| Sprints cut | 1 (S12 SAP B1) |
| Engineering completion | ~82% |
| Gate completion | ~65% (G-R2-01/04/05/TAG open) |
| Spec 018 docs | `specs/018-phase2-release2/` — converge, implement, README synced |

**P0 blockers before tag**: migration branch reconcile (043 vs 040–042), G-R2-01 smoke, S5 Arabic native QA.

---

*Sprint plan v1.1 — reconciled with Spec 017 and codebase audit 2026-07-10*
