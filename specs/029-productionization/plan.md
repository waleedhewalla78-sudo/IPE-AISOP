# Implementation Plan: Spec 029 Productionization

**Feature**: `029-productionization` · **Constitution**: 1.4.0 → **1.4.1** (PATCH)

## Approach

Close engineering gaps from `OPEN-TOPICS-REGISTER.md` without inventing product scope or faking COM. Reuse Phase 5–7 patterns inside `dpe-svc`.

| Workstream | Location | Pattern |
|------------|----------|---------|
| Kong enterprise route | `infrastructure/docker/kong.release2.yml` (+ deploy mirror) | Clone `r2-planning-command` route shape |
| Andon DB wire | `ipe_shared/models/andon_alert.py`, `phase7/andon_persist.py`, `phase7_deep.py` | Dual-write; `get_session` like admin |
| RLS remediation | `migrations/versions/068_rls_coverage_gaps.py` | ENABLE + policy / EXISTS parent-join |
| MPS/MRP persist | `069_cdm_mps_mrp_runs.py`, `phase5/plan_persist.py` | Optional save of compute JSON |
| S&OP stage-gate | `phase7/sop_stage_gate.py` + API | In-memory scaffold + skip-to-management_review |
| QA notes | `docs/qa/SPEC029-*.md` | Honest residuals |
| Pointers | `feature.json`, `AGENTS.md`, constitution footer | Spec 029 active |

## Waves

- **8A (must)**: Kong route, Andon dual-write, RLS 068, tests, docs/pointers
- **8B (should)**: MPS/MRP 069 + helpers, stage-gate scaffold + API tests
- **8C (if healthy)**: seed MOs + star-trans-validate; else document
- **8D (notes)**: k6 p95 + Playwright flake notes

## Honesty guardrails

- COM blockers stay OPEN in PRODUCT-STATUS / converge.
- No `v9.1.1-r2` tag; never push `v9.1.0-r2`.
- Live integrations remain MOCK/STUB (PH1-02).

## Out of commit scope

Unrelated dirty tree (frontend UX, kms keys, prior test-results) — exclude from Spec 029 commits.
