# Plan — 014 Release 2 Commercial Growth

**Feature**: `014-release2-growth`  
**Date**: 2026-07-01  
**Readiness**: 0/100 → target 92/100 post-implement  
**Tech stack**: FastAPI, PostgreSQL 16, React/Vite, httpx, existing res-svc/dpe-svc/connector  
**Deployment**: Extends `docker-compose.release1.yml` (no new mandatory services for A+B)

---

## 1. Architecture

### 1.1 Stream A — Auto-propose flow (release1-safe)

```text
Odoo sync (connector)
    → fea-svc POST /feasibility/rescore/{mo_id}
    → if score < threshold:
        res-svc POST /resolution/scenarios { mo_id }
    → cdm_resolution_scenario rows (status=proposed)
    → Resolution Center UI (existing GET /resolution/scenarios)
```

**Config:** `tenant.config.auto_propose_threshold` (default 75)

### 1.2 Stream B — Outcomes dashboard

```text
web-ui OutcomesPage
    → GET /analytics/otd-baseline
    → GET /analytics/roi-metrics
    → GET /sync/status
    → POST /analytics/otd-baseline/capture (button)
```

Optional aggregator: `GET /analytics/outcomes-summary` (dpe-svc) — Phase B2.

### 1.3 Stream C — Copilot Lite

```text
ControlTowerPage → PlannerAssistPanel
    → POST /planner-assist/query { query }
    → dpe-svc intent router (keyword + regex)
    → internal httpx to fea-svc / sync / resolution APIs
    → structured markdown response
```

Hybrid profile: passthrough to nlp-svc when `NLP_SVC_URL` set.

### 1.4 Stream D — Odoo resolution write-back

```text
res-svc POST /resolution/scenarios/{id}/approve
    → connector POST /erp/odoo/resolution-notify
    → Odoo XML-RPC mail.message on mrp.production
```

---

## 2. File touch map

| Stream | Files |
|--------|-------|
| A | `connector/app/odoo/sync_engine.py`, `res-svc/app/events/handlers.py`, `connector/tests/test_auto_propose.py` |
| B | `apps/web/.../OutcomesPage.tsx`, `CommandCenterHub.tsx`, `router.tsx`, `constants.ts`, `locales/ar.json` |
| C | `dpe-svc/app/api/v1/planner_assist.py`, `apps/web/.../PlannerAssistPanel.tsx` |
| D | `connector/app/api/v1/erp_odoo.py`, `res-svc/app/api/v1/resolution.py` |
| Demo | `scripts/run-release2-demo.ps1` |

---

## 3. Kong routes (release1)

| Route | Service | New? |
|-------|---------|------|
| `/api/v1/resolution` | res-svc | Existing |
| `/api/v1/analytics` | dpe-svc | Existing |
| `/api/v1/planner-assist` | dpe-svc | **New** |

---

## 4. Testing strategy

| Layer | Tests |
|-------|-------|
| Unit | auto-propose dedupe, intent router, res-svc handler mo_id fix |
| Integration | sync → rescore → scenarios count increase |
| E2E | `run-release2-demo.ps1` 5 checkpoints |
| Regression | `run-release1-integration-demo.ps1` 13/13 |

---

## 5. Rollout phases

| Phase | Streams | Gate |
|-------|---------|------|
| Phase 0 | Hygiene (feature.json, stale docs) | T001 |
| Phase A | Auto-propose + handler fix | T110–T112, demo A |
| Phase B | Outcomes UI | T120–T121, demo B |
| Phase C | Copilot Lite | T140–T142, demo C |
| Phase D | Odoo write-back | T150–T152, demo D |
| Closure | R2 demo + R1 regression | T160–T163 |

---

## 6. Non-goals (this plan)

- Kafka in release1 compose
- Ollama bundled in release1
- SAP connector
- Stripe/Keycloak

---

*Plan version 1.0 — `/speckit.plan`*
