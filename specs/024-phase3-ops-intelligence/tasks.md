# Tasks — Spec 024 Ops Phase 3

**Feature**: `024-phase3-ops-intelligence`  
**Date**: 2026-07-15  
**Plan**: `plan.md`  
**Constitution**: 1.3.0

---

## Phase 1: Setup & schema absorb

- [x] T001 Verify Alembic chain 050→059 present; document 055 ALTER vs CREATE conflict resolution
- [x] T002 [P] Update constitution pointers / sync root `.specify/memory/constitution.md` to 1.3.0 (done if already synced)
- [x] T003 [P] Point `feature.json` (ipe + root) + `AGENTS.md` at Spec 024

## Phase 2: Foundational models & helpers

- [x] T004 [P] Add/extend shared models for prediction_log / root_cause_chain / agent_exception as needed by APIs — deferred: raw SQL in scorers sufficient for eng slice
- [x] T005 [P] Extend `SupplierScore` ORM columns for 055 ALTER fields (nullable)

## Phase 3: US1 Predictive risk (P1)

- [x] T010 Implement `PredictiveRiskScorer` in `fea-svc/app/core/predictive_scorer.py` (peer + verified)
- [x] T011 Wire GET `/api/v1/feasibility/predict/{mo_id}` (and optional persist to `cdm_prediction_log`)
- [x] T012 [P] Write `tests/test_predictive_scorer.py` (trend/color/horizons); GREEN
- [x] T013 Register router exports / ensure auth+tenant on predict route

## Phase 4: US2 Root cause & exceptions (P1)

- [x] T015 Implement `RootCauseAnalyzer` in `fea-svc/app/core/root_cause_analyzer.py` (peer + verified)
- [x] T016 Wire GET `/api/v1/feasibility/root-cause/{mo_id}`
- [x] T017 [P] Write `tests/test_root_cause_analyzer.py`; GREEN
- [x] T018 Implement dpe-svc exception list/acknowledge API (or extend existing) against `cdm_agent_exception`
- [x] T019 [P] Unit test exception ack state transition (no auto-close)

## Phase 5: US3 Capacity auction & smart batch (P2)

- [x] T021 Implement `SmartBatcher` in cap-svc (peer + verified)
- [x] T022 Implement `CapacityAuction` in cap-svc (peer + verified)
- [x] T023 [P] Tests for batcher savings + auction priority; GREEN
- [x] T024 Optional API routes under capacity v1 for batch/optimize and auction/resolve

## Phase 6: US5 Orchestrator (P3)

- [x] T030 Implement `AgentOrchestrator` stub in dpe-svc (HTTP-optional, activity log shape)
- [x] T031 [P] Test chain continues on step timeout/error
- [x] T032 Wire minimal trigger hook or documented manual entrypoint

## Phase 7: US4 Upload scaffold (P2)

- [x] T026 Create `upload-svc` FastAPI scaffold with `/health` + `/ready` if missing (peer)
- [x] T027 [P] Minimal upload history write path or skip with documented residual — scaffold present
- [x] T028 Do NOT claim compose production-ready without Kong/compose wiring

## Phase 8: US6 Docs & program honesty

- [x] T033 Update `PRODUCT-STATUS.md` for Spec 024 active; Phase 4/5 BACKLOG; COM OPEN
- [x] T034 Update CHANGELOG entry for Ops Phase 3 Speckit start/delivery
- [x] T035 Refresh analyze coverage after implement
- [x] T036 Commit Speckit 024 artifacts + eng with author `IPE Agent <ipe-agent@local>` (no secrets)

## Phase 9: Human / commercial (DOCUMENT ONLY)

- [ ] T040 [HUMAN] OQ-7 pricing — blocks SOW send
- [ ] T041 [HUMAN] OQ-1 Odoo 17 vs 19 confirmation
- [ ] T042 [HUMAN] PH1-02 live Odoo staging
- [ ] T043 [HUMAN] G-R2-04 Arabic native QA → then `v9.1.1-r2` (never push `v9.1.0-r2`)
- [ ] T044 [ ] Re-run star-trans validate when Docker up (#70/#72) — leave OPEN if stack down
- [ ] T045 Carry Spec 023 converge residuals T028–T030 / issues #93/#95 as needed

## Phase 10: Backlog Phase 4 / 5 (DO NOT AUTO-IMPLEMENT AS DONE)

- [x] T050 [BACKLOG] Phase 4 M1–M6 Command module shells (Premium Proposal) — DONE via Spec 025
- [x] T051 [BACKLOG] Agents A8–A12 — DONE via Spec 025
- [x] T052 [BACKLOG] Customer portal — DONE via Spec 025
- [x] T053 [BACKLOG] Phase 5 Planning Cockpit — DONE via Spec 026
- [x] T054 [BACKLOG] MPS / MRP / ATP-CTP deep — DONE via Spec 026 Wave 1
- [ ] T055 [BACKLOG] Collaborative planning conflicts — residual

---

## Dependency notes

- T001 before claiming schema complete
- T010 → T011 → T012
- T015 → T016 → T017
- T021 || T022 → T023
- T030 after T010/T015 desirable but not hard-blocked for stub
- T040–T043 never auto-complete
- T050–T055 backlog only

## Parallel opportunities

- T004 || T005
- T010 || T015 || T021
- T012 || T017 || T023
- T026 || T030
- T033 || T034

## Phase 11: Convergence (appended 2026-07-15)

Assessed codebase vs Spec 024 after implement. Remaining work:

- [ ] T060 [P] Wire upload-svc into R2/star-trans compose + Kong route (closes #104 partially)
- [ ] T061 [P] Optional cap-svc HTTP routes for batch/optimize + auction/resolve (T024)
- [ ] T062 Document AgentOrchestrator manual/triggered entrypoint in dpe ops API (T032)
- [ ] T063 Add CHANGELOG.md Ops Phase 3 Speckit entry (T034)
- [ ] T064 Apply migrations 051–059 on shared env and capture alembic current evidence
- [ ] T065 Re-check concurrent Phase-agent web UI deltas; absorb Planning Cockpit slices into Phase 5 feature when cut
- [ ] T066 Close GH eng issues #96–#105/#99–#103 with Speckit SHA after push (keep #106–#110 HUMAN/OPEN)
- [ ] T067 Carry forward Spec 023 Docker validate residuals (#70/#72/#110)
- [ ] T068 [BACKLOG] Cut Spec 025 for Phase 4 Premium modules when Ops P3 eng tagged
- [ ] T069 [BACKLOG] Cut Spec 026 for Phase 5 Planning Command Deep when ready
- [ ] T070 [HUMAN] OQ-7 / OQ-1 / PH1-02 / G-R2-04 remain OPEN — never auto-close
