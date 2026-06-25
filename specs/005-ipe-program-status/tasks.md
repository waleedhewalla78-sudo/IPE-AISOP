# Tasks: IPE Program — Release Execution & Post-V6 Backlog

**Input**: [plan.md](./plan.md), [spec.md](./spec.md), [converge.md](./converge.md), [../004-ai-first-v6/tasks-release.md](../004-ai-first-v6/tasks-release.md)

**Branch**: `005-ipe-program-status` | **Updated**: 2026-06-26

**Live evidence**: `docs/demo-run-report-v6.txt` **20/20** ✅ (2026-06-26)

---

## Phase P1: Status Spec Creation ✅

- [x] T001 Create `specs/005-ipe-program-status/spec.md`
- [x] T002 Create `checklists/requirements.md`
- [x] T003 Point `.specify/feature.json` to this feature + `active_plan`

---

## Phase P2: Documentation Sync (maps P-DOC-*)

- [x] T004 [P1] Execute P-DOC-01–03, P-DOC-08
- [x] T005 [P2] Execute P-DOC-04–07
- [ ] T006 [P1] After REL-11 (20/20), mark SC-V6 live proven in analyze + tracker

---

## Phase P3: Release Verification (maps REL-*)

| Program task | Release tasks | Exit gate | Status |
|--------------|---------------|-----------|--------|
| T007 [P0] Stack | REL-01–05 | API :8000 + seed | ✅ 2026-06-25 |
| T008 [P0] Tests | REL-06–08 | launch-verify 10/10 | ✅ 2026-06-23 |
| T009 [P0] Demo | REL-09–11 | demo 20/20 | ✅ **20/20** 2026-06-26 |
| T010 [P0] Tag | REL-12–17 | v6.0.0 + T055 | ⬜ pending demo + git |
| T011 [P2] 100/100 | REL-18–20 | k6 + Chaos | ⬜ optional |

- [x] T007 [P0] REL-STACK
- [x] T008 [P0] REL-TEST
- [x] T009 [P0] REL-DEMO — **20/20** 2026-06-26
- [ ] T010 [P0] REL-TAG — user approval + T055 + **T023 git commit**
- [ ] T011 [P2] REL-PROD

---

## Phase P3-FIX: Demo 20/20 — Live failures

**Evidence**: `docs/demo-run-report-v6.txt` 2026-06-26

| Task | CP | Issue | Fix | Status |
|------|-----|-------|-----|--------|
| T016 | 10–11 | Copilot 503 | nlp-svc catch LLMUnavailableError + demo env | ✅ |
| T017 | 15 | Guardrail / wrong MOs | `$ApproveMoIds` 005/006 in demo script | ✅ |
| T018 | 18 | Tariff 500 | BomLine→BillOfMaterial join | ✅ |
| T019 | 20 | recovery-plan 500 | alert-svc init_database + seed/fallback | ✅ |
| T021 | 15 | MAINT_* UUID parse 500 | Skip synthetic ops in persist | ✅ |
| T022 | all | Stable 20/20 | Rebuild cap-svc + demo script CP15 gate | ✅ 2026-06-26 |

- [x] T016 [P0] Fix nlp-svc Copilot 503
- [x] T017 [P0] Fix CP15 approve guardrail + demo script
- [x] T018 [P0] Fix CP18 tariff shock
- [x] T019 [P0] Fix CP20 chaos/maintenance + War Room recovery
- [x] T021 [P0] Skip synthetic maintenance assignments
- [x] T022 [P0] Demo **20/20** verified

**Validation**:

```powershell
cd E:\AISOP\ipe
docker compose -f infrastructure/docker/docker-compose.yml -f infrastructure/docker/docker-compose.demo.yml build cap-svc
docker compose -f infrastructure/docker/docker-compose.yml -f infrastructure/docker/docker-compose.demo.yml up -d cap-svc
.\scripts\run-full-demo.ps1 -ReportPath docs\demo-run-report-v6.txt
```

---

## Phase P0-GIT: Foundation (Master Plan §5)

- [ ] T023 [P0] `git init` + initial commit (all T016–T021 + BUG-01 fixes)
- [ ] T024 [P0] User approval → `git tag -a v6.0.0` (T055)

---

## Phase P1-AUDIT: Post-tag production blockers

- [ ] T025 [P1] C-01 mat-svc check-availability → `rule_based_atp()`
- [ ] T026 [P1] C-02 dpe-svc double route prefix; BUG-02 MDR fail-closed; BUG-03 version guard

---

## Phase P4: Ongoing Sync

- [ ] T012 [P] After T024, update spec program table **55/55**
- [ ] T013 [P] Sync Notion after REL phases
- [ ] T014 [P] Close 002 T049–T053 hygiene
- [ ] T015 [P] Archive superseded IMPLEMENTATION-TASKS pointers

---

## Phase POST-A — Scale (post-v6.0.0)

- [ ] POST-A1 Async CPM >50 MOs
- [ ] POST-A2 `visual-cpm-svc` split
- [ ] POST-A3 Chaos metric real-time UI

---

## Phase POST-B — Enterprise

- [ ] POST-B1 Keycloak — **BLOCKED** C-007
- [ ] POST-B2 SAP sandbox
- [ ] POST-B3 D365 sandbox
- [ ] POST-B4 Odoo routing correction handler

---

## Phase POST-C — Governance & Data

- [ ] POST-C1 `cdm_schedule_version`
- [ ] POST-C2 Digital Twin promote/clone
- [ ] POST-C3 Legacy RLS 002–012

---

## Phase POST-D — Commercial & UX

- [ ] POST-D1–D5 (out of scope v6)

---

## Program Rollup

| Feature | Tasks | Done | Open |
|---------|-------|------|------|
| 002 Gates | 62 | 58 | 4 |
| 003 V5 | 45 | 45 | 0 |
| 004 V6 | 55 | 54 | 1 (T055) |
| 005 Program | 27 | 12 | 15 |
| **Critical path** | T021–T024 | 4 done (T016–T019) | **T021–T024** |

---

## Critical Path

```text
T021 (CP15 rebuild) → T022 (20/20) → T023 (git commit) → T024 (v6.0.0 tag)
```

**Stack command**:

```powershell
cd E:\AISOP\ipe
.\scripts\rel-demo-stack.ps1 -SkipBuild
```
