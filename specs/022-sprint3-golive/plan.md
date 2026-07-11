# Implementation Plan — Spec 022 Sprint 3 Go-Live

**Branch**: `022-sprint3-golive`  
**Date**: 2026-07-11  
**Constitution**: 1.2.7  
**Spec**: `ipe/specs/022-sprint3-golive/spec.md`

---

## Summary

Close the engineering go-live readiness loop for Star Trans R1 after Sprint 2 GTM packaging: harden/verify `deploy/star-trans/`, run and record `star-trans-validate.ps1` + smoke where Docker allows, refresh program status docs for honesty, triage Spec 021 GitHub issues, commit seed SQL with non-prod policy, and leave commercial blockers OPEN.

This is primarily **ops/docs/hygiene + verification**, not a new microservice feature.

---

## Technical Context

| Dimension | Choice |
|-----------|--------|
| **Language** | PowerShell 5.1+ validation scripts; Markdown docs; optional SQL seed |
| **Runtime** | Docker Compose (dev R2 stack and/or `deploy/star-trans`) |
| **Gateway** | Kong (`kong.star-trans.yml` for customer; release2 kong for dev smoke) |
| **Auth** | Local JWT for R1 validate (`AUTH_MODE=local`) |
| **ERP** | Mock Odoo for eng evidence; live Odoo = PH1-02 COM |
| **DB** | PostgreSQL via compose; migrations head ~049 on full stack; R1 package may use subset |
| **Frontend** | `VITE_RELEASE_PROFILE=release1` for customer package |
| **Tests** | Existing pytest/playwright; no new product APIs required |
| **Target platform** | Windows ops + Ubuntu customer VM (cross-platform scripts) |

---

## Constitution Check

| Principle | Plan compliance |
|-----------|-----------------|
| I RLS | Seed SQL is demo overlay only; production `DEMO_SEED_ENABLED=false` (OQ-2) |
| II Auth | Validate uses authenticated calls; health probes only for /health |
| III Tests | Prefer execute existing suites; record evidence |
| VII Honesty | COM blockers documented, not closed |
| VIII Gates | Script output is evidence; no invented PASS |

**Gate:** PASS for planning — no principle dilution.

---

## Project Structure (touched)

```text
ipe/
├── deploy/star-trans/          # compose, env, kong, runbook, smoke
├── docs/
│   ├── customer/star-trans/    # SOW-STATUS refresh
│   ├── project/                # OQ status (read; COM edits only if factual)
│   ├── qa/                     # dry-run + validate/smoke evidence
│   └── demo-data/              # star-trans-seed.sql
├── scripts/star-trans-validate.ps1
├── PRODUCT-STATUS.md
├── specs/018-phase2-release2/OPEN-ITEMS-PROJECT.md
├── specs/022-sprint3-golive/   # Speckit artifacts
└── .specify/memory/constitution.md
```

**Out of structure:** `nexus-social/`, root orphan `services/`.

---

## Implementation Approach

### Phase 1 — Deploy package integrity
1. Re-validate `docker compose -f deploy/star-trans/docker-compose.yml config` with temp `.env`.
2. Align `DEPLOY-RUNBOOK.md` / `SMOKE-TEST.md` with compose (already partially done).
3. Finalize `docs/qa/DEPLOYMENT-DRYRUN-LOG.md`.

### Phase 2 — Live validation evidence
1. Run `scripts/star-trans-validate.ps1` against running stack (adjust BaseUrl if needed).
2. Attempt `scripts/release2-smoke.ps1` if applicable; record results.
3. Document SKIP for live Odoo / LLM as needed.

### Phase 3 — Status honesty + GH hygiene
1. Update PRODUCT-STATUS, OPEN-ITEMS, SOW-STATUS (Odoo dual-support wording).
2. Close/comment Spec 021 issues #52–#55; refresh #50.
3. Map Spec 022 tasks → GitHub issues.

### Phase 4 — Seed + commit durable artifacts
1. Ensure `star-trans-seed.sql` referenced as non-prod.
2. Commit Speckit artifacts + evidence (no secrets).

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Customer images missing for full compose up | Dry-run config + runbook; document image build path |
| Validate script fails on port mismatch | Parameterize BaseUrl; record actual ports from docker ps |
| Accidental COM closure | Checklist FR-007; leave #50 open |
| Duplicate GH issues | Dedup by `\bT\d{3}\b` / prior titles before create |

---

## Complexity Tracking

| Item | Why needed |
|------|------------|
| Two compose profiles (star-trans vs release2) | Customer package ≠ full R2 demo stack |
| Dual Odoo version support | OQ-1 unresolved |

---

## Success Metrics

- Dry-run + validate evidence files present
- Status docs match reality
- GH triage done
- COM blockers still OPEN in docs and #50
