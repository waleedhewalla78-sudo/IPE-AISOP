# Research: Release Stabilization & Deployment Gates

**Feature**: 002-release-stabilization-gates  
**Date**: 2026-06-21  
**Status**: Complete — all technical context resolved

---

## R1: Authoritative Readiness Score

**Decision**: Use **74/100** as pre-stabilization baseline (audit-report.md, live validation); target **85/100** post-Gate 2; do not publish 87, 90, or 99 until independently re-measured.

**Rationale**:
- **74/100** — Derived from audit dimension scores with live test failures and Docker not running
- **87/100** — Pre-Gate 2 projection in `000-project-completion/spec.md`; overstated without green E2E
- **99/100** — tasks.md completion projection; conflates "code exists" with "validated releasable"
- **90/100** — Internal contradiction in `001-production-readiness-convergence/plan.md`

**Alternatives considered**:
- Single jump to 99 after doc sync only — rejected; no live validation evidence
- Keep multiple scores per audience — rejected; violates FR-009

---

## R2: Test Count Methodology

**Decision**: Report **~700+ test functions** counting only project-owned `test*.py` under `ipe/` excluding `.venv`, `node_modules`, `.pytest_cache`, and site-packages.

**Rationale**: Raw recursive scan returned **154,225** — included third-party packages in `.venv`. Per-file grep across `services/`, `tests/`, `apps/web/tests/` yields ~700–900 range aligned with AGENTS.md.

**Alternatives considered**:
- pytest `--collect-only` per service — preferred for Gate 1 evidence (exact count)
- CI badge from coverage.xml — deferred

---

## R3: Gate 1 Test Failure Root Causes

**Decision**: Fix environment + test drift; do not lower test standards or skip suites.

| Failure | Root Cause | Fix |
|---------|------------|-----|
| JWT 3 failures | Empty `JWT_SECRET_KEY` in test env | conftest sets dev secret from `.env.template` |
| dpe-svc collection error | `GL_ACCOUNT_MAP` renamed to `DEFAULT_GL_ACCOUNT_MAP` | Update test imports |
| cap-svc abort | OTel exporter writes after pytest closes stdout | Disable OTel in test profile or use `OTEL_SDK_DISABLED=true` |

**Alternatives considered**:
- Skip JWT tests on Windows — rejected; violates FR-003
- `@pytest.mark.skip` for cost_accounting — rejected; violates constitution III

---

## R4: Docker Stack Validation Strategy

**Decision**: Use production-like `docker-compose.yml` (not test overlay) for Gate 2 E2E; use `docker-compose.test.yml` only for CI parity checks.

**Rationale**: Status report E2E claims (15/15, 16/16) were validated against full stack with migrate init container.

**Port overrides** (documented in quickstart):
- Redis host: **6380** (not 6379)
- dpe-svc external: **8020** (not 8011)

**Alternatives considered**:
- Mock all integration tests — rejected; violates FR-007

---

## R5: Documentation Reconciliation Priority

**Decision**: Resolve **12 CRITICAL+HIGH** conflicts first (C1–C3, H1–H9); MEDIUM/LOW in same PR if time permits.

**Rationale**: Cross-artifact analysis verified 29 total; CRITICAL/HIGH block audit and handover conversations.

**Source of truth hierarchy** (during stabilization):
1. Live test/E2E evidence (Gate 1–2 logs)
2. `specs/002-release-stabilization-gates/` (this feature)
3. `audit-report.md` (74/100 baseline)
4. `000-project-completion/spec.md` (updated to match evidence)
5. `001-production-readiness-convergence/tasks.md` (task completion, with BLOCKED caveats)

**Alternatives considered**:
- Rewrite all docs from scratch — rejected; 1400+ line spec too costly
- Delete old specs — rejected; historical reference needed

---

## R6: Git Release Strategy

**Decision**: Logical commits on `master` → tag **`v1.0.0-rc1`** (release candidate, not production).

**Rationale**: Single Sprint 1 commit does not represent delivered product. RC tag allows rollback and audit trail without claiming production deployment.

**Commit grouping**:
1. `fix(test): align tests with contracts and JWT env`
2. `fix(obs): OTel test teardown`
3. `docs: reconcile readiness scores and phase status`
4. `chore(release): add READINESS.md and gate evidence`
5. `chore(release): tag v1.0.0-rc1`

**Alternatives considered**:
- Single squashed commit — acceptable if logical messages preserved in PR description
- `v1.0.0` production tag — rejected until Gate 4 (K8s canary) per audit

---

## R7: Keycloak C-007 Handling

**Decision**: Label **BLOCKED** in all artifacts; do not claim FR-008/FR-009/FR-010 SSO production-ready.

**Rationale**: No Azure AD/Okta sandbox credentials available.

**Alternatives considered**:
- Mock IdP in Docker — partial; insufficient for SAML/SCIM production claims

---

## R8: Makefile vs Windows Parity

**Decision**: Add `scripts/run-all-tests.ps1` and document PowerShell equivalents for `make docker-up`, `make test`, `make migrate`.

**Rationale**: User environment is Windows; constitution requires cross-platform support.

**Alternatives considered**:
- WSL-only documentation — rejected; excludes native Windows workflow
