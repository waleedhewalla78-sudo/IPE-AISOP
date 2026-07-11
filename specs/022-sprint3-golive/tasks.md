# Tasks — Spec 022 Sprint 3 Go-Live

**Feature**: `022-sprint3-golive`  
**Date**: 2026-07-11  
**Plan**: `plan.md`  
**Constitution**: 1.2.7

---

## Phase 1: Deploy package integrity

- [x] T001 Verify `deploy/star-trans/` file set (compose, .env.template, kong, runbook, smoke) and document in dry-run log
- [x] T002 Run `docker compose -f deploy/star-trans/docker-compose.yml config` with filled `.env` (no secrets committed); confirm exit 0
- [x] T003 Align `DEPLOY-RUNBOOK.md` health paths/service names with compose; update `docs/qa/DEPLOYMENT-DRYRUN-LOG.md`

## Phase 2: Validation & live evidence

- [x] T004 Run `scripts/star-trans-validate.ps1` against live Docker stack; save evidence under `docs/qa/`
- [x] T005 [P] Attempt `scripts/release2-smoke.ps1` (or note blocker); record PASS/FAIL counts; SKIP live Odoo honestly

## Phase 3: Program status honesty

- [x] T006 Update `PRODUCT-STATUS.md` — Sprint 2 complete, Spec 022 active, COM blockers OPEN, tags accurate
- [x] T007 Update `specs/018-phase2-release2/OPEN-ITEMS-PROJECT.md` — 021 DONE, 022 ACTIVE, Sprint 2 GTM done
- [x] T008 Refresh `docs/customer/star-trans/SOW-STATUS.md` — dual Odoo 17/19 support; SOW send blocked by OQ-7

## Phase 4: GitHub hygiene

- [x] T009 Triage Spec 021 issues #52–#55 — close with commit evidence or comment residual
- [x] T010 Refresh #50 commercial blockers with Sprint 3 note (keep OPEN)
- [x] T011 Create GitHub issues for Spec 022 engineering tasks; write `taskstoissues.md` mapping

## Phase 5: Seed & durable artifacts

- [x] T014 Ensure `docs/demo-data/star-trans-seed.sql` present, referenced as non-production (OQ-2)
- [x] T015 Confirm FR-007: no invented pricing, Arabic sign-off, live Odoo, or Odoo version confirm in any 022 artifact
- [x] T016 Update `AGENTS.md` (ipe and/or workspace) pointers to Spec 022 / constitution 1.2.7 (remove stale v6-only gate as sole status)
- [x] T017 Commit Speckit 022 artifacts + evidence with author `IPE Agent <ipe-agent@local>` (no secrets)

## Phase 6: Human / commercial (DOCUMENT ONLY — do not fake)

- [ ] T018 [HUMAN] OQ-7 pricing decision — blocks SOW send
- [ ] T019 [HUMAN] OQ-1 Star Trans Odoo 17 vs 19 confirmation
- [ ] T020 [HUMAN] PH1-02 live Odoo staging provision
- [ ] T021 [HUMAN] G-R2-04 Arabic native QA → then cut `v9.1.1-r2` (never push `v9.1.0-r2`)

## Phase 7: Convergence (appended 2026-07-11)

- [ ] T022 Seed or sync demo MOs so validate check 8 (feasibility queue) PASSes on R2 stack without claiming live Odoo
- [ ] T023 Resolve write-back activate 404 — map correct Kong/R1 route or document intentional absence for current profile with ARB note
- [ ] T024 Re-run `star-trans-validate.ps1` after T022–T023; target ≥16 PASS with only PH1-02 Odoo SKIP remaining for COM

---

## Dependency notes

- T002 → T003
- T001–T003 before claiming deploy ready
- T004–T005 need Docker (available this run)
- T009–T011 need `gh` auth
- T018–T021 never auto-complete
- T022 → T024; T023 → T024

## Parallel opportunities

- T005 || T006–T008 after T004 starts
- T009 || T014
- T022 || T023
