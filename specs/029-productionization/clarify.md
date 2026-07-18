# Clarify — Spec 029 Productionization

**Date**: 2026-07-18 · **Mode**: non-interactive (full pipeline, no approval stops)

## Clarifications resolved from OPEN-TOPICS-REGISTER + prior specs

| # | Ambiguity | Decision |
|---|-----------|----------|
| Q1 | Feature slug `029-productionization` vs `029-phase8-hardening`? | **`029-productionization`** — matches eng backlog framing; Phase 8 not an Ops Blueprint number. |
| Q2 | New constitution principle? | **No** — PATCH **1.4.1**: workflow/pointers only (Spec 029 active; Phases 6–7 marked ENG COMPLETE in map). |
| Q3 | Replace in-memory Andon or dual-write? | **Dual-write**: keep `AndonBoard` for deterministic unit tests; persist via `cdm_andon_alert` when session available. |
| Q4 | RLS on `cdm_tenant` / scenario children / skill link? | Enable RLS: tenant self-scope on `cdm_tenant`; EXISTS parent-join policies for scenario children + worker_skill_link. |
| Q5 | Full monetary leveling / tablet UI / WhatsApp? | **Out of scope** (ENG-08/09, OPS-01) — remain deferred. |
| Q6 | Fake live Odoo / Arabic / pricing? | **Forbidden** — track as COM OPEN only. |
| Q7 | k6 p95 “fix” required for Wave 1 complete? | **Notes + light fixes only**; under-load SLO remains genuine residual risk if not fully closed. |
| Q8 | Must close GH #70/#72/#110 in this run? | **Attempt when R2 healthy**; else document BLOCKED-by-stack and leave issues OPEN. |
| Q9 | Notifications channel for Andon? | Scaffold notify list already in policy; **real push channel deferred** (ENG-04 residual depth). |
| Q10 | Which Kong files? | Primary: `infrastructure/docker/kong.release2.yml`; mirror deploy/star-trans + infrastructure/kong copies if they carry planning-command. |

## Assumptions locked

- Migrations continue from head **067** → **068** (RLS) → **069** (MPS/MRP) as needed.
- No tag cut; never push `v9.1.0-r2`.
- Author for commits: `IPE Agent <ipe-agent@local>`.
