# Speckit Converge — Spec 017 First Release Plan

**Date**: 2026-07-09  
**Constitution**: v1.2.3  
**Tag target**: `v9.4.0-p3` — **NOT APPLIED**

---

## 1. Verdict

| Stream | Spec | Code | Tests | Issues |
|--------|------|------|-------|--------|
| Phase 0 cluster | ✅ | ✅ | — | — |
| Phase 0 Gate 11 | 🟡 12/14 | — | script | #27 |
| Sprint 7 emitters | ✅ | ✅ | 20/20 | — |
| T730 migration | ⬜ | ✅ file | — | #29 |
| Wave 1 Copilot nav | ✅ | ✅ | ⬜ | #30 |
| Wave 1 Odoo/OTD | ⬜ | — | — | #31–#36 |
| Wave 2–3 | ⬜ | — | — | #37–#46 |

**Phase 0: ~88%** · **Wave 1: ~12%** · **Program issues: #27–#46 created**

---

## 2. Implemented this run

| Change | Path |
|--------|------|
| Copilot R1 sidebar | `apps/web/src/components/layout/Sidebar.tsx` |
| i18n en/ar | `locales/en.json`, `ar.json` |
| releaseProfile | `lib/releaseProfile.ts` |
| Spec 017 artifacts | `specs/017-first-release-plan/*` |
| GitHub issues | `taskstoissues.md` (#27–#46) |
| Constitution sync | Gate 11 2026-07-09, Spec 017 workflow |

---

## 3. Appended tasks (converge)

| ID | Task | Priority | Issue |
|----|------|----------|-------|
| C-01 | Close #30 — Copilot smoke test | P1 | #30 |
| C-02 | Run T730 migration (compose + K8s) | P0 | #29 |
| C-03 | OQ-9 decision document | P0 | #28 |
| C-04 | Gate 11 steps 10–11 remediation | P0 | #27 |
| C-05 | Tag v9.4.0-p3 after C-03/C-04 | P0 | #18 |
| C-06 | T732 mat-svc release1 compose | P1 | (new — add to #29 body) |
| C-07 | Update GATE-RESULTS 2026-07-09 run | P1 | — |

---

## 4. Constitution checklist

| Principle | Status |
|-----------|--------|
| I RLS | ✅ migration 038 ready; apply pending |
| II Auth | ✅ Copilot route behind ProtectedRoute |
| III Tests | ✅ emitters 20/20 |
| VIII Gates | 🟡 12/14 |

---

## 5. Next action

1. Approve **#29** migration run on K8s  
2. Stakeholder **#28** OQ-9 decision  
3. Execute **#31** Odoo Config v2 (Wave 1) after tag or in parallel per stakeholder  

---

*Converge v1.0 — 2026-07-09*
