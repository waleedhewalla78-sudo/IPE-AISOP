# Clarifications: Release Stabilization & Deployment Gates

**Feature**: `002-release-stabilization-gates`  
**Date**: 2026-06-22  
**Status**: Resolved (re-validated `/speckit.clarify` 2026-06-22)  
**Input**: [spec.md](./spec.md), live validation, End User Guide v1.0.0

---

## Purpose

This document records ambiguities discovered during stabilization and the **binding decisions** applied to implementation. Each item maps to plan/tasks execution.

---

## C1 — Canonical Readiness Score

| Option | Score | Rationale |
|--------|-------|-----------|
| A. Audit baseline | 74/100 | Live validation before fixes |
| B. Post–Gate 1 engineering | 78/100 | Tests green, stack not proven |
| **C. Post–Gate 2 target (chosen)** | **85/100** | E2E + stack verified; handover threshold per audit |
| D. Projection table | 99/100 | Aspirational; not evidenced |

**Decision**: Publish **85/100** in `READINESS.md` after Gate 2 passes. Supersede 74, 87, 90, 99 with explicit provenance. Gate 3 stretch target remains ≥90/100 (ops hardening deferred).

---

## C2 — Service Count

| Source | Count |
|--------|-------|
| spec.md line 21 | 14 app services |
| spec.md line 678 | 15 |
| quality-checklists | 16 |

**Decision**: **14 application microservices + connector** (15 runnable Python packages). ML-svc, alert-svc, etc. are included in the 14; `connector` is integration layer, not counted as planning-domain service in user-facing docs.

---

## C3 — Test Count Authority

| Source | Count |
|--------|-------|
| spec.md | 897 / 700+ / 290+ |
| Gate 1 collect-only | ~700+ functions (excl. `.venv`) |

**Decision**: Use **700+ automated tests** in all reconciled docs, sourced from Gate 1 evidence `evidence/gate-1/README.md`. Do not cite 897 until re-counted in CI.

---

## C4 — Docker Database Environment Variable

**Ambiguity**: `docker-compose.yml` sets `DATABASE_URL`; all service `Settings` use `env_prefix="IPE_"`, so apps read `IPE_DATABASE_URL` and default to `localhost:5432/ipe_dev`.

**Symptom**: Health endpoints pass (no DB); all DB-backed API routes return HTTP 500 (`ConnectionRefusedError` to localhost inside container).

**Decision**: Set `IPE_DATABASE_URL`, `IPE_DATABASE_URL_SYNC`, `IPE_KAFKA_BOOTSTRAP_SERVERS`, and `IPE_REDIS_URL` in `infrastructure/docker/ipe-common.env`. Disable OTEL when collector absent (`IPE_OTEL_TRACING_ENABLED=false`). Keep compose `DATABASE_URL` / `KAFKA_BOOTSTRAP_SERVERS` for migrate/init containers.

---

## C5 — PostgreSQL Host Port (Windows Dev)

**Ambiguity**: Local Postgres may occupy 5432.

**Decision**: Map Docker Postgres **5433:5432** on host. E2E and seed scripts default to `127.0.0.1:5433`. In-container services use `db:5432`.

---

## C6 — Frontend Routes vs End User Guide

| Guide URL | App Route | Decision |
|-----------|-----------|----------|
| `/resolution` | `/resolution`, `/resolution-center` | Register **both** aliases |
| `/copilot` | missing from router | Add `CopilotPanel` at `/copilot` |
| `localhost:8082` login | Kong/Vite dev proxy | Document **8082** for UI; API via Kong **8000** or service ports |

**Decision**: Router and `docs/END-USER-GUIDE.md` aligned; sidebar `ROUTES.RESOLUTION_CENTER` kept as `/resolution-center` with redirect alias.

---

## C7 — Keycloak / C-007

**Ambiguity**: Tasks mark Phase C complete; C-007 Keycloak live IdP blocked.

**Decision**: **BLOCKED** everywhere. Never mark COMPLETE. Document waiver in READINESS.md and Gate 3 residual risks.

---

## C8 — E2E Pass Criteria

| Suite | Prior | Target | Notes |
|-------|-------|--------|-------|
| `test_sprint2_e2e.py` | 3/26 | ≥15 executable pass | 7 skipped acceptable (optional endpoints) |
| `test_phase5_6_e2e.py` | 13/16 | 16/16 | Cost accounting blocked by C4 |

**Decision**: Gate 2 PASS requires fixing C4 first, then re-run both suites.

---

## C9 — Git / Tag Scope (US5)

**Ambiguity**: Large uncommitted delta; user rule says commit only when asked.

**Decision**: Document commit plan in tasks T049–T053; **do not auto-commit** unless user explicitly requests. Tag `v1.0.0-rc1` blocked until Gate 2 green + user approval.

---

## C10 — Out of Scope (Confirmed)

No change from spec FR-013: Stripe billing, mobile app, WCAG audit, feature store, live SAP/D365, Keycloak enterprise IdP.

---

## C11 — Product Login & Dashboard APIs

**Ambiguity**: Frontend calls `/api/v1/auth/login`, `/api/v1/auth/me`, and `/api/v1/dashboard/*` but no backend routes existed; login always failed.

**Decision**: Implement auth + dashboard in `dpe-svc`; register Kong routes in `infrastructure/kong/kong.yml`. Dev passwords `demo` and `admin` for seeded users when `IPE_ENVIRONMENT=development`.

---

## C12 — Ready-to-Use UI Shell

**Ambiguity**: Routes existed without login guard, MainLayout, or full sidebar; Vite on port 3000 vs End User Guide port 8082.

**Decision**: Protected routes + `MainLayout` + full nav; Vite **8082**; `scripts/start-product.ps1` + `GETTING-STARTED.md`.

---

## C13 — E2E Prerequisites

**Ambiguity**: Integration E2E fail with `ReadTimeout` when Docker stack is down or Kong hung.

**Decision**: Gate 2 PASS requires warm stack (`docker compose up -d`); document in quickstart. Product auth validated via `dpe-svc/tests/test_auth.py` (4 tests) without live stack.

---

## Traceability

| Clarification | Tasks | Contract |
|---------------|-------|----------|
| C1 | T036, T042 | gate-3-release |
| C4 | T025–T030 | gate-2-operations |
| C6 | T035+, END-USER-GUIDE | — |
| C7 | T037, T046 | gate-3-release |
| C9 | T048–T053 | — |
| C11 | T059 | gate-2-operations |
| C12 | T060–T061 | — |
| C13 | T062 | gate-2-operations |

**Next**: [analysis.md](./analysis.md) → implementation per [tasks.md](./tasks.md).
