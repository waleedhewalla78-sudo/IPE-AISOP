# Feature Specification: Phase 3 — AI Agents + Data Onboarding

**Feature Branch**: `024-phase3-ai-agents`

**Created**: 2026-07-15

**Status**: ENG IN PROGRESS → target ENG COMPLETE this execution

**Input**: IPE-Phase3-Blueprint-v2.0.md (product/scope) + IPE-Phase3-Technical-Spec-v2.0.md (implementation acceptance).

**Prior features**: 023 sprint4-wave1 ENG COMPLETE. Constitution **1.2.8**.

**Depends on**: Migration head ≥050; R2 stack; planning modules from Spec 020.

---

## Conflict notes (Blueprint vs Technical Spec)

| Topic | Blueprint | Technical Spec | Resolution |
|-------|-----------|----------------|------------|
| Supplier score table | Implied new | Migration 055 CREATE `cdm_supplier_score` | **041 already created table** → 055 ALTER adds Phase 3 columns |
| Resolution generate-all | A5 in process map | Tech Spec orchestrator calls `dpe-svc /api/v1/resolution/generate-all` | **res-svc owns `/api/v1/resolution`** → implemented as `POST /api/v1/agents/generate-resolutions` on dpe-svc |
| Scope waves | Full operational vision | Cursor prompt lists 10 engineering items | Treat 10 items as **Phase 3 Wave 1 MVP**; S&OP monthly process depth / WhatsApp alerts deferred |

Commercial blockers remain OPEN (OQ-7, PH1-02, G-R2-04, Odoo 17 vs 19, SOW send). Do not fake.

---

## User Stories

### US1 — Data onboarding wizard (P1)

As a planner/admin without live Odoo, I upload the 14 Excel file types through a 5-phase wizard with validation and agent activation.

### US2 — Predictive risk + root cause (P1)

As a planner, I see MO feasibility at T+3/7/14 and a 5-why chain with recommendations.

### US3 — Smart batching + capacity auction (P1)

As a planner, I optimise changeover and resolve WC conflicts with financial rationale.

### US4 — Demand fusion + supplier/stockout intel (P1)

As a planner, I see fused demand signals and predictive stockout / supplier scorecards.

### US5 — Orchestrator + exceptions + Copilot briefs (P1)

As a planner, agents run in chain after data changes; exceptions have SLA lifecycle; Copilot morning brief / meeting prep are available.

---

## Acceptance (Technical Spec §7)

1. upload-svc :8120 with wizard + validation
2. Predictive scoring in fea-svc
3. Root cause chain in fea-svc
4. Smart batching in cap-svc
5. Capacity auction in cap-svc
6. Demand signal fusion in demand-svc
7. Agent orchestrator in dpe-svc
8. Exception framework
9. Contextual Copilot
10. Frontend pages + migrations 051–059

---

## Out of scope / deferred

- Live WhatsApp push for exceptions
- Full monthly S&OP four-meeting UI beyond executive brief API
- Writing all 14 Excel schemas into Odoo write-back (upload validates; CDM persist best-effort / in-memory wizard for MVP)
- Commercial closure items
