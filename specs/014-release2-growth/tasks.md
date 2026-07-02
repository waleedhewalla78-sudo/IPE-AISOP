# Tasks — 014 Release 2 Commercial Growth

**Feature**: `014-release2-growth`  
**Date**: 2026-07-01  
**Gate**: `run-release2-demo.ps1` 5/5 PASS + `run-release1-integration-demo.ps1` 13/13 PASS

---

## Summary

| Phase | Done | Total | Status |
|-------|------|-------|--------|
| 0 Hygiene | 1 | 2 | In progress |
| A Auto-propose | 6 | 6 | ✅ Complete |
| B Outcomes | 3 | 4 | ✅ Complete (T123 optional) |
| C Copilot Lite | 5 | 5 | ✅ Complete |
| D Odoo write-back | 4 | 4 | ✅ Complete |
| E Closure | 1 | 4 | In progress |

---

## Phase 0 — Hygiene

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T001 | Update `ipe/.specify/feature.json` → active 014 | P0 | ✅ |
| T002 | Refresh `SPECKIT-CHECKLIST.md` header to v8.2.0 / 32/32 | P2 | ⬜ |

---

## Phase A — Agentic resolution loop

| ID | Task | Priority | Status | Evidence |
|----|------|----------|--------|----------|
| T110 | connector: `_auto_propose_scenarios()` after rescore when score &lt; threshold | P0 | ✅ | sync_engine.py |
| T111 | Tenant config `auto_propose_threshold` (default 75) | P1 | ✅ | env AUTO_PROPOSE_THRESHOLD |
| T112 | Fix res-svc `handle_feasibility_scored` mo_id + persist scenarios | P0 | ✅ | handlers.py |
| T113 | Dedupe scenarios by (mo_id, strategy) on propose | P0 | ✅ | resolution.py |
| T114 | Unit test: sync rescore triggers propose | P0 | ✅ | test_auto_propose.py |
| T115 | Add `RES_SVC_URL` to connector release1 compose env | P0 | ✅ | docker-compose.release1.yml |

---

## Phase B — Outcomes dashboard

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T120 | Create `OutcomesPage.tsx` (OTD, ROI, sync status) | P0 | ✅ |
| T121 | OTD baseline capture button + i18n | P0 | ✅ |
| T122 | Command Center tab Outcomes (release1 visible) | P0 | ✅ |
| T123 | Optional `GET /analytics/outcomes-summary` | P2 | ⬜ |

---

## Phase C — Copilot Lite

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T140 | dpe-svc `POST /planner-assist/query` intent router | P1 | ✅ |
| T141 | Kong route `/api/v1/planner-assist` on release1 | P1 | ✅ |
| T142 | `PlannerAssistPanel` on Control Tower | P1 | ✅ |
| T143 | Unit tests: 5 intents | P1 | ✅ |
| T144 | Optional nlp-svc passthrough when configured | P2 | ✅ |

---

## Phase D — Odoo resolution write-back

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T150 | connector `POST /erp/odoo/resolution-notify` | P1 | ✅ |
| T151 | res-svc approve → call connector notify | P1 | ✅ |
| T152 | Feature flag `odoo_resolution_writeback_enabled` | P1 | ✅ |
| T153 | Integration test with mock Odoo | P1 | ✅ |

---

## Phase E — Closure

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T160 | `scripts/run-release2-demo.ps1` (5 checkpoints) | P0 | ✅ |
| T161 | R1 regression 13/13 after R2 merge | P0 | ⬜ |
| T162 | Update `RELEASE1-DEMO-STATUS.md` → R2 section | P1 | ✅ |
| T163 | Tag readiness `v9.1.0-r2` checklist | P2 | ⬜ |

---

## Dependency graph

```text
T001 → T110 → T114 → T160
T110 → T112 → T113
T120 → T122 → T160
T140 → T141 → T142 → T160
T150 → T151 (after A stable)
T160 → T161 → T163
```
