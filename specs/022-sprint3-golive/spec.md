---
status: CLOSED
closed_by: sprint-3 engineering closure
date: 2026-07-11
---

# Feature Specification: Sprint 3 Star Trans Go-Live Readiness

**Feature Branch**: `022-sprint3-golive`

**Created**: 2026-07-11

**Status**: Active

**Input**: Full Speckit pipeline after Sprint 1 engineering closure (`v9.2.0-planning` @ `b04434d`) and Sprint 2 customer enablement (SOW, sales, field mapping, playbook, training, support, release notes, validate script, OQ status). Advance Spec 022 to make Star Trans R1 go-live-ready on the engineering track while documenting commercial blockers honestly.

**Prior features**: 017 → 018 → 019 → 020 → 021 (all ENG closed or superseded for this track).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Deploy package is customer-operable (Priority: P1)

As a Diligent or Star Trans ops engineer, I can take `deploy/star-trans/`, fill `.env` from the template, and bring up a healthy Release 1 stack using only the runbook and smoke checklist — without tribal knowledge.

**Why this priority**: Without a self-contained deploy package, SOW signature cannot convert into a week-1 installation.

**Independent Test**: On a workstation with Docker, copy `deploy/star-trans/`, `cp .env.template .env`, run `docker compose config`, and confirm runbook health paths match compose services. Evidence in `docs/qa/DEPLOYMENT-DRYRUN-LOG.md`.

**Acceptance Scenarios**:

1. **Given** `deploy/star-trans/` with five required files, **When** ops copies `.env.template` → `.env` and runs `docker compose config`, **Then** config validates exit 0 with no missing interpolations.
2. **Given** a configured `.env`, **When** ops follows `DEPLOY-RUNBOOK.md` health steps, **Then** documented service names and `/api/v1/health` paths match the compose file.
3. **Given** the package, **When** a reviewer checks for hardcoded secrets, **Then** none appear in committed files (secrets only in local `.env`).

---

### User Story 2 — Pre-UAT validation script proves readiness (Priority: P1)

As an implementation lead, I run `scripts/star-trans-validate.ps1` against a live stack and get a clear PASS/FAIL/SKIP summary covering health, auth, migrations/RLS signals, web UI, Arabic i18n files, and Odoo connectivity (skip when staging unavailable).

**Why this priority**: UAT cannot start without a reproducible pre-flight gate.

**Independent Test**: With R2/dev compose up, run the script; interpret SKIP on live Odoo as expected when PH1-02 is open.

**Acceptance Scenarios**:

1. **Given** Kong and core services healthy, **When** validate script runs, **Then** health and auth checks PASS (or FAIL with actionable detail).
2. **Given** no live Odoo staging (PH1-02 OPEN), **When** Odoo connectivity is probed, **Then** result is SKIP or FAIL labeled as commercial/ops blocker — never silently claimed PASS.
3. **Given** Arabic locale files in `apps/web`, **When** i18n checks run, **Then** presence of keys PASS; native QA sign-off remains a separate COM gate.

---

### User Story 3 — Program status stays honest (Priority: P1)

As the program owner, I can open PRODUCT-STATUS, OPEN-ITEMS, SOW-STATUS, OQ-RESOLUTION-STATUS, and Spec 022 analyze/converge and see accurate Sprint 2 complete / Sprint 3 active state with commercial blockers explicitly OPEN.

**Why this priority**: Constitution Principle VII honesty rule — fake closures destroy trust.

**Independent Test**: Diff status docs against git tags and `gh issue list`; no Arabic sign-off, pricing, or live Odoo claims without evidence.

**Acceptance Scenarios**:

1. **Given** Sprint 2 commits landed, **When** status docs are read, **Then** they list GTM package complete and OQ-7 / OQ-1 / PH1-02 / G-R2-04 OPEN.
2. **Given** `v9.2.0-planning` exists, **When** tag policy is stated, **Then** docs say do not push stale `v9.1.0-r2`; cut `v9.1.1-r2` only after G-R2-04.

---

### User Story 4 — GitHub hygiene for shipped work (Priority: P2)

As an engineering lead, Spec 021 bugfix issues that are already in `master` are closed or commented with evidence; Wave 2/3 and commercial issues stay open with accurate labels; new Spec 022 tasks become issues without duplicates.

**Why this priority**: Stale open bugs hide real remaining work.

**Independent Test**: `gh issue list` shows #52–#55 closed or evidenced; #50 remains OPEN; new 022 issues linked from `taskstoissues.md`.

**Acceptance Scenarios**:

1. **Given** UAT-10/11 fixes are on `master`, **When** issues #52/#53 are triaged, **Then** they are closed with commit SHA evidence or marked done with comment.
2. **Given** commercial blockers, **When** #50 is reviewed, **Then** it stays OPEN with updated Sprint 3 note.

---

### User Story 5 — Live stack smoke / planning UAT re-check (Priority: P2)

As QA, I re-run release2 smoke and/or planning UAT against the running Docker stack and record results. Failures that need live LLM or live Odoo are documented, not invented green.

**Why this priority**: Spec 021 converge left live re-runs as ops follow-ups; Sprint 3 closes the loop where the stack is available.

**Independent Test**: Execute smoke script; attach output under `docs/qa/` dated 2026-07-11+.

**Acceptance Scenarios**:

1. **Given** docker compose services healthy, **When** `scripts/release2-smoke.ps1` runs, **Then** results are recorded (PASS count or actionable FAIL).
2. **Given** LLM optional, **When** Copilot UAT-10 is exercised, **Then** timeout/fallback behavior matches Spec 021 code path or SKIP if LLM unavailable.

---

### Edge Cases

- What happens when customer has Odoo 17 but docs recommend 19? Connector mapper aliases MUST continue to work; confirmation remains OQ-1 COM.
- How does system handle missing `.env`? Compose MUST fail loudly; runbook MUST document `cp .env.template .env` first.
- What if Arabic engineering keys PASS but native reviewer has not signed? G-R2-04 stays OPEN; do not cut `v9.1.1-r2`.
- What if SOW amounts are still placeholders? OQ-7 blocks send; engineering does not invent prices.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `deploy/star-trans/` MUST remain self-contained (compose, env template, Kong, runbook, smoke) with dry-run evidence.
- **FR-002**: `scripts/star-trans-validate.ps1` MUST produce PASS/FAIL/SKIP summary suitable for pre-UAT.
- **FR-003**: Status docs MUST reflect Sprint 2 complete, Spec 021 closed, Spec 022 active, and COM blockers OPEN.
- **FR-004**: GitHub issues for shipped Spec 021 engineering MUST be triaged; commercial #50 MUST stay OPEN.
- **FR-005**: Live smoke/UAT re-check MUST be attempted when Docker is available; results recorded under `docs/qa/`.
- **FR-006**: Seed SQL for Star Trans demo overlay (`docs/demo-data/star-trans-seed.sql`) MUST be committed and referenced from runbook as **non-production** (OQ-2 policy: `DEMO_SEED_ENABLED=false` in production).
- **FR-007**: Agents MUST NOT claim OQ-7 pricing, OQ-1 version confirm, Arabic COM sign-off, or live Odoo PH1-02 without human evidence.

### Key Entities

- **Deploy package**: `deploy/star-trans/*`
- **Validation script**: `scripts/star-trans-validate.ps1`
- **Commercial blockers**: OQ-7, OQ-1, PH1-01 SOW send, PH1-02 staging, G-R2-04
- **Tags**: `v9.2.0-planning` (applied); `v9.1.1-r2` (HOLD)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Deploy dry-run log shows compose config OK and runbook/service alignment.
- **SC-002**: Validate script runs to completion with categorized results (no crash).
- **SC-003**: PRODUCT-STATUS / OPEN-ITEMS / OQ status updated for Sprint 3 without inventing COM closures.
- **SC-004**: Spec 021 GH issues triaged; Spec 022 issues created and mapped.
- **SC-005**: At least one live smoke or validate evidence file dated this Speckit run.
- **SC-006**: Constitution v1.2.7 and feature.json point at `022-sprint3-golive`.

### Out of Scope

- Filling OQ-7 license/implementation dollar amounts
- Obtaining Arabic native QA signature
- Provisioning customer Odoo staging (PH1-02)
- Pushing `v9.1.0-r2` or inventing `v9.1.1-r2`
- Nexus Social / non-IPE products
- Wave 3 NL schedule change / supplier comms (remain deferred #43–#46)
