# Analyze — Spec 029 Whole-Project Status

**Date**: 2026-07-18 · **Constitution**: 1.4.1 (PATCH from 1.4.0) · **HEAD baseline**: ~39ad033

## Whole-program status (honest)

| Track | Spec | Status | Evidence |
|-------|------|--------|----------|
| Sprint 3 go-live | 022 | ENG COMPLETE | residuals #70/#72 may OPEN |
| Sprint 4 Wave 1 | 023 | ENG COMPLETE | Odoo Config v2 + OTD |
| Ops Phase 3 | 024 | ENG COMPLETE Wave 1 | PHASE3 report |
| Ops Phase 4 | 025 | ENG COMPLETE Wave 1 | PHASE4 report |
| Ops Phase 5 | 026 | ENG COMPLETE Wave 1 | PHASE5 report |
| Ops Phase 6 | 027 | ENG COMPLETE Wave 1 | PHASE6 report; enterprise handlers ASGI 6/6; **Kong route GAP** |
| Ops Phase 7 | 028 | ENG COMPLETE Wave 1 | PHASE7 report; Kong planning-command 13/13 |
| **Productionization** | **029** | **THIS RUN** | OPEN-TOPICS eng items 5–9 |
| COM blockers | — | **OPEN** | OQ-7, PH1-02, G-R2-04, OQ-1 — do not fake |
| Tag `v9.1.1-r2` | — | **HOLD** | gated by G-R2-04 |
| Stale `v9.1.0-r2` | — | **NEVER PUSH** | standing policy |

## Constitution compliance (I–X)

| Principle | Spec 029 relevance | Status |
|-----------|-------------------|--------|
| I RLS | Close ~10 `rowsecurity=false` tables | IN SCOPE |
| II Auth | Kong enterprise route inherits dpe JWT/tenant plugins | IN SCOPE |
| III Tests | New pytest for Andon persist, stage-gate, MPS save, RLS migration sanity | IN SCOPE |
| IV Events | No new Kafka topics required | N/A |
| V API consistency | `/enterprise`, `/planning-command` prefixes preserved | OK |
| VI Observability | k6 notes only | NOTES |
| VII Customer-first | No COM fake; seed/validate when healthy | OK |
| VIII Enterprise gates | No tag promotion | OK |
| IX Ops Phase 3–5 | Unchanged COMPLETE | OK |
| X Agentic governance | Phase 6 enterprise must be gateway-reachable | GAP → FR-001 |

## Gap inventory → Spec 029 mapping

| Register ID | Gap | Spec 029 action |
|-------------|-----|-----------------|
| INT-01 / QA-06 | Kong `/enterprise/*` 404 | Add route |
| ENG-04 | Andon in-memory | Dual-write to 067 table |
| QA-04 | RLS 10 tables off | Migration 068 |
| ENG-07 | MPS/MRP persistence | Migration 069 + helpers |
| ENG-05 | S&OP stage-gate | Scaffold API |
| QA-01 | k6 p95 under load | Investigation notes (+ light fixes if trivial) |
| QA-02 | Playwright flakes | Notes + optional Phase 3+ stub |
| ENG-01/02/03 | #70/#72/#110 validate | Attempt if stack up |
| C-01..C-08 | COM | Document OPEN only |

## Risks

1. Dirty working tree has unrelated frontend/UX edits — **do not mix into Spec 029 commit**.
2. Live Docker stack may be down — validate residuals stay OPEN with evidence.
3. Under-load k6 may remain FAIL — honesty over fake green.

## User enablement (absorb `docs/USER-GUIDE-BY-SCREEN.md` @ `d83169a`)

| Signal | Status |
|--------|--------|
| Exhaustive screen-by-screen guide landed | **DONE** — `docs/USER-GUIDE-BY-SCREEN.md` (commit `d83169a`) |
| Grounding | Routes from `apps/web` router + locales; honesty flags for stubs/mocks |
| G-R2-04 Arabic native QA | Still **OPEN** (guide documents RTL exists; human sign-off not claimed) |
| PH1-02 live Odoo | Still **OPEN** (guide flags live ERP as blocked) |
| Spec 029 impact | No new product screens required; guide is customer-enablement companion to Wave 1 ENG COMPLETE (022–028). Analyze treats it as **enablement COMPLETE artifact**, not an eng backlog item. |

## Verdict

**PROCEED** with Spec 029 Wave 1 engineering backlog. No constitution MAJOR/MINOR principle change required. User guide @ `d83169a` absorbed as enablement status only.
