# Hybrid Stack Gap Analysis — Release 1 → 32/32 Demo

**Date:** 2026-06-30  
**Purpose:** Readiness assessment for moving from 8-service Release 1 to 22+ service hybrid stack.  
**Do not start hybrid stack from this document alone** — use `scripts/prepare-startrans-demo-hybrid.ps1`.

---

## Current state

| Profile | Services | Integration demo | Full demo |
|---------|----------|------------------|-----------|
| Release 1 | 9 app + db/redis/kong | **13/13 PASS** | **13/32 PASS** |
| Hybrid | 22+ app + kafka/ollama | Not run (this sprint) | Target **32/32** |

---

## Release 1 stack (running)

| Service | Port | Kong route | Role |
|---------|------|------------|------|
| db | 5433 | — | PostgreSQL |
| redis | 6380 | — | Cache |
| kong | 8000 | gateway | API gateway |
| dpe-svc | 8020 | auth, health, dashboard, analytics, demand, admin | Platform core |
| fea-svc | 8004 | feasibility | Control Tower scoring |
| cap-svc | 8003 | capacity | OR-Tools scheduling |
| res-svc | 8005 | resolution | Resolution scenarios |
| connector | 8016 | sync, erp/odoo | Odoo 19 sync |
| web-ui | 8082 | — | React UI (release1 profile) |

---

## Services required for 32/32 (missing from Release 1)

| Service | Port | Needed for (checkpoints) | Docker image built | Kong (hybrid) | Star Trans seed | Known issues |
|---------|------|--------------------------|-------------------|---------------|-----------------|--------------|
| mat-svc | 8002 | 14 Inventory summary | Yes (`docker-mat-svc`) | Yes | Base seed | — |
| del-svc | 8006 | 5 Shop Floor | Yes | Yes | Work orders in demo seed | — |
| rec-svc | 8008 | 12 AI Trust | Yes | Yes | Trust scores seed | — |
| nlp-svc | 8007 | 10–11, 30 Copilot | Yes | Yes | Copilot intents | Requires Ollama |
| ollama | 11434 | Copilot LLM | Profile `ollama` | — | Model `llama3.2:3b` | ~4GB RAM |
| alert-svc | 8010 | 20 War Room / IoT | Yes | Yes | Alert feed partial via dpe | — |
| demand-svc | 8040 | 21–22 Demand forecast/sense | Yes | Yes | Demand lines seeded | — |
| scenario-svc | 8050 | 23–24 Scenario sandbox | Yes | Yes | — | — |
| supply-svc | 8060 | 25 Supply network | Yes | Yes | Plants in overlay SQL | — |
| order-svc | 8070 | 26 Customer orders | Yes | Yes | — | — |
| equipment-svc | 8061 | 27 Equipment fleet | Yes | Yes | Work centers | — |
| material-svc | 8090 | 28 Design AI catalog | Yes | Yes | Products | — |
| procurement-svc | 8100 | 29 Procurement spend | Yes | Yes | Suppliers | — |
| sustain-svc | 8012 | 31 Sustainability | Yes | Yes | — | — |
| quality-svc | 8013 | 32 Quality intelligence | Yes | Yes | — | — |
| scn-svc | 8014 | 6 SCN Portal | Yes | Yes | Suppliers seeded | — |
| ml-svc | 8011 | Schedule ML duration (optional) | Not in local images list | **Missing from kong.yml** | — | P1 audit item; cap-svc degrades gracefully |
| network-svc | 8015 | Digital twin (extended) | Yes | Yes | Plants | — |
| kafka | 9092 | Event bus (res-svc, cap-svc) | Running (full compose) | — | — | Required for event-driven features |

---

## prepare-startrans-demo-hybrid.ps1 summary

1. Starts `docker-compose.yml` + `docker-compose.demo.yml` + Ollama profile
2. Brings up: db, redis, ollama, dpe-svc, mat-svc, cap-svc, fea-svc, res-svc, del-svc, nlp-svc, connector, alert-svc, demand-svc, scenario-svc, supply-svc, order-svc, equipment-svc, material-svc, procurement-svc, sustain-svc, quality-svc, kong
3. Runs `seed-startrans-demo.ps1`
4. Configures Odoo credentials and optional live sync
5. Validates with `run-full-demo.ps1 -Profile startrans`

---

## run-full-demo.ps1 expectations

- **Base URL:** `http://localhost:8000` (Kong)
- **Profile startrans:** MO-ST prefix, transformer product names
- **32 checkpoints** across Planning, Analytics, Copilot, v6/v7/v8 modules
- **Release 1 baseline (2026-06-30):** 13 PASS, 19 SKIP (hybrid-only), 0 bug failures

---

## Recommended next sprint actions

1. Run `prepare-startrans-demo-hybrid.ps1` on demo laptop (16GB+ RAM)
2. Add `ml-svc` route to `kong.yml` if ML duration predictions required
3. Re-run `run-full-demo.ps1 -Profile startrans` → target 32/32
4. UAT sign-off (T071) and tag `v9.0.0-r1` (T073)

---

## Infrastructure not required for demo (optional)

| Service | Notes |
|---------|-------|
| keycloak | Enterprise SSO — Phase 2 |
| airflow | Batch pipelines |
| otel-collector / jaeger | Tracing (disabled in release1) |
| mlflow | ML experiment tracking |
