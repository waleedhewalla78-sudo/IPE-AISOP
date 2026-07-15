# Clarifications — Spec 024 Ops Phase 3

**Date**: 2026-07-15  
**Method**: Full analysis against Blueprint/Tech Spec/Premium/Planning-Command-Deep + tree inventory (no interactive Q&A — pipeline non-stop; decisions encoded here and into `spec.md`)

## Clarification Log

### Q1 — Platform Phase 3 vs Ops Blueprint Phase 3 numbering
**Decision**: Treat as distinct. Platform Phase 3 (`v9.4.0-p3` Helm/K8s) is DONE. Spec 024 is **Ops Blueprint Phase 3** only. Constitution Principle IX + Phase Naming Map bind this.  
**Status**: Resolved → encoded in constitution 1.3.0 and spec Context.

### Q2 — Migration 055 CREATE vs existing 041 `cdm_supplier_score`
**Decision**: ALTER-only (peer migration `055_cdm_supplier_score_phase3.py` already correct). Speckit MUST NOT emit CREATE.  
**Status**: Resolved → FR-001 / plan data-model note.

### Q3 — Scope of Spec 024 vs Phase 4/5
**Decision**: Spec 024 **implements** Ops Phase 3 eng slice; Phase 4/5 captured as FR-B* backlog in same feature for program visibility; separate feature numbers MAY be cut later (025/026) without rewriting Spec 024 history.  
**Status**: Resolved.

### Q4 — Concurrent Phase agents writing code
**Decision**: Absorb existing untracked/peer migrations 051–059; implement application-layer gaps (predictive scorer, root cause, auction/batcher, orchestrator stubs, tests). Do not revert unrelated `apps/web` UX edits. Converge absorbs peer outcomes after implement.  
**Status**: Resolved.

### Q5 — upload-svc on R1 compose this sprint?
**Decision**: Scaffold + history schema first; full wizard UI + compose/Kong wiring may remain converge residual if time-boxed. Honesty over fake "production upload".  
**Status**: Resolved → US4 acceptance #3.

### Q6 — Commercial blockers
**Decision**: OQ-7, OQ-1, PH1-02, G-R2-04, SOW send remain **OPEN — HUMAN**. No Speckit task may close them.  
**Status**: Resolved (constitution VII).

### Q7 — Predict API auth roles
**Decision**: Same as existing feasibility routes — planner/manager/admin/auditor read; mutations admin/planner where applicable.  
**Status**: Resolved.

### Q8 — Kafka dependency for agent chain
**Decision**: R1 may have empty Kafka; orchestrator uses direct HTTP/in-process calls and still writes `cdm_agent_activity_log`.  
**Status**: Resolved → NFR / US5.

## Coverage Map (post-clarify)

| Category | Status |
|----------|--------|
| Functional scope | Clear |
| Out of scope | Clear (nexus; COM; Platform P4/P5 invent) |
| Personas | Clear (planner, admin, program owner) |
| Data model | Clear (051–059) |
| Lifecycle/exceptions | Clear |
| Auth/RBAC | Clear |
| Scale assumptions | Partial (NFR p95 best-effort) |
| Phase 4/5 detail | Partial by design (backlog) |
| Upload wizard UX | Partial (scaffold OK) |

## Underspecified retained (acceptable)

- Exact WhatsApp notification channel for exceptions (POST-R1).
- Customer portal auth model (Phase 4).
- Collaborative multi-user conflict UX (Phase 5).
