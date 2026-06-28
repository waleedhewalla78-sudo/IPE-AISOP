# Feature Specification: v8 Validation Convergence & Program Rollup

**Feature Branch**: `010-v8-validation-convergence`  
**Created**: 2026-06-27  
**Status**: Active — v8.2.0 validation complete  
**Release target**: `v8.2.0`  
**Prior features**: `007-v8-phase1-foundation`, `008-v8-phase2-expansion`, `009-v8-phase3-design-procurement`, `005-ipe-program-status`

**Purpose**: Authoritative rollup after the v8 validation sprint — cross-artifact consistency, live proof, open issues, and the post-v8 roadmap.

---

## Executive verdict

| Layer | Status | Evidence |
|-------|--------|----------|
| **v7 core** | ✅ Complete | Demo CP0–20, chaos 6/6 |
| **v8 Phase 1 (U1–U3)** | ✅ Validated | CP21–24, CP30, migration 029 |
| **v8 Phase 2 (U4–U6)** | ✅ Validated | CP25–27, migration 030 |
| **v8 Phase 3 (U7–U8)** | ✅ Validated | CP28–29, migration 031 |
| **v8 validation sprint (QA-001–010)** | ✅ Complete | 30/30 demo, 5/5 integration |
| **Staging / UAT / Demo** | ✅ Ready | `docs/qa-e2e-demo-v8-report.txt` |
| **Production deployment** | ❌ Blocked | Keycloak, secrets, Stripe, RLS ADR-002 |

---

## User stories

### US-V8-01 — Demo parity with v7 (P0)

As a **product owner**, I need **30/30 demo checkpoints** covering v7 and all v8 streams so pilot customers can walk through the SAP-gap upgrade.

**Acceptance**: `run-full-demo.ps1` passes CP0–30; report saved.

### US-V8-02 — Service health (P0)

As an **SRE**, I need all **7 v8 microservices** returning HTTP 200 on `/api/v1/health` through Kong and direct ports.

**Acceptance**: Integration test `test_v8_services_health` + manual port sweep.

### US-V8-03 — Automated test gate (P0)

As an **engineer**, I need **zero pytest failures** in CI with SageMaker/vLLM tests deselected, plus **≥25 v8 API tests**.

**Acceptance**: nlp 131 pass / 12 deselected; 26 v8 API tests; Vitest 28/28.

### US-V8-04 — Cross-service flow (P1)

As a **QA lead**, I need an integration test proving demand → scenario → supply → order → copilot session.

**Acceptance**: `tests/integration/test_v8_e2e.py` — 5/5 pass.

### US-V8-05 — Production hardening (P2 — deferred)

As a **CISO**, I need enterprise IdP, secrets manager, and full RLS INSERT policies before production.

**Acceptance**: POST-B/C backlog; explicitly out of this feature.

---

## Functional requirements

| ID | Requirement | Status |
|----|-------------|--------|
| FR-V8-01 | Migrations 029–033 applied | ✅ alembic 033 |
| FR-V8-02 | 7 v8 services in docker-compose + Kong | ✅ |
| FR-V8-03 | Demo CP21–30 | ✅ |
| FR-V8-04 | Copilot session persistence | ✅ User ORM + CP30 |
| FR-V8-05 | Role enum includes procurement | ✅ QA-008 |
| FR-V8-06 | Vitest smoke for 7 v8 pages | ✅ QA-009 |
| FR-V8-07 | PRODUCT-STATUS v8.2.0 matrix | ✅ QA-007 |
| FR-V8-08 | nlp integration tests marked | ✅ QA-006 |
| FR-V8-09 | Git tag v8.2.0 | ⬜ Pending sign-off |
| FR-V8-10 | Supply network seed data | ⬜ CP25 passes with 0 facilities |

---

## Non-goals (this feature)

- Keycloak / Azure AD live SSO (C-007)
- Stripe live billing
- Prophet/LSTM forecaster upgrade
- copilot-svc split to port 8030
- Production TLS runtime enforcement

---

## References

- [analyze.md](./analyze.md) — cross-artifact analysis
- [plan.md](./plan.md) — post-v8 technical plan
- [tasks.md](./tasks.md) — actionable backlog
- [converge.md](./converge.md) — convergence verdict
- [docs/PRODUCT-STATUS.md](../../docs/PRODUCT-STATUS.md)
- [docs/qa-e2e-demo-v8-report.txt](../../docs/qa-e2e-demo-v8-report.txt)
