# Feature Specification: Release Stabilization & Deployment Gates

**Feature Branch**: `002-release-stabilization-gates`

**Created**: 2026-06-21

**Status**: Approved (Gate 1–3 passed 2026-06-22)

**Input**: Inferred from IPE status report (2026-06-21), `SPECKIT-CHECKLIST.md`, `CROSS-ARTIFACT-ANALYSIS.md`, and live validation findings (uncommitted work, local test/env drift, Docker stack not running).

---

## Executive Summary

The IPE platform is functionally mature (14 microservices, 21 migrations, 700+ documented tests, compliance modules, executive UX) but **not yet releasable as a coherent v1.0.0 artifact**. Engineering work exists largely outside git history; local validation fails on environment and test drift; planning documents disagree on readiness scores and completion status.

This feature defines the **minimum stabilization work** required so stakeholders can trust that the codebase, documentation, and deployment path describe the same product—and that automated verification passes before production promotion.

**Out of scope**: New product capabilities (Stripe billing, mobile app, federated learning, feature store), live SAP/D365 connectors, and Keycloak testing against a real enterprise IdP (blocked on sandbox credentials).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Engineering Team Validates a Releasable Build (Priority: P1)

As a **backend or frontend engineer**, I need to clone the repository, configure a documented dev environment, and run the full automated test suite with **zero collection errors and no unexplained failures**, so I can confidently merge changes without regressions.

**Why this priority**: Without a green local/CI baseline, every subsequent feature or deployment is unverifiable. Current drift (stale imports, missing secrets, OTel teardown errors) blocks trust in the 700+ test claim.

**Independent Test**: A new engineer follows the setup guide, runs the documented test command(s), and receives a pass result on all required suites (unit + integration where infra is available) within one working session.

**Acceptance Scenarios**:

1. **Given** a fresh clone with documented environment variables set, **When** the engineer runs the standard test command, **Then** no test module fails to import or collect.
2. **Given** the shared authentication test suite, **When** dev secrets are configured per template, **Then** token creation and validation tests pass.
3. **Given** a service whose production code renamed a public constant, **When** its tests run, **Then** tests reference the current contract (no import errors on renamed symbols).

---

### User Story 2 - Operations Team Brings Up a Verifiable Stack (Priority: P1)

As an **SRE or DevOps engineer**, I need to start the platform stack from documented compose instructions and confirm all application services report healthy status, so staging and demo environments can be reproduced reliably.

**Why this priority**: The status report found the IPE Docker stack was not running locally; E2E and integration tests cannot be validated without a live stack.

**Independent Test**: Run the documented `docker compose up` flow; within 90 seconds all defined health checks return success; a documented smoke script hits representative endpoints without 5xx errors.

**Acceptance Scenarios**:

1. **Given** Docker and documented ports available, **When** the engineer starts the stack, **Then** database migration completes before dependent services accept traffic.
2. **Given** all containers are up, **When** health endpoints are queried, **Then** each core planning service returns a successful health response.
3. **Given** the integration test suite marked as requiring live infra, **When** run against the stack, **Then** documented E2E scenarios pass at the rate claimed in release materials (≥15/15 for phase 5–6 paths, ≥15/15 for sprint-2 paths).

---

### User Story 3 - Product & Audit Stakeholders Read One Truth (Priority: P1)

As a **product owner or compliance reviewer**, I need specification, plan, task, and checklist documents to agree on completion status, readiness score, and open blockers, so handover and audit conversations do not contradict each other.

**Why this priority**: Cross-artifact analysis identified **29 inconsistencies** (e.g., spec says "NOT STARTED" while tasks say "COMPLETE"; three different readiness scores: 74, 87, 99).

**Independent Test**: Run a documentation reconciliation checklist; zero CRITICAL or HIGH cross-artifact conflicts remain; a single authoritative readiness score is published with rationale.

**Acceptance Scenarios**:

1. **Given** the master spec and task list, **When** a reviewer compares sprint/phase status tables, **Then** no item is marked complete in one artifact and not started in another.
2. **Given** the convergence plan, **When** a reviewer checks readiness score, **Then** exactly one current score is stated with aligned sub-dimension scores.
3. **Given** the Speckit checklist blockers section, **When** compared to plan verify gates, **Then** blocked items (e.g., Keycloak live IdP) are consistently marked BLOCKED—not COMPLETE—in all artifacts.

---

### User Story 4 - Release Manager Passes Deployment Gates (Priority: P2)

As a **release manager**, I need a short, ordered gate checklist (critical fixes → staging validation → canary) with measurable pass/fail criteria, so production promotion requires evidence—not assumptions.

**Why this priority**: Audit report scored deployment readiness at 74/100 with 8 active risks; gate model exists in audit but is not tied to a single executable spec.

**Independent Test**: Release manager completes Gate 1 checklist items with recorded evidence (test output, smoke results, TLS/JWT procedure documented); no Gate 2 item starts until Gate 1 is fully green.

**Acceptance Scenarios**:

1. **Given** Gate 1 (critical fixes), **When** all items are checked, **Then** no known broken public endpoints remain from the audit critical list.
2. **Given** Gate 2 (staging), **When** integration and load smoke tests run, **Then** error rate stays below 1% and user-facing latency stays within documented SLA targets.
3. **Given** Gate 3 (canary), **When** 48-hour observation completes, **Then** on-call runbook exists and SRE ownership is assigned or explicitly waived with risk acceptance.

---

### User Story 5 - Version Control Reflects Delivered Product (Priority: P2)

As a **technical lead**, I need the git history to capture the current codebase state in logical commits (or a tagged release candidate), so rollback, blame, and external audit trails are possible.

**Why this priority**: Only one commit exists on `master` while hundreds of files are modified or untracked—v1.0.0 release notes do not match version control reality.

**Independent Test**: `git log` shows commits covering major phase deliveries; a release tag (e.g., `v1.0.0-rc1`) points to a tree that passes Gate 1 tests.

**Acceptance Scenarios**:

1. **Given** the working tree after stabilization fixes, **When** changes are committed, **Then** no orphaned duplicate service directories exist outside the monorepo root.
2. **Given** a release tag, **When** checked out, **Then** documented test and compose instructions succeed without undeclared manual steps.

---

### Edge Cases

- What happens when Postgres/Redis/Kafka ports conflict with other local projects? Documented port overrides must be tested (historically Redis 6380, dpe-svc 8020).
- How does validation behave when optional AI keys (Anthropic) are unset? Copilot and NLP classification must degrade gracefully with documented fallback behavior—not hard failures in unrelated suites.
- What if Keycloak live IdP sandbox is unavailable? C-007 remains BLOCKED; spec/plan must not claim SSO is production-verified.
- What when integration tests skip due to missing infra? Skips must be explicit, counted, and separated from passes in release evidence.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST provide a documented, reproducible developer setup (environment template + setup steps) that enables test execution without undeclared secrets.
- **FR-002**: All automated test modules MUST collect successfully; zero import/collection errors across required service suites.
- **FR-003**: Authentication-related unit tests MUST pass when dev credentials from the template are applied.
- **FR-004**: Test code MUST stay aligned with production contracts (renamed modules, constants, and endpoints reflected in tests within the same release).
- **FR-005**: Docker compose documentation MUST start the full application stack with migration-before-traffic ordering.
- **FR-006**: Health verification MUST confirm every core planning service is reachable after stack startup within a documented time budget (≤90 seconds for health checks).
- **FR-007**: Documented integration/E2E suites MUST pass at claimed counts when run against the live stack, or claims MUST be revised downward with evidence.
- **FR-008**: Cross-artifact reconciliation MUST resolve all CRITICAL (3) and HIGH (9) inconsistencies identified in `CROSS-ARTIFACT-ANALYSIS.md`.
- **FR-009**: A single authoritative **deployment readiness score** MUST be published with aligned sub-scores; conflicting values (74, 87, 90, 99) MUST not coexist in active documents.
- **FR-010**: Blocked work (Keycloak live IdP) MUST be labeled BLOCKED consistently—not COMPLETE—in spec, plan, tasks, and checklist.
- **FR-011**: Release gate checklists (critical → staging → canary) MUST map to measurable pass/fail criteria traceable to test or smoke output.
- **FR-012**: Git history MUST capture stabilization deliverables such that a release tag identifies a testable tree.
- **FR-013**: Known deferred FRs (Stripe, mobile, WCAG audit, feature store) MUST remain explicitly OUT OF SCOPE in this feature to prevent scope creep.

### Key Entities

- **Release Gate**: A ordered checkpoint (Gate 1–3) with entry criteria, verification evidence, and exit decision (pass/fail/waived).
- **Cross-Artifact Conflict**: A documented mismatch between spec, plan, tasks, or checklist (severity: CRITICAL/HIGH/MEDIUM/LOW).
- **Validation Evidence**: Immutable artifact (test log, smoke output, checklist sign-off) proving a gate requirement is met.
- **Readiness Score**: Composite metric with dimension breakdown (product, testing, security, ops) and single current value.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new engineer completes environment setup and runs the full required test suite in **under 4 hours** on first attempt using only documented steps.
- **SC-002**: **100%** of test modules collect without import errors; **zero** unexplained failures in Gate 1 required suites.
- **SC-003**: Stack startup health checks reach **100% success** for all core planning services within **90 seconds** of documented compose up.
- **SC-004**: Integration/E2E pass rate matches or exceeds documented claims (**≥31/31** combined sprint-2 + phase 5–6 scenarios when infra is available), or documentation is corrected within 24 hours of discovery.
- **SC-005**: Cross-artifact CRITICAL and HIGH conflicts reduced from **12 to 0** in active documents.
- **SC-006**: Exactly **one** readiness score published; stakeholders can cite it without encountering conflicting numbers in spec/plan/checklist.
- **SC-007**: Release Gate 1 checklist achieves **100%** item completion with attached evidence before Gate 2 work begins.
- **SC-008**: Git repository contains commits (or tag) representing stabilization work; release notes reference a verifiable revision.

---

## Assumptions

- Stabilization targets the existing IPE monorepo under `ipe/`; no greenfield rewrite.
- Windows and Linux are both supported development platforms; PowerShell equivalents exist or are documented for shell scripts.
- Anthropic API keys remain optional for Gate 1; graceful NLP fallback is acceptable evidence.
- Keycloak live IdP testing stays blocked until Azure AD/Okta sandbox credentials are provided—this feature documents the block rather than resolving it.
- Production deployment still requires K8s-specific items (mTLS runtime, log aggregation) as Gate 2+ ops work, not Gate 1 engineering fixes.
- Current audit baseline readiness of **74/100** is the honest starting point until gates pass; target after Gate 1+2 is **≥85/100** with documented residual risks.

---

## Dependencies

- Existing `000-project-completion` and `001-production-readiness-convergence` artifacts (plan/tasks) as source material—not authoritative until reconciled.
- `.specify/memory/constitution.md` principles (RLS, RBAC, test-backed changes) apply to any code fixes under this feature.
- Docker Desktop (or equivalent) available on validation machines.
- Prior test result files and audit reports (`audit-report.md`, `AGENTS.md`) as evidence inputs.

---

## Constitution Alignment Notes

Stabilization fixes MUST NOT weaken:

- **Principle I**: Tenant RLS on all `tenant_id` tables.
- **Principle II**: No new unauthenticated state-changing endpoints.
- **Principle III**: Every behavioral fix includes or updates automated tests.
- **Principle VI**: Health/readiness/metrics endpoints remain on all services.

Violations discovered during stabilization MUST be filed as blockers, not silently waived.
