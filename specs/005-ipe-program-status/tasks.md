# Tasks: IPE Program — Release Execution & Post-V6 Backlog



**Input**: [plan.md](./plan.md), [spec.md](./spec.md), [converge.md](./converge.md), [analyze.md](./analyze.md), [../004-ai-first-v6/tasks-release.md](../004-ai-first-v6/tasks-release.md)



**Branch**: `005-ipe-program-status` | **Updated**: 2026-06-26



**Live evidence**: Demo **20/20** · k6 · chaos **6/6** · coverage **68/65/66%** · ops MVP



---



## Phase P1: Status Spec Creation ✅



- [x] T001 Create `specs/005-ipe-program-status/spec.md`

- [x] T002 Create `checklists/requirements.md`

- [x] T003 Point `.specify/feature.json` to this feature + `active_plan`



---



## Phase P2: Documentation Sync (maps P-DOC-*)



- [x] T004 [P1] Execute P-DOC-01–03, P-DOC-08

- [x] T005 [P2] Execute P-DOC-04–07

- [x] T006 [P1] SC-V6 live proven in analyze + tracker (20/20 + CP17–20)



---



## Phase P3: Release Verification (maps REL-*)



| Program task | Release tasks | Exit gate | Status |

|--------------|---------------|-----------|--------|

| T007 [P0] Stack | REL-01–05 | API :8000 + seed | ✅ |

| T008 [P0] Tests | REL-06–08 | launch-verify 10/10 | ✅ |

| T009 [P0] Demo | REL-09–11 | demo 20/20 | ✅ |

| T010 [P0] Tag | REL-12–17 | v6.0.0 + T055 | ✅ |

| T011 [P2] REL-PROD | REL-18–24 | k6 + chaos + coverage + ops | ✅ code |



- [x] T007 [P0] REL-STACK

- [x] T008 [P0] REL-TEST

- [x] T009 [P0] REL-DEMO — **20/20**

- [x] T010 [P0] REL-TAG — **v6.0.0** + **v6.0.1**

- [x] T011 [P2] REL-PROD — Waves 2A–2D



---



## Phase P3-FIX: Demo 20/20 ✅



- [x] T016–T022 Demo fixes + stable 20/20

- [x] T023–T024 Git + v6.0.0 tag

- [x] T025–T026 Audit fixes (C-01, BUG-02, BUG-03)



---



## Phase REL-PROD — Waves (maps REL-18–24)



| Wave | Task | Description | Status |

|------|------|-------------|--------|

| 2A | REL-18 | k6 smoke + 10 VU + 200 VU | ✅ `docs/k6-summary.md` |

| 2B | REL-19 | Chaos C1–C6 | ✅ `docs/chaos/chaos-summary.md` |

| 2C | REL-20 | Coverage ≥60% cap/mat/dpe | ✅ `docs/coverage-summary.md` |

| 2D | REL-21 | `docker-compose.monitoring.yml` | ✅ |

| 2D | REL-22 | Prometheus + Loki + Grafana configs | ✅ |

| 2D | REL-23 | `run-monitoring-stack.ps1` + verify | ✅ script |

| 2D | REL-24 | Live verify on demo stack | ✅ containers up |



---



## Phase W3 — v6.1.0 Hardening (OPEN)



- [x] W3-01 [P1] C-03 TLS internal services runbook — `docs/runbooks/tls-internal.md`

- [x] W3-02 [P1] C-04 JWT rotation runbook — `docs/runbooks/jwt-rotation.md`

- [x] W3-03 [P1] SEC-05 `password_hash` Alembic migration + seed update

- [x] W3-04 [P2] Post-W3 chaos C6 + demo 20/20 regression

- [x] W3-05 [P0] Tag **v6.1.0** + update READINESS (~95/100 audit)



---



## Phase V8 — Validation convergence (maps 010)

| Task | Description | Status |
|------|-------------|--------|
| V8-01 | QA-001–010 validation sprint | ✅ |
| V8-02 | Demo 30/30 (CP21–30) | ✅ |
| V8-03 | v8 integration 5/5 | ✅ |
| V8-04 | Migrations 029–033 | ✅ |
| V8-05 | Speckit 010 artifacts | ✅ |
| V8-06 | READINESS + PRODUCT-STATUS sync | ✅ |
| V8-07 | Git tag v8.2.0 | ⬜ Pending sign-off |

---

## Phase P4: Ongoing Sync



- [ ] T012 [P] Program table **55/55** on 004 (verify synced)

- [ ] T013 [P] Notion sync after W3

- [ ] T014 [P] Close 002 T049–T053 hygiene

- [ ] T015 [P] Archive superseded IMPLEMENTATION-TASKS pointers



---



## Phase POST-A — Scale (post-v6.1.0)



- [ ] POST-A1 Async CPM >50 MOs

- [ ] POST-A2 `visual-cpm-svc` split

- [ ] POST-A3 Chaos metric real-time UI



---



## Phase POST-B — Enterprise



- [ ] POST-B1 Keycloak — **BLOCKED** C-007

- [ ] POST-B2–B4 SAP/D365/Odoo live



---



## Phase POST-C / POST-D



- [ ] POST-C1–C3 Governance & RLS debt

- [ ] POST-D1–D5 Commercial (out of scope v6)



---



## Program Rollup



| Feature | Tasks | Done | Open |

|---------|-------|------|------|

| 002 Gates | 62 | 58 | 4 |

| 003 V5 | 45 | 45 | 0 |

| 004 V6 | 55 | **55** | 0 |

| 005 Program | 35 | 22 | 13 |

| REL-PROD | 24 | 23 | 1 (live verify) |

| 010 Validation | 30 | 22 | 8 |

---



## Critical Path



```text

REL-24 (monitoring verify) → W3-01..03 (hardening) → W3-04 (regression) → W3-05 (v6.1.0)

```



**Commands**:



```powershell

cd E:\AISOP\ipe

.\scripts\rel-demo-stack.ps1 -SkipBuild

.\scripts\run-monitoring-stack.ps1

.\scripts\run-monitoring-stack.ps1 -VerifyOnly

```


