# Converge — Spec 021 Release Closure

**Date:** 2026-07-11  
**Status:** Engineering complete. Two non-blocking items pending live stack.

---

## Engineering Gaps Closed

| Item | Status | Evidence |
|------|--------|---------|
| RC-01 UAT-10 Copilot /chat timeout | **CLOSED** | asyncio.timeout(20) + tool fallback; 170 nlp-svc tests green |
| RC-02 UAT-11 best-fit cold path | **CLOSED** | 8 s budget + deadline propagation; 29 demand-svc tests green |
| RC-03 OQ-13 migration script | **CLOSED** | scripts/apply-planning-migrations.ps1 written |
| RC-04 tag readiness docs | **CLOSED** | docs/TAG-READINESS-021.md |
| RC-05 GitHub issue triage | **CLOSED** | #52 #53 #54 #55 created; comment on #50 |
| RC-07 OPEN-ITEMS-PROJECT.md | **CLOSED** | Spec 020 DONE / 021 ACTIVE |
| RC-09 constitution + feature.json | **CLOSED** | v1.2.6; feature.json → 021 |

---

## Remaining Gaps (not engineering-blocked)

| Item | Blocker | Action |
|------|---------|--------|
| RC-06 planning-uat.ps1 re-run | Docker stack not running | Re-run after `docker compose -f infrastructure/docker/docker-compose.release2.yml up -d` |
| RC-08 release2-smoke re-verify | Docker stack not running | Re-run scripts/release2-smoke.ps1 |
| v9.2.0-planning tag | UAT re-run (live) | After 10/10 planning-uat.ps1 on live stack |
| v9.1.1-r2 tag | G-R2-04 Arabic sign-off | Human reviewer |
| PH1-01 SOW | Commercial | Executive |
| PH1-02 Odoo staging | Ops | Provision staging Odoo |

---

## Code Quality

| Check | Status |
|-------|--------|
| nlp-svc: 170 tests | ✓ GREEN |
| demand-svc: 29 tests | ✓ GREEN |
| New tests for UAT-10 | ✓ Added and green |
| New tests for UAT-11 | ✓ Added and green |
| Stale test count (tools = 16→25) | ✓ Fixed |
| No secrets committed | ✓ |
| Constitution v1.2.6 | ✓ |

---

## Next Actions for Operators

1. Start docker stack: `docker compose -f infrastructure/docker/docker-compose.release2.yml up -d`
2. Run `scripts/apply-planning-migrations.ps1` to verify DB head = 049
3. Run `scripts/planning-uat.ps1` — expect 10/10 PASS
4. If 10/10: cut tag `v9.2.0-planning`
5. For R2 tag: wait for G-R2-04 Arabic sign-off, then cut `v9.1.1-r2`

---

## Spec 021 Verdict

**Engineering: COMPLETE.** All code fixes committed and tested. Human blockers documented and not faked. Tag conditions are unambiguous. Speckit pipeline artifacts (spec, clarify, analyze, plan, tasks, taskstoissues, implement, converge, checklists) produced under `specs/021-release-closure/`.
