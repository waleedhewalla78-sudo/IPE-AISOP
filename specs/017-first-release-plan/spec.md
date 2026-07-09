# Feature Specification: IPE First Release Plan (017)

**Feature**: `017-first-release-plan`  
**Version**: 1.0  
**Date**: 2026-07-09  
**Status**: Phase 0 in progress — Wave 1 starting  
**Sources**: `IPE-First-Release-Plan.docx`, `IPE-Priority-Features-Roadmap (2).docx`, `IPE-Cursor-Prompt-Suite.docx`  
**Constitution**: v1.2.3  
**Depends on**: Spec 015 (enterprise gates), Spec 016 (Sprint 7 cohesion)  
**Release targets**: `v9.4.0-p3` (Phase 0) → Wave features through Week 15

---

## 1. Vision

Ship **v9.4.0-p3** with enterprise Phase 3 gate evidence, then deliver **nine priority expansion features** in three waves — UX foundation, AI/ML intelligence, and supply-chain automation — without diluting Constitution principles I–VIII.

---

## 2. Scope

### Phase 0 — Close `v9.4.0-p3` (Week 1)

| ID | Requirement | Acceptance |
|----|-------------|------------|
| FR-017-P0-01 | Stable kind cluster (1 replica, no HPA conflict) | All pods 1/1; ingress 200 |
| FR-017-P0-02 | Gate 11 R1 K8s demo | ≥12/14 PASS with evidence file |
| FR-017-P0-03 | Sprint 7 activity emitters | T717–T719 + tests 5/5 each |
| FR-017-P0-04 | Migration 038 applied | `cdm_activity_event` on compose + K8s |
| FR-017-P0-05 | Tag `v9.4.0-p3` | Git tag + GATE-RESULTS updated |

### Wave 1 — Foundation (Weeks 2–5)

| ID | Feature | User story |
|----|---------|------------|
| FR-017-W1-01 | **Copilot R1 nav** | US-W1-01: Planner sees Copilot in R1 sidebar without full AI hub |
| FR-017-W1-02 | **Admin Odoo Config v2** | US-W1-02: Admin validates mappings and tests Odoo connection <5s |
| FR-017-W1-03 | **OTD Analytics Dashboard** | US-W1-03: Manager views 5 OTD KPIs filtered by supplier/line/region |

### Wave 2 — Intelligence (Weeks 6–11)

| ID | Feature | User story |
|----|---------|------------|
| FR-017-W2-01 | Multi-Tenant Ops Tooling | US-W2-01: Operator provisions tenant in one API call |
| FR-017-W2-02 | Scenario Workbench | US-W2-02: Planner compares two what-if scenarios side-by-side |
| FR-017-W2-03 | Demand Sensing (SES/Prophet) | US-W2-03: Planner gets blended forecast with confidence intervals |
| FR-017-W2-04 | Predictive Delay Engine | US-W2-04: Planner sees delay risk with SHAP explanation |

### Wave 3 — Automation (Weeks 12–15)

| ID | Feature | User story |
|----|---------|------------|
| FR-017-W3-01 | NL Schedule Change | US-W3-01: Planner moves an MO via natural language with preview |
| FR-017-W3-02 | Automated Supplier Comms | US-W3-02: Supplier receives email on reschedule rule trigger |

---

## 3. Non-functional requirements

| ID | Requirement |
|----|-------------|
| NFR-017-01 | All new services: FastAPI 3.12, RLS, `/health`/`/metrics`, Kong route |
| NFR-017-02 | Wave 2 ML: MAPE <15% (demand), AUC >0.80 (delay) on holdout |
| NFR-017-03 | No Wave 2+ code merged before `v9.4.0-p3` tag (Spec 015 alignment) |
| NFR-017-04 | Arabic i18n on all Wave 1 user-facing screens |

---

## 4. Out of scope

- NEXUS Social product
- Live SAP/D365 connectors (scaffold only)
- EDI supplier communications (Wave 3 email only)
- Gate 11 waiver without OQ-9 stakeholder sign-off

---

## 5. References

- `plan.md`, `tasks.md`, `clarify.md`, `analyze.md`, `converge.md`
- `docs/PRD-IPE-AUTHORITATIVE.md`
- Cursor Prompt Suite prompts 1–11

---

*Spec v1.0 — `/speckit.specify` 2026-07-09*
