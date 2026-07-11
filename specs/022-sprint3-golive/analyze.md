# Analyze — Spec 022 Sprint 3 Go-Live + Whole Project Status

**Date:** 2026-07-11  
**Constitution:** 1.2.7  
**Active feature:** `ipe/specs/022-sprint3-golive`  
**Mode:** Non-destructive analysis (Layer A at clarify; Layer B after tasks)

---

## A. Cross-artifact consistency (constitution ↔ spec ↔ clarify)

| Check | Result | Notes |
|-------|--------|-------|
| Constitution honesty rule vs FR-007 | PASS | Spec forbids inventing COM closures |
| Principle VII customer package vs Sprint 2 | PASS | Package exists; SOW send still OQ-7 blocked |
| Tag policy vs C-022-02 / C-022-06 | PASS | v9.2.0-planning applied; v9.1.1-r2 HOLD |
| Dual Odoo support vs C-022-04 | PASS | Spec edge case + clarify decision |
| Out of scope Wave 3 | PASS | Spec Out of Scope matches #43–#46 defer |
| Root vs ipe constitution sync | PASS | Both 1.2.7 after this Speckit run |
| Nexus Social | PASS | Explicitly out of scope in feature.json |

**CRITICAL conflicts:** None requiring constitution change.

**WARNINGS:**

1. Root `AGENTS.md` still mentions REL-STACK / v6.0.0 — stale vs v9.x program (documentation drift; fix in implement if in scope).
2. `SOW-STATUS.md` Odoo 17 recommendation vs OQ doc Odoo 19 — clarified C-022-04; update SOW-STATUS wording in implement.
3. Spec 021 GH issues #52–#55 still OPEN despite code on master — hygiene task.

---

## B. Whole project status (detailed)

### B1. Spec / program tracks

| Spec | Status | Notes |
|------|--------|-------|
| 000–012 | Archive / absorbed | Do not reopen |
| 013 R1 Odoo MENA | Eng done; COM UAT open | PH1-01/02 |
| 014–016 | Delivered / absorbed | Gate 11 waiver COM sigs |
| 017 First release | Wave 1 eng ✅ | C-11 UAT docx residual; commercial open |
| 018 Phase 2 R2 | Eng ~PASS | G-R2-04 human OPEN; tag HOLD Option B |
| 019 Program converge | DONE | #50 human-open |
| 020 Planning intelligence | ENG COMPLETE | mig 044–049; modules A–F |
| 021 Release closure | ENG COMPLETE | UAT-10/11 fixed; tag v9.2.0-planning |
| **022 Sprint 3 go-live** | **ACTIVE** | This feature |

### B2. Engineering readiness

| Area | Status | Evidence |
|------|--------|----------|
| R1 core modules | BUILT | PRODUCT-STATUS |
| R2 modules | BUILT | nlp/demand/scenario |
| Planning A–F | BUILT | mat/demand/cap/sop |
| Migrations head | ~049 | compose planning |
| R2 smoke | Prior 15/15 | Re-verify on live stack |
| Playwright | Prior 22/22 | Arabic eng, not COM sign-off |
| k6 SLO | Prior PASS | p95 under target |
| Deploy package | Present | dry-run log started Sprint 3 |
| Validate script | Present | `scripts/star-trans-validate.ps1` |

### B3. Commercial / human OPEN (do not fake)

| Item | Blocks | Owner |
|------|--------|-------|
| **OQ-7 pricing** | SOW send | Waleed |
| **OQ-1 Odoo 17 vs 19** | Field mapping Week 1 | Star Trans IT |
| **PH1-01 SOW send** | Commercial start | COM (depends OQ-7) |
| **PH1-02 live Odoo staging** | Live sync UAT | Ops / Customer IT |
| **G-R2-04 Arabic native QA** | `v9.1.1-r2` | Native reviewer |
| OQ-9 waiver signatures | Formal go-live packet | Waleed |
| OQ-8 Customer 2 list | Pipeline | Waleed |

### B4. GitHub open issues (snapshot)

| Bucket | Issues | Action in 022 |
|--------|--------|---------------|
| Spec 021 eng | #52–#55 | Triage/close with evidence |
| Commercial | #50 | Keep OPEN; refresh comment |
| Wave 2 defer | #37 #38 #42 | Leave deferred |
| Wave 3 OOS | #43–#46 | Leave OOS |
| EP3/EP4 stale | #15–#26 | Comment defer or close if shipped — no silent reopen |
| Tag readiness | #55 | Update: planning tag applied; R2 tag still HOLD |

### B5. Runtime (this Speckit run)

Docker services observed healthy: kong, dpe, fea, res, cap, mat, connector, web-ui, demand, nlp, scenario, sop, db, redis, keycloak, mock-odoo. Suitable for validate/smoke evidence. Live customer Odoo **not** present → PH1-02 still OPEN.

---

## C. Coverage matrix (Layer B — after plan/tasks)

| Spec requirement | Plan | Tasks | Gap |
|------------------|------|-------|-----|
| FR-001 deploy package | Yes | T001–T003 | — |
| FR-002 validate script | Yes | T004–T005 | — |
| FR-003 status honesty | Yes | T006–T008 | — |
| FR-004 GH hygiene | Yes | T009–T011 | — |
| FR-005 live smoke | Yes | T012–T013 | — |
| FR-006 seed SQL | Yes | T014 | — |
| FR-007 no fake COM | Yes | T015 + COM tasks marked HUMAN | — |

**Duplication:** Minimal — 022 does not re-implement 020/021 code paths.

**Ambiguity residual:** None blocking engineering; COM items intentionally unresolved.

---

## D. Constitution compliance snapshot

| Principle | 022 impact |
|-----------|------------|
| I RLS | No new tables expected; seed SQL must not weaken RLS |
| II Auth | Validate script uses JWT login — no open endpoints |
| III Tests | Prefer running existing suites; new code needs tests |
| IV Events | R1 profile Kafka optional — unchanged |
| V Architecture | deploy/star-trans service set must stay R1-scoped |
| VI Observability | Health checks via documented paths |
| VII Customer-first | Core of this feature |
| VIII Gates | Do not invent gate PASS; record script output |

---

## E. Analyze verdict

**Engineering track:** Ready to plan/implement Spec 022.  
**Commercial track:** Blocked on OQ-7 / PH1-02 / G-R2-04 / OQ-1 — document only.  
**Risk:** Stale AGENTS.md and SOW-STATUS Odoo wording can confuse operators — fix in implement.  
**No CRITICAL constitution violations.**
