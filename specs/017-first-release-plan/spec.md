---
status: ACTIVE
note: Wave 1 in progress
date: 2026-07-11
---

# Feature Specification: IPE First Release Plan (017)

**Feature**: `017-first-release-plan`  
**Version**: 2.0  
**Date**: 2026-07-10  
**Status**: Phase 0 **COMPLETE** · Wave 1 **IN PROGRESS** (2/8) · Phase 1 UAT **BLOCKED** (commercial)  
**Sources**: IPE-UAT-Phases-0-3.docx, IPE-Strategy-Assessment (July 2026), IPE-First-Release-Plan.docx, PRD  
**Constitution**: v1.2.4  
**Depends on**: Spec 015 (gates), Spec 016 (Sprint 7), Star Trans Phase 1 blueprint  
**Release**: `v9.4.0-p3` @ `4629119` · HEAD `ad494e0`

---

## 1. Vision

Deliver a **customer-validated, revenue-ready** IPE Release 1 for MENA mid-market discrete manufacturing: live Odoo closed loop, measurable OTD improvement, and a sequenced expansion path (Waves 1–3) without diluting Constitution principles I–VIII.

---

## 2. What we build (program scope)

### 2.1 Phase 0 — Release stabilization ✅ DONE

| ID | Requirement | Acceptance | Status |
|----|-------------|------------|--------|
| FR-017-P0-01 | Stable kind cluster | 8/8 pods 1/1; ingress health 200 | ✅ |
| FR-017-P0-02 | Gate 11 K8s demo | ≥12/14 + evidence | ✅ 12/14 |
| FR-017-P0-03 | Sprint 7 emitters T717–T719 | 5/5 tests each | ✅ 20/20 |
| FR-017-P0-04 | Migration 038 | `cdm_activity_event` compose + K8s | ✅ head 038 |
| FR-017-P0-05 | Tag `v9.4.0-p3` | Git tag + GATE-RESULTS | ✅ |
| FR-017-P0-06 | OQ-9 waiver | Documented §6 sign-off | ✅ template |

### 2.2 Phase 1 — Star Trans go-live (UAT §4) ⬜ BLOCKED

| ID | Requirement | User story |
|----|-------------|------------|
| FR-017-PH1-01 | Signed SOW + Odoo staging access | As CEO, I can authorize UAT on real factory data |
| FR-017-PH1-02 | R1.1 stock.quant sync (FR-R1-05) | As planner, material gate uses on-hand inventory |
| FR-017-PH1-03 | OTD baseline capture (FR-R1-16) | As manager, I see pre-go-live OTD baseline |
| FR-017-PH1-04 | Admin Odoo config self-service | As admin, I configure Odoo without SQL |
| FR-017-PH1-05 | Arabic QA (RTL) | As Arabic planner, I complete triage/resolve/approve |
| FR-017-PH1-06 | Write-back validation | As planner, approved schedule updates Odoo MO dates |
| FR-017-PH1-07 | Production go-live | As customer, I run IPE on 8GB VM compose |

### 2.3 Wave 1 — Foundation (Weeks 2–5) 🔄 25%

| ID | Feature | User story | Status |
|----|---------|------------|--------|
| FR-017-W1-01 | Copilot R1 nav | US-W1-01: Planner sees Copilot in R1 sidebar | ✅ |
| FR-017-W1-02 | Copilot smoke (auth + route + 401) | US-W1-02a: Unauthenticated users cannot access Copilot | ✅ 12/12 |
| FR-017-W1-03 | Admin Odoo Config v2 schema + API | US-W1-02: Admin validates mappings, tests connection <5s | ⬜ |
| FR-017-W1-04 | Odoo connection test endpoint | US-W1-02b: Admin verifies Odoo reachability in <5s | ⬜ |
| FR-017-W1-05 | Odoo multi-entity + versioning | US-W1-02c: Admin manages multiple Odoo instances | ⬜ |
| FR-017-W1-06 | Odoo Config v2 React UI | US-W1-02d: Admin configures Odoo without SQL | ⬜ |
| FR-017-W1-07 | OTD aggregation service | US-W1-03a: Manager queries OTD baseline API | ✅ |
| FR-017-W1-08 | OTD dashboard UI (5 KPIs) | US-W1-03: Manager views 5 OTD KPIs with filters | ✅ |

### 2.4 Wave 2 — Intelligence (Weeks 6–11) ⬜

| ID | Feature | User story |
|----|---------|------------|
| FR-017-W2-01 | Multi-Tenant Ops | US-W2-01: Operator provisions tenant in one API call |
| FR-017-W2-02 | Scenario Workbench | US-W2-02: Planner compares two what-if scenarios |
| FR-017-W2-03 | Demand sensing (simplified) | US-W2-03: Planner gets statistical forecast + intervals |
| FR-017-W2-04 | Predictive delay | US-W2-04: Planner sees delay risk with explanation |

### 2.5 Wave 3 — Automation (Weeks 12–15) ⬜

| ID | Feature | User story |
|----|---------|------------|
| FR-017-W3-01 | NL Schedule Change | US-W3-01: Planner moves MO via NL with preview |
| FR-017-W3-02 | Automated Supplier Comms | US-W3-02: Supplier receives email on reschedule rule |

### 2.6 Phase 3 UAT scope (enterprise) — PLANNED

Full Arabic 15 screens, mobile PWA, multi-site planning (if demanded). **Cut per strategy**: Design AI, SAP B1. **Deferred**: Saudi entry, enterprise K8s sales motion.

---

## 3. What we want to build (north star)

| Horizon | Outcome | Metric |
|---------|---------|--------|
| Phase 1 | Star Trans live, OTD proof | 30-day OTD trend, 2+ MOs saved |
| Wave 1 | Partner-ready Odoo config + OTD story | Admin self-service; 5 KPI dashboard |
| Wave 2 | Repeatable multi-customer ops | 6+ paying customers; tenant provision E2E |
| Wave 3 | Planner workflow transformation | NL schedule accuracy >90% |
| Phase 4+ | Platform maturity | $1M ARR, predictive moat on factory data |

---

## 4. Non-functional requirements

| ID | Requirement |
|----|-------------|
| NFR-017-01 | FastAPI 3.12, RLS, `/health`/`/metrics`, Kong/nginx route |
| NFR-017-02 | Wave 2 ML: MAPE <15%, AUC >0.80 (holdout) — simplified forecast acceptable Phase 2 |
| NFR-017-03 | Wave 2+ gated on `v9.4.0-p3` tag ✅ |
| NFR-017-04 | Arabic i18n on all Wave 1 user-facing screens |
| NFR-017-05 | Customer-validated demand before speculative features (Strategy Assessment) |

---

## 5. Out of scope

- NEXUS Social, live SAP/D365, Design AI, SAP B1 connector, ERP marketplace
- Enterprise K8s sales tier before validated enterprise customer (Phase 4)
- Gate 11 14/14 on kind without infra investment (#27 closed WON'T FIX)

---

## 6. References

- `plan.md`, `tasks.md`, `clarify.md`, `analyze.md`, `converge.md`, `implement.md`
- `docs/qa/UAT-PHASES-0-3-CORRECTIONS.md`
- `docs/PRD-IPE-AUTHORITATIVE.md`

---

*Spec v2.0 — `/speckit.specify` 2026-07-10*
