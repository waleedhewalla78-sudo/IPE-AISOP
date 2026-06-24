# Tasks: IPE Program — Release Execution & Post-V6 Backlog

**Input**: [plan.md](./plan.md), [spec.md](./spec.md), [../004-ai-first-v6/tasks-release.md](../004-ai-first-v6/tasks-release.md)

**Branch**: `005-ipe-program-status`

**Purpose**: Program-level task rollup — maps features 002–004 release work and POST backlog.

---

## Phase P1: Status Spec Creation ✅

- [x] T001 Create `specs/005-ipe-program-status/spec.md`
- [x] T002 Create `checklists/requirements.md`
- [x] T003 Point `.specify/feature.json` to this feature + `active_plan`

---

## Phase P2: Documentation Sync (maps P-DOC-*)

**Owner**: Any agent before or parallel to release  
**Detail**: [../004-ai-first-v6/tasks-release.md](../004-ai-first-v6/tasks-release.md) P-DOC-01–08

- [x] T004 [P1] Execute P-DOC-01–03, P-DOC-08 — fix HIGH analyze drift in `005/spec.md` + `implementation-tracker.md`
- [x] T005 [P2] Execute P-DOC-04–07 — Notion note, quickstart CP, SPECKIT footnote
- [ ] T006 [P1] After REL-11, execute P-DOC-04 — mark SC-V6 live proven in analyze + tracker

---

## Phase P3: Release Verification (maps REL-*)

**Owner**: Release engineer / `/speckit.implement`  
**Detail**: [../004-ai-first-v6/tasks-release.md](../004-ai-first-v6/tasks-release.md)

| Program task | Release tasks | Exit gate |
|--------------|---------------|-----------|
| T007 [P0] Stack | REL-01–05 | API :8000 + seed |
| T008 [P0] Tests | REL-06–08 | launch-verify 10/10 |
| T009 [P0] Demo | REL-09–11 | demo 20/20 |
| T010 [P0] Tag | REL-12–17 | v6.0.0 + T055 ✅ |
| T011 [P2] 100/100 | REL-18–20 | k6 + Chaos evidence |

- [x] T008 [P0] [P3] Complete REL-TEST (REL-06–08) — 10/10 2026-06-23
- [ ] T007 [P0] [P3] Complete REL-STACK (REL-01–05)
- [ ] T009 [P0] [P3] Complete REL-DEMO (REL-09–11)
- [ ] T010 [P0] [P3] Complete REL-TAG (REL-12–17) — **closes 004 T055**
- [ ] T011 [P2] [P3] Complete REL-PROD (REL-18–20) — optional 100/100

---

## Phase P4: Ongoing Sync (recurring)

- [ ] T012 [P] After T010, update `005/spec.md` program table to **55/55**, readiness **96/100**
- [ ] T013 [P] Sync Notion IPE Task Tracker v2 after each REL phase completes
- [ ] T014 [P] Close 002 T049–T053 or mark superseded in `005/spec.md` (see G-002-*)
- [ ] T015 [P] Archive superseded `IMPLEMENTATION-TASKS.md` pointers → 005 spec

---

## Phase POST-A — Scale & Performance (post-v6.0.0)

- [ ] POST-A1 [P1] Implement async CPM cascade for >50 MOs in `services/cap-svc/app/core/visual_cpm.py`
- [ ] POST-A2 [P1] Extract `visual-cpm-svc` microservice per AD-007 follow-on
- [ ] POST-A3 [P2] Wire `ipe.chaos.metric` real-time tail to Cost of Chaos UI

**Effort**: 2–4 weeks · **Trigger**: Customer plant >20 MOs on Gantt

---

## Phase POST-B — Enterprise Integrations

- [ ] POST-B1 [P1] Keycloak OIDC/SAML/SCIM live test — **BLOCKED** C-007 (Azure AD sandbox)
- [ ] POST-B2 [P1] SAP sandbox connector validation beyond mapper scripts
- [ ] POST-B3 [P1] D365 sandbox connector validation beyond mapper scripts
- [ ] POST-B4 [P2] Production Odoo handler for `sync_routing_correction` (extends V6-R4 stub)

**Effort**: 4–8 weeks · **Blocker**: Customer IdP / ERP sandbox

---

## Phase POST-C — Governance & Data

- [ ] POST-C1 [P2] Migration `cdm_schedule_version` immutable snapshots (003 C2)
- [ ] POST-C2 [P2] Digital Twin promote/clone workflow (003 C7)
- [ ] POST-C3 [P2] RLS policies on legacy migrations 002–012 tables (constitution I debt)

---

## Phase POST-D — Commercial & UX (out of scope unless requested)

- [ ] POST-D1 [P3] FR-603 Stripe billing integration
- [ ] POST-D2 [P3] FR-505 React Native mobile app
- [ ] POST-D3 [P2] FR-506 WCAG 2.1 AA audit
- [ ] POST-D4 [P3] FR-405 MLflow feature store
- [ ] POST-D5 [P3] Project Phoenix commerce stack (Engine A)

---

## Program Task Rollup

| Feature | Tasks | Done | Open |
|---------|-------|------|------|
| 002 Release gates | 62 | 58 | 4 (hygiene) |
| 003 V5 | 45 | 45 | 0 |
| 004 V6 build | 55 | 54 | 1 (T055) |
| 004 Release (REL-*) | 25 | 0 | 25 |
| 005 Program meta | 15 | 5 | 10 |
| **Speckit total** | **202** | **162** | **40** |

*Release tasks (REL-*) overlap T055; after T010 program counts 004 @ 55/55.*

---

## Critical Path (Next 48h)

```text
T007 (REL-01–05) → T008 (REL-06–08) → T009 (REL-09–11) → T010 (REL-12–17)
```

**Start command**:

```powershell
cd D:\AISOP\ipe\infrastructure\docker
docker compose up -d
```

**Next speckit command**: `/speckit.implement` on REL-01
