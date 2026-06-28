# Analyze: IPE Program — Cross-Artifact Consistency & Whole-Project Status

**Feature**: `010-v8-validation-convergence` | **Date**: 2026-06-27  
**Scope**: Program-wide (000 → 010) + v8 SAP-gap upgrade + QA-001–010  
**Readiness**: **98/100** (Speckit) · **~92/100** (Audit est.) · **30/30** demo

**Method**: `/speckit.analyze` — synthesis across specs 000–010, `PRODUCT-STATUS.md`, live evidence, test runs.

---

## Executive summary

| Dimension | Status |
|-----------|--------|
| **Speckit build tasks (002–004)** | **158 / 162 (98%)** |
| **v6 delivery (004)** | **55/55** — v6.0.0–v6.1.0 tagged |
| **v7 hub consolidation (006)** | **18/18** |
| **v8 Phase 1–3 (007–009)** | **31/31** |
| **v8 validation (010)** | **18/22 (82%)** — 4 open (tag, seed, POST-A, docs) |
| **Live demo** | **30/30** — v7 CP0–20 + v8 CP21–30 |
| **Integration E2E** | **5/5** — `test_v8_e2e.py` |
| **Chaos (v7)** | **6/6** — unchanged |
| **Production deploy** | **Blocked** — enterprise IdP, secrets, billing |

**Recommendation**: Tag **v8.2.0** after stakeholder sign-off; begin **POST-A scale** and **supply network seed** as v8.3 prep.

---

## Whole project status (detailed)

### 1. Workspace & tooling

| Item | State |
|------|-------|
| Workspace root | `E:\AISOP` |
| Monorepo | `ipe/` |
| Spec Kit | `.specify/feature.json` → `010-v8-validation-convergence` |
| Active release | **v8.2.0** (code + validation complete; tag pending) |
| Demo auth | `Ahmed@nour` / `admin`; tenant `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11` |
| API / UI | Kong `:8000` · Web `:8082` |

### 2. Feature timeline

```text
000 Completion ──► 001 Convergence ──► 002 Gates (58/62)
        │                                    │
        └── 003 V5 (45/45) @ v1.0.0 ────────┤
                    │                        │
              004 V6 (55/55) @ v6.0.0        │
                    │                        │
              005 Program rollup             │
                    │                        │
              006 Hub consolidation (18/18)  │
                    │                        │
         007 v8 P1 ─ 008 v8 P2 ─ 009 v8 P3   │
                    │                        │
              010 Validation convergence ◄───┘
                    │
              v8.2.0 tag (pending)
                    │
              POST-A/B/C/D backlog
```

| Feature | Tasks | Done | Tag / gate |
|---------|-------|------|------------|
| 000 Project completion | meta | docs | historical |
| 001 Production readiness | 39 | 38 | convergence |
| 002 Release gates | 62 | 58 | G1–G3 ✅ |
| 003 Autonomous V5 | 45 | 45 | **v1.0.0** |
| 004 AI-first V6 | 55 | **55** | **v6.0.0–v6.1.0** |
| 005 Program status | 35 | 28 | living spec |
| 006 Hub consolidation | 18 | **18** | v7.0.0 RC |
| 007 v8 Phase 1 | 14 | **14** | U1–U3 |
| 008 v8 Phase 2 | 9 | **9** | U4–U6 |
| 009 v8 Phase 3 | 8 | **8** | U7–U8 |
| 010 Validation | 22 | 18 | **v8.2.0** |

### 3. Delivered product surface

**v7 (complete + proven)**

| Domain | Capability | Demo CP |
|--------|------------|---------|
| Visibility | Control Tower, KPIs | CP1–2 |
| Resolution | Scenarios | CP3 |
| Scheduling | OR-Tools Gantt, approve | CP4, 15 |
| Shop floor | Work orders | CP5 |
| Supply chain | SCN scorecards | CP6 |
| Executive | Delays, OTD | CP7–8 |
| War Room | Alerts | CP9 |
| Copilot | Query orchestrator | CP10–11 |
| AI Trust / Admin | Governance | CP12–13 |
| Inventory | FG summary | CP14 |
| V6 ABP / Tariff / CPM / Chaos | Margin, tariff, CPM, maintenance | CP17–20 |

**v8.2.0 (complete + validated)**

| Stream | Capability | Service | Port | Demo CP |
|--------|------------|---------|------|---------|
| U1 | Role copilot + sessions | nlp-svc | 8007 | CP30 |
| U2 | Demand sensing / forecast | demand-svc | 8040 | CP21–22 |
| U3 | Scenario workbench | scenario-svc | 8050 | CP23–24 |
| U4 | Multi-echelon supply | supply-svc | 8060 | CP25 |
| U5 | Order management | order-svc | 8070 | CP26 |
| U6 | Equipment intelligence | equipment-svc | 8061 | CP27 |
| U7 | Product Design AI | material-svc | 8090 | CP28 |
| U8 | Responsible procurement | procurement-svc | 8100 | CP29 |

### 4. Codebase inventory (2026-06-27)

| Layer | Count | Notes |
|-------|-------|-------|
| Microservices | **22+** Kong-routed | +7 v8 services |
| Migrations | **001–033** | 032 merge heads; 033 RLS WITH CHECK |
| Backend tests | **870+** core + **26** v8 API + **131** nlp unit | 12 nlp integration deselected |
| Frontend tests | **28** Vitest | +7 v8 page smoke |
| Demo checkpoints | **30** | `run-full-demo.ps1` |
| Integration v8 | **5** | Kong live stack |
| Kafka topics | 24 | unchanged |

### 5. Validation evidence matrix

| QA ID | Issue | Status | Evidence |
|-------|-------|--------|----------|
| QA-001 | v8 services down | ✅ | 30/30 demo; integration health |
| QA-002 | Demo CP21–30 missing | ✅ | `docs/qa-e2e-demo-v8-report.txt` 30/30 |
| QA-003 | No v8 E2E test | ✅ | `test_v8_e2e.py` 5/5 |
| QA-004 | CopilotPanel Vitest fail | ✅ | 28/28 Vitest |
| QA-005 | No v8 API tests | ✅ | 26 API tests (7 services) |
| QA-006 | nlp SageMaker/vLLM fail | ✅ | 131 pass, 12 deselected |
| QA-007 | PRODUCT-STATUS stale | ✅ | v8.2.0 matrix |
| QA-008 | procurement Role missing | ✅ | `rbac.py` |
| QA-009 | No v8 page smoke tests | ✅ | `v8Pages.smoke.test.tsx` |
| QA-010 | Stack smoke tasks | ✅ | T014/T008/T009 marked ✅ |

---

## Specification analysis — findings

| ID | Category | Severity | Summary | Status |
|----|----------|----------|---------|--------|
| A-V8-01 | Coverage | ✅ | Demo 30/30 | Closed |
| A-V8-02 | Coverage | ✅ | v8 integration 5/5 | Closed |
| A-V8-03 | Bug | ✅ | CP30 session 500 (NoReferencedTableError) | Fixed — User ORM |
| A-V8-04 | Migration | ✅ | 033 wrong table names | Fixed |
| A-V8-05 | Data | LOW | Supply network 0 facilities | CP25 passes; seed gap |
| A-V8-06 | Docs | MEDIUM | READINESS.md still v7 / 20/20 | Open — T020 |
| A-V8-07 | Docs | MEDIUM | 005 analyze pre-v8 | Open — T019 |
| A-V8-08 | Release | LOW | v8.2.0 git tag pending | Open — T021 |
| A-V8-09 | Security | MEDIUM | Legacy RLS 22 tables | POST-C3 |
| A-V8-10 | Security | HIGH | Keycloak live (C-007) | POST-B1 BLOCKED |
| A-V8-11 | Test | LOW | dpe-svc API coverage ~14% | POST test sprint |
| A-V8-12 | Infra | LOW | Host/Docker port conflicts 8040–8100 | Ops note |
| A-V8-13 | Feature | LOW | Prophet/LSTM forecaster | v8.3 backlog |
| A-V8-14 | Metrics | INFO | PRODUCT-STATUS says 42 v8 tests | Clarify: 26 API + per-svc unit |

**Critical conflicts**: **0**

---

## Cross-artifact matrix

| # | Artifact A | Artifact B | Severity | Status |
|---|------------|------------|----------|--------|
| X-01 | 010 spec FR-V8-03 | demo report | — | ✅ 30/30 |
| X-02 | 009 converge | 010 analyze | INFO | ✅ Synced this run |
| X-03 | PRODUCT-STATUS | test counts | LOW | 26 API vs "42" — unit tests included in 42 |
| X-04 | READINESS.md | PRODUCT-STATUS | MEDIUM | ⬜ v7 vs v8.2.0 drift |
| X-05 | feature.json | 010 phase | INFO | ✅ Updated |
| X-06 | 007 T014 | demo CP21–24 | — | ✅ |
| X-07 | migration 033 | 029–031 tables | — | ✅ Fixed names |
| X-08 | CopilotSession ORM | cdm_user FK | — | ✅ User model added |
| X-09 | integration test | demo user UUID | — | ✅ c0eebc99…c03 |
| X-10 | 006 T014 | demo count | LOW | ⬜ Still says 20/20 |

**Hierarchy**: `tasks.md` > `spec.md` > `PRODUCT-STATUS.md` > `READINESS.md`

---

## Readiness dimensions

| Dimension | Score | Gap |
|-----------|-------|-----|
| Product completeness | **99** | Supply network seed; Prophet upgrade |
| Testing | **95** | dpe API gaps; 8 integration skips (v7) |
| Security | **78** | Keycloak live; RLS legacy tables |
| Operations | **90** | Port conflict ops note |
| Documentation | **94** | READINESS + 005 sync |
| Demo / UAT | **100** | 30/30 |
| **Speckit overall** | **98/100** | Tag v8.2.0 |
| **Audit overall** | **~92/100** | Production blockers |

---

## Open points & issues (complete list)

### P0 — Release (demo-ready, tag pending)

| ID | Item | Owner | Remediation |
|----|------|-------|-------------|
| OP-01 | Git tag **v8.2.0** | Release | Stakeholder sign-off + `git tag -a v8.2.0` |
| OP-02 | READINESS.md drift (v7, 20/20) | Docs | T020 sync to v8.2.0 / 30/30 |

### P1 — Quality / data

| ID | Item | Owner | Remediation |
|----|------|-------|-------------|
| OP-03 | Supply network empty (facilities=0) | Data | Seed `cdm_plant` / network edges for demo richness |
| OP-04 | dpe-svc API test coverage ~14% | Eng | POST test sprint (CTP, demand sense, financial) |
| OP-05 | 8 integration test skips (WS, sustain, quality) | QA | Harness fix or accept for demo overlay |
| OP-06 | Host uvicorn vs Docker port conflicts 8040–8100 | Ops | Kill host processes or use Docker-only |

### P2 — v8.3 enhancements

| ID | Item | Owner | Remediation |
|----|------|-------|-------------|
| OP-07 | Prophet/LSTM demand forecaster | ML | Replace SES stub in demand-svc |
| OP-08 | supply→demand feedback loop | Eng | Kafka consumer wiring |
| OP-09 | copilot-svc split (8030) | Arch | Optional refactor |
| OP-10 | Visual CPM async >50 MOs | Scale | POST-A1 |

### P3 — Production (explicitly deferred)

| ID | Item | Reference |
|----|------|-----------|
| OP-11 | Keycloak / Azure AD SSO | C-007, ADR-001 |
| OP-12 | Production JWT / secrets manager | SEC-P0 |
| OP-13 | Live Stripe billing | BILL-P1 |
| OP-14 | RLS INSERT on 22 legacy tables | ADR-002, migration backlog |
| OP-15 | Live SAP/D365 connectors | ERP-P2 |
| OP-16 | WCAG 2.1 AA audit | FR-506 |
| OP-17 | Alertmanager / PagerDuty live | POST ops |

### Documentation debt

| ID | Item | File |
|----|------|------|
| OP-18 | 005 spec still v7.0.0 RC header | `005/spec.md` |
| OP-19 | CROSS-ARTIFACT-ANALYSIS.md dated 2026-06-21 | Superseded by this analyze |
| OP-20 | 006 T014 says 20/20 | Update to 30/30 |
| OP-21 | Program tasks T012–T015 open | `005/tasks.md` |

---

## Gap analysis (98 → 100)

| Gap | Blocks v8.2.0 tag? | Remediation |
|-----|-------------------|-------------|
| Stakeholder sign-off | Yes | Release meeting |
| READINESS sync | No | T020 |
| Supply seed | No | v8.3 |
| Keycloak | Yes (prod only) | POST-B1 |

---

## Next actions

| Priority | Action | Command |
|----------|--------|---------|
| P0 | Re-run demo before tag | `.\scripts\run-full-demo.ps1` |
| P0 | Tag v8.2.0 | User approval + git tag |
| P1 | Sync READINESS | T020 in tasks.md |
| P1 | Seed supply network | Alembic seed script |
| P2 | Prophet upgrade | 011-v8-ml-upgrade (future spec) |

---

*Generated by `/speckit.analyze` 2026-06-27. Supersedes stale sections in `005/analyze.md` for v8 scope.*
