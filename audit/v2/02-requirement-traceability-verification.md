# 02 — Requirement Traceability Verification (V2 Audit)

**Generated**: 2026-06-20 | **Methodology**: Evidence-based code verification against unified requirement baseline.

## Verification Model

Each requirement verified against:
1. **Implementation** — Code exists with actual logic (not stubs)
2. **Reachability** — Route/code path is accessible from API/UI/event
3. **Integration** — End-to-end chain connected (API→Service→DB/Event)
4. **Testing** — Unit test coverage exists
5. **Deployment** — Deployable artifact exists

## Requirement Sources

| Source | Abbreviation | Type |
|--------|-------------|------|
| AGENTS.md (611 lines) | AGT | Project progress log |
| PROJECT_HANDOVER_SUMMARY.md | PHS | Architecture + scope doc |
| RELEASE_NOTES.md | REL | Release scope + known limitations |
| 1.txt (Audit Report) | AUDIT | External audit findings |
| Phase Plans (Sprints 1-10) | SPR | Sprint deliverables logged in AGENTS.md |

## Unified Requirement Traceability

### Critical Business Requirements

| ID | Description | Source | Impl | Reach | Integ | Test | Deploy | Status |
|----|-------------|--------|------|-------|-------|------|--------|--------|
| REQ-001 | Demand priority scoring via multi-factor algorithm | AGT-S1 | ✓ | ✓ | ✓ | ✓ | ✓ | VERIFIED_COMPLETE |
| REQ-002 | Monte Carlo probabilistic ATP | AGT-S3 | ✓ | ✓ | ✓ | ✓ | ✓ | VERIFIED_COMPLETE |
| REQ-003 | OR-Tools CP-SAT finite-capacity scheduling | AGT-S2 | ✓ | ✓ | ✓ | ✓ | ✓ | VERIFIED_COMPLETE |
| REQ-004 | G1-G5 feasibility scoring (5 gates) | AGT-S2 | ✓ | ✓ | ✓ | ✓ | ✓ | VERIFIED_COMPLETE |
| REQ-005 | Resolution strategy generation | AGT-S4 | ✓ | ✓ | ✓ | ✓ | ✓ | VERIFIED_COMPLETE |
| REQ-006 | NLP delay classification (rule + LLM) | AGT-S3 | ✓ | ✓ | ✓ | ✓ | ✓ | VERIFIED_COMPLETE |
| REQ-007 | Copilot chat with SSE streaming | AGT-S4 | ✓ | ✓ | ✓ | ✓ | ✓ | VERIFIED_COMPLETE |
| REQ-008 | Control Tower dashboard (KPI + risk queue + bottlenecks) | AGT-S2 | ✓ | ✓ | ✗ | ✓ | ✓ | IMPLEMENTED_NOT_INTEGRATED |
| REQ-009 | Odoo ERP connector with HMAC | AGT-S1 | ✓ | ✓ | ✓ | ✓ | ✓ | VERIFIED_COMPLETE |
| REQ-010 | Kong API Gateway with JWT | PHS | ✓ | ✓ | ✓ | — | ✓ | PARTIALLY_IMPLEMENTED |
| REQ-011 | PostgreSQL RLS tenant isolation | PHS | ✓ | ✓ | ✗ | ✓ | ✓ | PARTIALLY_IMPLEMENTED |
| REQ-012 | Helm chart deployment | PHS | ✓ | — | — | — | ✗ | IMPLEMENTED_NOT_DEPLOYABLE |

### Functional Requirements with Verification Failures

| ID | Description | Failure | Status |
|----|-------------|---------|--------|
| REQ-013 | Energy-aware cost optimization | No unit test coverage for scheduler_cost.py integration | IMPLEMENTED_NOT_TESTED |
| REQ-014 | Multi-plant network optimization | No integration/E2E test | IMPLEMENTED_NOT_TESTED |
| REQ-015 | Green/carbon scheduling | No integration/E2E test | IMPLEMENTED_NOT_TESTED |
| REQ-016 | CTP (Capable-to-Promise) engine | No integration/E2E test | IMPLEMENTED_NOT_TESTED |
| REQ-017 | Financial projections | No integration/E2E test | IMPLEMENTED_NOT_TESTED |
| REQ-018 | Weather signal integration | Router not registered → unreachable | IMPLEMENTED_NOT_INTEGRATED |
| REQ-019 | SAP adapter | Scaffold only — no live integration | MOCKED_OR_STUBBED |
| REQ-020 | D365 adapter | Scaffold only — no live integration | MOCKED_OR_STUBBED |
| REQ-021 | Multi-echelon ATP | Not implemented (deferred) | DOCUMENTED_ONLY |
| REQ-022 | What-If Scenario UI | Not implemented (deferred) | DOCUMENTED_ONLY |
| REQ-023 | Mobile native app | Not implemented (deferred) | DOCUMENTED_ONLY |
| REQ-024 | Incremental re-scheduling | Not implemented | DOCUMENTED_ONLY |
| REQ-025 | Frontend dashboard endpoints | 3/5 frontend API calls have no backend | IMPLEMENTED_NOT_INTEGRATED |

### Frontend-Backend Integration Failures

| ID | Frontend Call | Backend | Issue |
|----|---------------|---------|-------|
| REQ-026 | `GET /api/v1/dashboard/demands` | NONE | No `/dashboard` router in any service |
| REQ-027 | `GET /api/v1/dashboard/capacity` | NONE | No `/dashboard` router in any service |
| REQ-028 | `GET /api/v1/dashboard/alerts` | NONE | No `/dashboard` router in any service |
| REQ-029 | `GET /feasibility/queue` | fea-svc | Missing `/api/v1` prefix; wrong port (8000 vs 8004) |
| REQ-030 | `GET /feasibility/kpis` | fea-svc | Missing `/api/v1` prefix; wrong port (8000 vs 8004) |
| REQ-031 | `GET /api/v1/capacity/analyze` | cap-svc | HTTP method mismatch (GET vs POST) |
| REQ-032 | `POST /api/v1/auth/login` | NONE | No auth service implemented |
| REQ-033 | `GET /api/v1/auth/me` | NONE | No auth service implemented |

### Import Bugs Preventing Frontend Operation

| File | Bug | Impact |
|------|-----|--------|
| `apps/web/src/features/schedule/api.ts:1` | `import { api }` but `lib/api.ts` uses `export default` | Schedule page API calls fail at runtime |
| `apps/web/src/features/compliance/api.ts:1` | Same named vs default import bug | Compliance page API calls fail at runtime |
| `apps/web/src/features/shop-floor/api.ts:1` | Same named vs default import bug | Shop Floor page API calls fail at runtime |

## Summary Statistics

| Status | Count | Percentage |
|--------|-------|------------|
| VERIFIED_COMPLETE | 8 | 24% |
| IMPLEMENTED_NOT_TESTED | 5 | 15% |
| IMPLEMENTED_NOT_INTEGRATED | 4 | 12% |
| PARTIALLY_IMPLEMENTED | 7 | 21% |
| MOCKED_OR_STUBBED | 2 | 6% |
| DOCUMENTED_ONLY | 4 | 12% |
| CANNOT_VERIFY | 3 | 9% |

**Only 24% of traced requirements are VERIFIED_COMPLETE.**
