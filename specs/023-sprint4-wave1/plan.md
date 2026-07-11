# Implementation Plan — Spec 023 Sprint 4 Wave 1

**Branch**: `023-sprint4-wave1` (work on `master` acceptable if repo convention)  
**Date**: 2026-07-11  
**Constitution**: 1.2.8  
**Spec**: `ipe/specs/023-sprint4-wave1/spec.md`  
**Checklist**: `ipe/tasks/sprint4-todo.md`

---

## Summary

Deliver Spec 017 Wave 1 remaining engineering: **Odoo Config v2** (encrypted ERP connection management in connector + Admin UI) and **OTD Analytics** polish (dpe-svc aggregator/API + dashboard/i18n/nav). Update program docs. Leave commercial blockers OPEN. Absorb Spec 022 residuals #70–#72 best-effort.

---

## Technical Context

| Dimension | Choice |
|-----------|--------|
| **Language** | Python 3.11 (connector, dpe-svc, shared); TypeScript/React (web-ui) |
| **API** | FastAPI routers; Pydantic v2 schemas; `APIResponse` envelope |
| **ORM / DB** | SQLAlchemy 2.0 async; Alembic migration **050**; RLS policies; existing **039** OTD snapshots |
| **Crypto** | `cryptography.Fernet` via `IPE_ENCRYPTION_KEY` |
| **Auth** | JWT + `require_roles(["admin"])` + `tenant_ctx` |
| **ERP** | Odoo XML-RPC test (mocked in unit tests) |
| **Frontend** | Vite React; lazy routes; i18n EN/AR JSON |
| **Gateway** | Kong paths for `/api/v1/erp/connections` and OTD (reuse connector/dpe upstreams) |
| **Tests** | pytest + httpx ASGI; Vitest optional for UI |
| **Target** | R1/R2 docker-compose; Windows ops scripts |

---

## Constitution Check

| Principle | Plan compliance |
|-----------|-----------------|
| I RLS | 050 enables RLS on both new tables |
| II Auth | Mutations admin-only; health unchanged |
| III Tests | New/extended pytest modules required |
| V Layering | `api/v1`, `core`, `schemas`, shared models |
| VI Obs | Connection log + last_test_* fields |
| VII Honesty | HUMAN tasks never auto-closed |
| Secrets | No plaintext passwords in API/logs/git |

**Gate:** PASS

---

## Project Structure (touched)

```text
ipe/
├── migrations/versions/050_erp_connections.py
├── services/shared/ipe_shared/models/erp_connection.py
├── services/connector/app/
│   ├── api/v1/erp_connections.py
│   ├── core/erp_connections_service.py
│   ├── core/password_crypto.py
│   ├── schemas/erp_connections.py
│   └── tests/test_erp_connections.py
├── services/dpe-svc/app/core/otd_aggregator.py
├── services/dpe-svc/app/api/v1/otd_analytics.py
├── services/dpe-svc/tests/test_otd_analytics.py
├── apps/web/src/features/odoo-config/
├── apps/web/src/features/otd-analytics/
├── apps/web/src/locales/{en,ar}.json
├── .env.template / .env.example / deploy/star-trans/.env.template
├── tasks/sprint4-todo.md
├── PRODUCT-STATUS.md / CHANGELOG.md
├── specs/017-first-release-plan/spec.md
└── specs/023-sprint4-wave1/
```

---

## Implementation Approach

### Phase A — Odoo Config v2 (W1-03/04/05)
1. Land migration 050 + shared models + Fernet module.
2. Complete service + REST (CRUD, test, activate, sync-now, logs).
3. Register router; add cryptography dependency if missing.
4. Frontend page + API client + i18n + Admin/Platform routes.
5. pytest green.

### Phase B — OTD Analytics (W1-06/07/08)
1. Confirm migration 039; finish `OTDAggregator`.
2. Extend `otd_analytics` API; tests.
3. Dashboard polish + nav + i18n.

### Phase C — Closure
1. CHANGELOG + PRODUCT-STATUS + Spec 017 status rows.
2. Mark `sprint4-todo.md` items done.
3. Commit with author `IPE Agent <ipe-agent@local>`; push per checklist C5.
4. Best-effort #70–#72.

### Phase D — Human / COM (document only)
OQ-7, OQ-1, PH1-02, G-R2-04 — OPEN.

---

## Data Model (summary)

See `data-model.md`. Key: `cdm_erp_connection.password_encrypted` (Text, Fernet); partial unique `(tenant_id, erp_type) WHERE is_active`.

---

## Risks

| Risk | Mitigation |
|------|------------|
| Missing Fernet key in deploy | Document in templates + validate script note |
| Parallel agent file races | Prefer completing existing WIP paths |
| Live Odoo test | Mock only in CI; SKIP live |

---

## Complexity Tracking

Medium feature (2 services + UI + migration). No new microservice.
