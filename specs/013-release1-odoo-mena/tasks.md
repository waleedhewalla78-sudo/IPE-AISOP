# Tasks — 013 Release 1 Odoo + MENA Go-Live

**Feature**: `013-release1-odoo-mena`  
**Version**: 2.1 (post-implement)  
**Date**: 2026-06-24  
**Readiness**: 92/100  
**Gate**: `release1-smoke.ps1` PASS + Star Trans UAT (T071) → tag `v9.0.0-r1` (T073)

---

## Summary

| Phase | Done | Total | Status |
|-------|------|-------|--------|
| 0 Business | 2 | 5 | Blocked on T002, T003 |
| A Connector | 12 | 12 | ✅ Complete (+ inventory) |
| B Data quality | 11 | 11 | ✅ Complete |
| C Deploy | 7 | 8 | T037 manual VM pending |
| D Arabic/UI | 11 | 11 | ✅ Complete |
| E Docs | 13 | 14 | T066–T067 optional |
| F Closure | 2 | 4 | T071, T073 pending |
| **G Pre-UAT gaps** | 4 | 5 | T086 customer sign-off pending |
| **H R1.1 hardening** | 4 | 4 | ✅ Complete (T081 vault) |

---

## Phase 0 — Business prerequisites

| ID | Task | Priority | Status | Owner | Evidence / next step |
|----|------|----------|--------|-------|----------------------|
| T000 | Lock OQ-1: Star Trans customer #1 | P0 | ✅ | Business | `clarify.md` OQ-1 |
| T001 | Lock OQ-3: Odoo 17.0 + mrp | P0 | ✅ | Business | `clarify.md` OQ-3 |
| T002 | Sign PoC/SOW ($24K/yr + $18K impl suggested) | P0 | 🟡 | Commercial | Template ready: `R1-CUSTOMER-SOW-TEMPLATE.md` — fill pricing + sign |
| T003 | Odoo staging credentials + API access | P0 | ⬜ | Customer IT | **Critical path blocker** — url, db, user, password |
| T004 | Second prospect discovery (name + ERP) | P1 | ⬜ | Business | Parallel only; no eng until T071 |

---

## Phase A — Odoo connector ✅

| ID | Task | Status | Evidence |
|----|------|--------|----------|
| T010 | Migration 036 (sync_run, data_quality_flag, MO cols) | ✅ | `migrations/versions/036_r1_odoo_sync_tables.py` |
| T011 | RLS on new tables | ✅ | `test_r1_sync_tables_rls.py` |
| T012 | Mapper MO/BOM/WC/product Odoo 17 | ✅ | `app/core/mapper.py` |
| T013 | MO sync upsert | ✅ | `app/odoo/sync_engine.py` |
| T014 | BOM header sync upsert | ✅ | sync_engine |
| T015 | WC sync upsert | ✅ | sync_engine |
| T016 | Product update path | ✅ | sync_engine |
| T017 | sync_all execution order | ✅ | `run_full_sync()` |
| T018 | Mapper unit tests (10+) | ✅ | `tests/test_odoo_mapper.py` |
| T019 | MO sync unit tests | ✅ | `tests/test_odoo_sync_mo.py` |
| T020 | Persist cdm_sync_run | ✅ | sync_engine |

---

## Phase B — Data quality + feasibility

| ID | Task | Priority | Status | Evidence |
|----|------|----------|--------|----------|
| T021 | `_validate_mo_for_scoring` | P0 | ✅ | sync_engine |
| T022 | fea-svc skip scoring on DQ flags | P0 | ✅ | `scorer.py` |
| T023 | Queue API includes data_quality_flags | P0 | ✅ | `feasibility.py` |
| T024 | SYNC_CONFLICT detection | P0 | ✅ | sync_engine |
| T025 | Integration: MO sync → feasibility queue | P0 | ✅ | `test_odoo_sync_integration.py` |
| T026 | Integration: bad BOM → DQ flag in queue | P0 | ✅ | `test_validate_mo_missing_routing_sets_dq_flag` |
| T027 | GET /sync/status + /data-quality | P0 | ✅ | `app/api/v1/sync.py` |
| T028 | 15-min APScheduler | P0 | ✅ | `jobs/sync_scheduler.py` |
| T029 | Tenant Odoo config in config JSONB | P0 | ✅ | sync creds helper |

---

## Phase C — Deploy + write-back

| ID | Task | Priority | Status | Evidence |
|----|------|----------|--------|----------|
| T030 | cap-svc → connector direct activate | P0 | ✅ | `erp_direct.py`, `ERP_SYNC_MODE=direct` |
| T031 | release1 profile env messaging | P0 | ✅ | compose env |
| T032 | docker-compose.release1.yml (8 svc incl. fea-svc) | P0 | ✅ | `infrastructure/docker/` |
| T033 | kong.release1.yml | P0 | ✅ | `infrastructure/kong/` |
| T034 | deploy-release1.ps1 | P0 | ✅ | `scripts/` |
| T035 | release1-smoke.ps1 | P0 | ✅ | `scripts/` |
| T036 | CI job: release1 compose smoke | P1 | ✅ | `.github/workflows/ci.yml` release1-smoke job |
| T037 | Windows 8GB VM deploy validation | P1 | 🟡 | `R1-8GB-VM-DEPLOY-NOTES.md` — manual sign-off |

---

## Phase D — Arabic + UI

| ID | Task | Priority | Status | Evidence |
|----|------|----------|--------|----------|
| T040 | i18n framework en + ar | P0 | ✅ | `lib/i18n.ts`, locales |
| T041 | RTL document.dir | P0 | ✅ | `setLocale()` |
| T042 | Arabic Control Tower strings | P0 | ✅ | `ar.json` + page |
| T043 | Arabic Resolution strings in JSON | P0 | ✅ | T084 wired Resolution + Login |
| T044 | Arabic nav strings | P0 | ✅ | Sidebar + locales |
| T045 | LanguageSwitcher component | P0 | ✅ | component |
| T046 | SyncStatusBar widget | P0 | ✅ | component |
| T047 | Data quality badges on Control Tower | P0 | ✅ | ControlTowerPage |
| T048 | release1 nav profile (hide POST-R1 hubs) | P0 | ✅ | `releaseProfile.ts` |
| T049 | Admin Odoo connection test UI | P1 | ✅ | AdminPage Odoo tab + `/admin/erp/odoo` |
| T050 | Vitest ar locale smoke | P0 | ✅ | `tests/lib/i18n.test.ts` |

---

## Phase E — Documentation

| ID | Task | Priority | Status | Evidence |
|----|------|----------|--------|----------|
| T060 | R1-IMPLEMENTATION-PLAYBOOK | P0 | ✅ | `docs/implementation/` |
| T061 | R1-SUPPORT-RUNBOOK | P0 | ✅ | `docs/runbooks/` |
| T062 | ODOO-CONNECTOR-INSTALL | P0 | ✅ | `docs/integration/` |
| T063 | ODOO-FIELD-MAPPING-WORKSHEET | P0 | ✅ | Template — fill at kickoff |
| T064 | export-roi-metrics.ps1 | P1 | ✅ | `scripts/` |
| T065 | OTD baseline procedure in playbook | P1 | ✅ | playbook §90-day |
| T066 | PRODUCT-STATUS R1 track doc | P2 | ⬜ | Optional |
| T067 | PRD v8.2.0 R1 addendum | P2 | ⬜ | Optional |
| T091 | Customer SOW template | P0 | ✅ | `docs/implementation/R1-CUSTOMER-SOW-TEMPLATE.md` |
| T092 | Data quality acceptance checklist | P0 | ✅ | `docs/implementation/R1-DATA-QUALITY-ACCEPTANCE-CHECKLIST.md` |
| T093 | Training curriculum (planner/manager/CEO) | P0 | ✅ | `docs/implementation/R1-TRAINING-CURRICULUM.md` |
| T094 | Customer support guide (non-engineers) | P0 | ✅ | `docs/runbooks/R1-CUSTOMER-SUPPORT-GUIDE.md` |

---

## Phase F — Closure

| ID | Task | Priority | Status | Depends on |
|----|------|----------|--------|------------|
| T070 | feature.json → 013 active, readiness 88 | P0 | ✅ | `.specify/feature.json` |
| T071 | Star Trans UAT sign-off | P0 | ⬜ | T003, T086, live Odoo |
| T072 | converge.md updated | P0 | ✅ | This speckit refresh |
| T073 | Git tag `v9.0.0-r1` | P0 | ⬜ | T071 |

---

## Phase G — Pre-UAT engineering gaps (NEW)

| ID | Task | Priority | Status | Acceptance criteria |
|----|------|----------|--------|---------------------|
| T080 | Sync BOM lines + routing operations from Odoo 17/19 | **P0** | ✅ | `sync_bom_details()` in sync_engine |
| T082 | Post-sync feasibility rescore hook | **P0** | ✅ | `_rescore_synced_mos()` → fea-svc |
| T084 | Wire Resolution Center + Login to i18n `t()` | **P0** | ✅ | locales + pages wired |
| T085 | SYNC_CONFLICT badge on Control Tower MO card | P1 | ✅ | fea queue + ControlTowerPage |
| T086 | Field mapping worksheet completed with Star Trans | **P0** | 🟡 | Template at `docs/integration/customers/startrans/` — customer sign-off pending |

---

## Phase H — R1.1 hardening (post-UAT)

| ID | Task | Priority | Status | Notes |
|----|------|----------|--------|-------|
| T049 | Admin Odoo config UI | P1 | ✅ | AdminPage Odoo tab |
| T081 | Encrypted Odoo credentials (vault/KMS) | P1 | ✅ | `odoo_credentials.py` + shared KMS volume |
| T083 | web-ui service in release1 compose (nginx) | P1 | ✅ | `Dockerfile.release1` |
| T087 | Sync failure alert (email/WhatsApp webhook) | P1 | ✅ | `sync_alerts.py` |
| T088 | stock.quant / material availability sync | P2 | ✅ | `sync_inventory()` |
| T089 | OTD baseline capture API | P2 | ✅ | `GET/POST /analytics/otd-baseline` |
| T090 | MOs saved ROI metric instrumentation | P2 | ✅ | `GET /analytics/roi-metrics`, `POST .../mos-saved` |

---

## Critical path (next 2 weeks)

```text
1. T002 + T003          ← business unblock (parallel)
2. T086 customer sign-off ← field mapping workshop
3. T071 UAT on staging
4. T073 tag v9.0.0-r1
```

---

## UAT checklist (T071)

- [ ] Odoo staging: MOs appear in Control Tower within 15 min of Odoo change
- [ ] ≥80% active MOs scorable (SC-R1-05)
- [ ] At-risk MO shows in queue with feasibility score
- [ ] Resolution scenario generated and selectable
- [ ] Schedule approve updates Odoo `date_planned_start`
- [ ] Data quality flag shown for intentionally broken MO (missing BOM test)
- [ ] Arabic Control Tower + Resolution readable by native speaker
- [ ] Sync status bar shows last run time and success
- [ ] Support runbook walkthrough with customer IT
- [ ] 90-day ROI clock start date recorded

---

## Commands reference

```powershell
# Deploy release1 stack
cd E:\AISOP\ipe
.\scripts\deploy-release1.ps1

# Smoke test
.\scripts\release1-smoke.ps1

# Web UI (release1 profile)
cd apps\web
$env:VITE_RELEASE_PROFILE = "release1"
$env:VITE_DEFAULT_LOCALE = "ar"
npm run dev

# Apply migrations
cd migrations
$env:IPE_DATABASE_URL_SYNC = "postgresql://ipe:ipe@localhost:5433/ipe"
uv run alembic upgrade head

# Connector tests
cd services\connector
uv run pytest tests/test_odoo_mapper.py tests/test_odoo_sync_mo.py -q
```

---

*Generated by `/speckit.tasks` v2.0 — 2026-06-29.*
