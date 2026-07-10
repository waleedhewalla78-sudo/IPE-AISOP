# Tasks: 019-program-converge

**Input**: plan.md, spec.md, research.md, data-model.md, contracts/  
**Created**: 2026-07-10

## Format: `[ID] [P?] [Story?] Description`

---

## Phase 1: Setup

- [x] T001 Create `specs/019-program-converge/` artifact tree and point `ipe/.specify/feature.json` at 019
- [x] T002 [P] Update constitution to v1.2.5 noting 019 + honest commercial blockers
- [x] T003 [P] Write checklist `checklists/requirements.md`

---

## Phase 2: Foundational

- [x] T004 Encode clarify decisions into spec (feature isolation, blockers OPEN, promote scope)
- [x] T005 [P] Write analyze.md whole-project status
- [x] T006 [P] Write plan.md / research.md / data-model.md / contracts / quickstart.md

---

## Phase 3: User Story 1 — mat-svc on R2 compose (P1) 🎯

**Goal**: mat-svc defined and health-checkable in release2 compose  
**Independent test**: `config --services` includes mat-svc

- [x] T010 [US1] Add `mat-svc` service to `infrastructure/docker/docker-compose.release2.yml` (AUTH_MODE=local, Kafka disabled, port 8002)
- [x] T011 [P] [US1] Ensure nlp-svc `depends_on` includes mat-svc (optional soft start) or document URL-only dependency

---

## Phase 4: User Story 2 — Scenario promote (P1)

**Goal**: Promote API + workbench UI  
**Independent test**: pytest promote + UI key present

- [x] T020 [US2] Add `POST /{scenario_id}/promote` in `services/scenario-svc/app/api/v1/scenarios.py`
- [x] T021 [P] [US2] Add API test in `services/scenario-svc/tests/test_api.py`
- [x] T022 [US2] Add Promote button in `apps/web/src/features/hubs/planning/ScenarioWorkbenchPage.tsx`
- [x] T023 [P] [US2] Add `scenarios.promote` to `apps/web/src/locales/en.json` and `ar.json`
- [x] T024 [P] [US2] Comment on GitHub #40 with implement link (close if verified)

---

## Phase 5: User Story 3 — stock.quant mock fidelity (P1)

**Goal**: mock-odoo returns quants; sync path testable  
**Independent test**: search_read non-empty

- [x] T030 [US3] Add `_sample_quants()` and wire search_read in `services/mock-odoo-api/app/main.py`
- [x] T031 [P] [US3] Add/extend unit test under `services/mock-odoo-api/tests/`
- [x] T032 [P] [US3] Document FR-R1-05 eng-local DONE; staging still PH1-02 in OPEN-ITEMS note

---

## Phase 6: User Story 4 — Program honesty (P2)

- [x] T040 [US4] Create GitHub issues for remaining open T0xx not covered by #37–#46; skip closed #27–#36/#39/#41
- [x] T041 [P] [US4] Comment on #37/#38/#42–#46 with defer/ARB notes
- [x] T042 [US4] Write `taskstoissues.md` mapping

---

## Phase 7: Polish

- [x] T050 Run scenario-svc + mock-odoo unit tests
- [x] T051 Write `implement.md` log
- [x] T052 Run converge assessment → append Phase Convergence tasks if needed
- [ ] T053 Commit Speckit + implementation (no secrets / no kms keys)

---

## Phase 8: Convergence

- [ ] T060 [Conv] Rebuild/start mat-svc on R2 stack when QA window allows; confirm `:8002/api/v1/health` (no destructive down if other agent active)
- [ ] T061 [Conv] Product-verify scenario promote on live R2 UI; close GitHub #40 if accepted
- [ ] T062 [Conv] BLOCKED PH1-01 — Phase 1 SOW / commercial signature (human) — see #50
- [ ] T063 [Conv] BLOCKED PH1-02 — Provision Odoo staging + wire connector (ops) — see #50
- [ ] T064 [Conv] BLOCKED G-R2-04 — Native Arabic human sign-off (`docs/qa/arabic-qa-r2.md`) — see #50
- [ ] T065 [P] [Conv] Defer/implement #37 tenant provision API (ARB)
- [ ] T066 [P] [Conv] Defer/implement #38 quotas metering E2E (ARB)
- [ ] T067 [P] [Conv] Defer/verify or CUT #42 predictive delay XGBoost+SHAP
- [ ] T068 [P] [Conv] Schedule Wave 3 #43–#46 or ARB CUT from near-term roadmap
- [ ] T069 [P] [Conv] Optional: refresh `READINESS.md` version banner to v9.x / Spec 019 pointer
- [ ] T070 [Conv] After G-R2-04 policy: cut/push `v9.1.1-r2` (do not move old `v9.1.0-r2`)

---

## Dependencies

```text
T001–T006 → T010/T020/T030 → T040 → T050–T053
T020 before T022
T030 before T031
T053 → T060+ (ops/human)
```

## Parallel examples

- T010 ‖ T020 ‖ T030 after foundation
- T021 ‖ T023 after T020
- T031 ‖ T032 after T030

## MVP

US1 + US2 + US3 engineering; US4 hygiene; commercial blockers remain blocked tasks in converge.
