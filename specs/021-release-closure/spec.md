# Spec 021 — Release Closure

**Status:** Active  
**Created:** 2026-07-11  
**Speckit phase:** Full pipeline (constitution → converge)  
**Constitution:** v1.2.6  
**Prior spec:** 020-planning-intelligence (ENG COMPLETE)

---

## Goal

Close the remaining **engineering** gaps that prevent release tags from landing after humans finish commercial and Arabic sign-off activities.

## Problem Statement

After Spec 020 planning intelligence was completed (2026-07-11), two UAT steps remained PARTIAL:

- **UAT-10**: Copilot `/chat` endpoint hangs indefinitely when LLM provider is unavailable or slow (default 300 s timeout). This prevents UAT pass.
- **UAT-11**: Best-fit model selector (`BestFitSelector`) can run ARIMA/SARIMA grid search for 45–180 s on first/cold call. UAT-11 endpoint is wired but times out during automated testing.

Additionally:

- **OQ-13**: Migration 044–049 apply path needs clear documentation + scripted verification so operators can confidently run `alembic upgrade head` on production DB.
- **Tag readiness**: The conditions under which `v9.1.1-r2` vs `v9.2.0-planning` can be cut need to be documented unambiguously.
- **GitHub issue hygiene**: Issues created/closed during Specs 017–020 need triage comments so the tracker reflects actual state.

## Scope

### In Scope (engineering)

| ID | Item |
|----|------|
| RC-01 | Fix Copilot `/chat` non-streaming path — 20 s timeout + tool-backed fallback |
| RC-02 | Fix best-fit cold path — 8 s time budget, SES fallback when ARIMA/SARIMA exceeds budget |
| RC-03 | OQ-13 migration apply script + documentation |
| RC-04 | Tag readiness document — when to cut v9.1.1-r2 vs v9.2.0-planning |
| RC-05 | GitHub issue triage/comment for 021 tasks |
| RC-06 | Re-run `planning-uat.ps1` and report updated scores |
| RC-07 | Update OPEN-ITEMS-PROJECT.md — Spec 020 DONE / 021 active |
| RC-08 | sop-svc: verify release2-smoke still green after code changes |

### Out of Scope (leave OPEN)

- PH1-01 SOW (commercial — human)
- PH1-02 Odoo staging (ops — human)
- G-R2-04 Arabic native sign-off (QA — human)
- Wave 3 items (#43–#46)
- NEXUS

## Success Criteria

1. `planning-uat.ps1` scores PASS=10 PARTIAL=0 FAIL=0 on a live stack (or documented as blocked by LLM key, not by code)
2. `release2-smoke.ps1` still PASS 15/15
3. All 021 engineering tasks committed and pushed to `origin/master`
4. GitHub issues created for RC-01–RC-08, linked to #50 where relevant
5. Tag readiness documented — no premature tag push

## Related

- `specs/020-planning-intelligence/` — predecessor
- `docs/qa/PLANNING-MASTER-BUILD-UAT-REPORT.md` — live UAT report
- `specs/018-phase2-release2/OPEN-ITEMS-PROJECT.md` — whole-project status
- `ipe/.specify/memory/constitution.md` — v1.2.6
