# Analyze — Spec 024 + Whole-Project Status

**Date**: 2026-07-15  
**Constitution**: 1.3.0  
**Mode**: Whole-project status + (post-tasks) artifact consistency  
**Strict honesty**: COM blockers NEVER marked PASS

---

## 1. Whole-Project Status (detailed)

### 1.1 Program map

| Track | Spec / Tag | Status | Evidence / Notes |
|-------|------------|--------|------------------|
| Planning Intelligence | 020 / `v9.2.0-planning` @ b04434d | **ENG COMPLETE** | Modules A–F; mig 044–049 |
| Release Closure | 021 | **ENG COMPLETE** | UAT-10/11 code; COM documented |
| Sprint 3 Go-Live | 022 | **ENG COMPLETE** | Residuals #70/#72 OPEN (Docker validate) |
| Sprint 4 Wave 1 | 023 @ ~31d4840 | **ENG COMPLETE** | Odoo Config v2 + OTD; mig 050 |
| **Ops Blueprint Phase 3** | **024** | **ACTIVE** | Agents + predictive; mig 051–059 peer-landed |
| Ops Blueprint Phase 4 | (backlog FR-B40x) | **BACKLOG** | Premium Proposal — 6 modules, A8–A12 |
| Ops Blueprint Phase 5 | (backlog FR-B50x) | **BACKLOG** | Planning Cockpit / MPS / MRP / ATP |
| Platform Phase 0–2 | `v9.3.0-p2` | **DONE** | Keycloak/Vault/TLS/Gates 1–5 |
| Platform Phase 3 K8s | `v9.4.0-p3` | **DONE** | Gates 6–10 PASS; Gate 11 OQ-9 waiver |
| Platform Phase 4–5 GTM/SOC2 | — | **BACKLOG** | Do not fake |
| Tag `v9.1.1-r2` | — | **HOLD** | Needs G-R2-04; never push `v9.1.0-r2` |

### 1.2 Migration head

| Rev | Purpose | Source |
|-----|---------|--------|
| 050 | ERP connections | Spec 023 DONE |
| 051 | agent activity log | Peer Phase agent (absorb) |
| 052 | agent exception + SLA | Peer |
| 053 | upload history/error | Peer |
| 054 | demand signal | Peer |
| 055 | supplier_score ALTER | Peer (041 conflict resolved) |
| 056 | root cause chain | Peer |
| 057 | prediction log | Peer |
| 058 | capacity auction log | Peer |
| 059 | batch group | Peer |

**Application code gap (pre-implement):** `predictive_scorer.py`, `root_cause_analyzer.py`, smart_batcher, capacity_auction, agent_orchestrator, upload-svc largely **absent** despite schema presence.

### 1.3 Service readiness (Ops Phase 3)

| Capability | Service | Schema | Code | Tests |
|------------|---------|--------|------|-------|
| Predictive risk | fea-svc | 057 | MISSING | MISSING |
| Root cause chain | fea-svc | 056 | MISSING | MISSING |
| Exception lifecycle | dpe-svc | 052 | MISSING/partial | MISSING |
| Smart batch / auction | cap-svc | 058–059 | MISSING | MISSING |
| Demand fusion | demand-svc | 054 | PARTIAL (forecast exists) | PARTIAL |
| Supplier scoring P3 cols | mat/scn | 055 | PARTIAL (scorecard exists) | PARTIAL |
| Upload wizard | upload-svc | 053 | MISSING service | — |
| Agent orchestrator | dpe-svc | 051 | MISSING | MISSING |

### 1.4 Commercial / human OPEN (immutable)

| ID | Item | Blocks |
|----|------|--------|
| OQ-7 | Pricing | SOW send |
| OQ-1 | Odoo 17 vs 19 confirm | Commercial clarity (eng supports both) |
| PH1-02 | Live Odoo staging | Live sync proof |
| G-R2-04 | Arabic native QA | Tag `v9.1.1-r2` |
| PH1-01 | SOW send | Depends OQ-7 |
| #70/#72 | Validate residuals | Docker stack ops |

### 1.5 Concurrent work caution

Uncommitted `apps/web` UX changes and peer migrations observed at Speckit start. Speckit will not fight those edits; converge appends remaining after implement.

---

## 2. Cross-Artifact Consistency (Spec 024)

| Check | Result |
|-------|--------|
| Spec FR ↔ Plan structure | ALIGNED (see plan.md) |
| Spec US ↔ Tasks coverage | ALIGNED (T001+ map US1–US6) |
| Constitution I RLS | Migrations include `_rls` |
| Constitution VII honesty | COM tasks HUMAN-only |
| Constitution IX absorb | Plan/tasks say verify-not-recreate 051–059 |
| Phase 4/5 in tasks | BACKLOG tasks marked `[BACKLOG]` / `[HUMAN]` as appropriate |
| Duplicate CREATE 055 | AVOIDED (ALTER) |

### Findings

| ID | Severity | Finding | Remediation |
|----|----------|---------|-------------|
| A-1 | MEDIUM | Schema ahead of application code | Implement US1–US3 cores this run |
| A-2 | LOW | fea-svc tests dir may be empty/partial | Add unit tests with Speckit implement |
| A-3 | INFO | analyze before plan (user pipeline order) | Status section written first; consistency after tasks |
| A-4 | CRITICAL if violated | Inventing G-R2-04 / OQ-7 close | Forbidden — monitored |

**Overall**: READY to plan/tasks/implement with absorb strategy.

---

## 3. Coverage matrix (spec stories → tasks)

| Story | Tasks | Notes |
|-------|-------|-------|
| US1 Predictive | T010–T014 | Core eng |
| US2 Root cause / exceptions | T015–T020 | Core eng |
| US3 Auction / batch | T021–T025 | Core eng |
| US4 Upload | T026–T029 | Scaffold; compose residual OK |
| US5 Orchestrator | T030–T032 | Stub chain |
| US6 Program honesty | T033–T036 | Docs + feature.json |
| COM / validate | T040–T045 | HUMAN / OPEN |
| Phase 4/5 backlog | T050–T055 | Document only |

---

## 4. Remediation plan (executed by subsequent phases)

1. Plan + data-model + contracts for Ops P3 APIs  
2. Tasks + GH issues  
3. Implement app-layer gaps + tests  
4. Converge residuals (compose upload, P4/P5, Docker validate, COM)
