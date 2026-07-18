# Tasks: Spec 029 Productionization

Legend: [x] done · [~] partial/deferred · [ ] not started · [!] COM OPEN

## Constitution / pointers
- [x] T001 Constitution PATCH 1.4.1 — Spec 029 active; Phase 6/7 COMPLETE in map
- [x] T002 Update `ipe/.specify/feature.json` + root/ipe `AGENTS.md` pointers

## Specify → Converge artifacts
- [x] T010 spec.md / clarify.md / analyze.md / plan.md / tasks.md
- [x] T011 quickstart.md / research.md / data-model.md / contracts
- [x] T012 taskstoissues.md + gh issues
- [x] T013 implement.md + converge.md + PHASE8/SPEC029 report

## 8A — Must
- [x] T101 Kong `/api/v1/enterprise` route on R2 declarative config (+ deploy mirror if present)
- [x] T102 AndonAlert model + `andon_persist` dual-write wired into phase7 API
- [x] T103 Migration 068 RLS coverage gaps
- [x] T104 pytest: andon persist helpers + API regression green

## 8B — Should
- [x] T201 Migration 069 MPS/MRP run tables + `plan_persist` helpers
- [x] T202 S&OP stage-gate scaffold core + `/planning-command/sop/stage-gate*` APIs
- [x] T203 pytest for stage-gate + plan_persist

## 8C — Stack-dependent
- [~] T301 Seed demo MOs + star-trans-validate (#70/#72/#110) — attempt or document BLOCKED

## 8D — Notes
- [x] T401 k6 p95 investigation notes
- [x] T402 Playwright flake notes (+ optional Phase 3+ stub if feasible)

## Deferred / COM (not faked)
- [!] OQ-7, SOW, PH1-02, G-R2-04, OQ-1
- [~] Real Andon push notifications; full collaborative locking UI; WhatsApp hub
