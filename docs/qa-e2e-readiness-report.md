# IPE v7.0.0 — Comprehensive E2E QA & Production Readiness Report

**Date:** 2026-06-27  
**Engineer:** QA validation cycle (automated + integration)  
**Environment:** Local demo stack (`docker-compose.yml` + `docker-compose.demo.yml`)  
**Web UI:** http://localhost:8082  
**API Gateway:** http://localhost:8000  
**Demo tenant:** `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11`  
**Credentials:** `Ahmed@nour` / `admin` · `admin@demo.com` / `demo`

---

## Executive Summary

| Area | Result | Notes |
|------|--------|-------|
| Full demo workflow (20 checkpoints) | **20/20 PASS** | `docs/qa-e2e-demo-report.txt` |
| Chaos engineering (C1–C6) | **6/6 PASS** | Post-chaos demo **20/20** |
| Service health (7 core services) | **7/7 HTTP 200** | Kong, dpe, mat, cap, fea, nlp, alert |
| Product smoke check | **PASS** | `scripts/check-product.ps1` |
| Data consistency (mat ↔ copilot) | **PASS** | FG totals and SKU quantities match |
| Copilot LLM (OpenRouter) | **PASS** | Real API via `google/gemini-2.5-flash` |
| **Staging / UAT readiness** | **READY** | Full demo cycle validated |
| **Production readiness** | **NOT READY** | See §7 blockers (Keycloak, billing, secrets, RLS) |

---

## 1. Workflows Tested

### 1.1 Authentication & Tenant Context

| Step | Endpoint / UI | Result |
|------|---------------|--------|
| Login (primary demo user) | `POST /api/v1/auth/login` | PASS — JWT issued |
| Login (alternate demo user) | `POST /api/v1/auth/login` | PASS — `admin@demo.com` |
| Tenant scoping | `X-Tenant-ID` + JWT | PASS — 10 MOs in queue for demo tenant |
| Web UI login page | http://localhost:8082/login | PASS — HTTP 200 |

### 1.2 Planning & Operations (Checkpoints 1–6)

| # | Module | API Validated | UI Route | Result |
|---|--------|---------------|----------|--------|
| 1 | Control Tower — feasibility queue | `GET /api/v1/feasibility/queue` | `/control-tower` | PASS — 10 MOs, worst score 45.0 |
| 2 | Control Tower — KPIs | `GET /api/v1/feasibility/kpis` | `/control-tower` | PASS — avg 74.9, 1 at risk |
| 3 | Resolution Center | `GET /api/v1/resolution/scenarios` | `/resolution-center` | PASS — 16 scenarios |
| 4 | Schedule (OR-Tools) | `POST /api/v1/capacity/schedule` | `/schedule` | PASS — 7 operations scheduled |
| 5 | Shop Floor | `GET /api/v1/shop-floor/items` | `/shop-floor` | PASS — 6 active work orders |
| 6 | SCN Portal | `GET /api/v1/supply-chain/suppliers` | `/scn-portal` | PASS — 3 supplier scorecards |

### 1.3 Analytics & Intelligence (Checkpoints 7–14)

| # | Module | API Validated | Result |
|---|--------|---------------|--------|
| 7 | Executive — delays | `GET /api/v1/executive/delay-breakdown` | PASS — 6 categories |
| 8 | Executive — OTD | `GET /api/v1/executive/otd-summary` | PASS — 2 trend points |
| 9 | War Room / Alerts | `GET /api/v1/dashboard/alerts` | PASS — 8 active alerts |
| 10 | Copilot — FG stock | `POST /api/v1/copilot/query` | PASS — `material_status`, Widget A/Gadget B |
| 11 | Copilot — at-risk | `POST /api/v1/copilot/query` | PASS — `feasibility_check` |
| 12 | AI Trust | `GET /api/v1/ai-trust/scores` | PASS |
| 13 | Admin config | `GET /api/v1/admin/tenant-config` | PASS — autonomy: shadow |
| 14 | Inventory summary | `GET /api/v1/material/inventory-summary` | PASS — 4 FG products |

### 1.4 V6 Advanced Features (Checkpoints 15–20)

| # | Feature | API | Result |
|---|---------|-----|--------|
| 15 | Schedule persist + approve | `POST /api/v1/capacity/approve` | PASS — 2 MOs persisted |
| 17 | V6-R1 Activity-based planning | margin/priority APIs | PASS — margin score 56.16 |
| 18 | V6-R2 Tariff shock | tariff shock + substitute draft | PASS — 6 affected, 6 drafts |
| 19 | V6-R3 Visual CPM | cascade API | PASS — 5–14 ms, 3 critical ops |
| 20 | V6-R4/R5 Maintenance + Chaos | maintenance + war-room APIs | PASS — 3 chaos categories, 3 recovery options |

### 1.5 End-to-End APS Pipeline (implicit in demo)

```
Demand/MO seed → Feasibility scoring → Capacity schedule → Resolution scenarios
     → Planner approve → CDM persist → (ERP event deferred when Kafka paused)
```

All stages exercised via demo script checkpoints 1–5, 15, and chaos C3/C4.

---

## 2. Integration Validation

| Integration | Type | Status | Evidence |
|-------------|------|--------|----------|
| Kong → microservices | Internal | **PASS** | All routed demo APIs return 200 |
| PostgreSQL (multi-tenant) | Data store | **PASS** | 10 MOs, 4 FG SKUs, 6 WOs from DB |
| Redis | Cache / idempotency | **PASS** | Stack healthy, no timeout errors |
| Kafka | Event mesh | **PASS** | C3/C4 validate publish + defer behavior |
| mat-svc ↔ nlp-svc (Copilot) | Service aggregation | **PASS** | Inventory data in copilot responses |
| fea-svc ↔ cap-svc | Scheduling pipeline | **PASS** | Queue + schedule checkpoints |
| alert-svc ↔ war-room | Alert feed | **PASS** | 8 alerts in dashboard |
| OpenRouter LLM | External API | **PASS** | Live chat completions |
| ERP connector | External | **PARTIAL** | Service running; live Odoo not in demo overlay |
| Stripe billing | External | **MOCK** | In-memory mock (see §4) |
| Keycloak SSO | External | **DEFERRED** | ADR-001; local JWT auth only |
| Weather API | External | **MOCK fallback** | Deterministic factor without API key |

---

## 3. Data Consistency Validation

| Check | Source A | Source B | Expected | Actual | Status |
|-------|----------|----------|----------|--------|--------|
| FG product count | `inventory-summary` | Demo checkpoint 14 | 4 | 4 (`total_products`) | PASS |
| FG total on-hand | mat-svc sum | Copilot query | Match | 2248 units both | PASS |
| Widget A quantity | mat-svc | Copilot | 1130 | Copilot cites 1130 | PASS |
| Feasibility queue size | fea-svc | Control Tower UI | 10 | 10 MOs | PASS |
| Shop floor WOs | shop-floor API | Demo checkpoint 5 | ≥1 | 6 WOs | PASS |
| Active alerts | dashboard/alerts | War Room | ≥1 | 8 alerts | PASS |

**Note:** Copilot responses are LLM-synthesized from structured JSON context; numeric fields were verified to match mat-svc source data for Widget A and total FG on-hand.

---

## 4. Mock-to-Real Transition Audit

| Component | Previous State | Current State | Action Taken | Re-validated |
|-----------|----------------|---------------|--------------|--------------|
| **Copilot LLM** | OpenRouter + Ollama | **Ollama host + OpenRouter fallback** | `docker-compose.ollama-host.yml`; Kong 300s timeout | YES |
| **Ollama local LLM** | Disabled in demo | **Host Ollama integrated** | `IPE_LLM_PRIMARY_PROVIDER=ollama` | YES — query + chat verified |
| **del-svc ANTHROPIC mock** | Dead `mock_anthropic_key` env | Removed | Cleaned `docker-compose.yml` | YES — del-svc health 200 |
| **Stripe billing** | `StripeMockService` | Still mock | **Intentional** — no Stripe account in demo | Demo billing endpoints work |
| **Weather signals** | `_mock_factor()` without key | Still mock fallback | **Acceptable** — NWS API optional | Capacity scheduling unaffected |
| **mock-odoo-api** | Test compose only | Not in demo stack | Used only in `docker-compose.test.yml` | ERP path via connector service |
| **Keycloak IdP** | Placeholder config | Not deployed | **Deferred** ADR-001 | Local JWT auth validated |
| **rule_based_atp** | N/A — not a mock | Production algorithm | Deterministic ATP (C-01 fix) | YES — checkpoint via material APIs |

### Mocks intentionally retained (production blockers)

1. **Stripe** — requires live Stripe account + webhook secrets  
2. **Keycloak/SAML** — requires enterprise IdP (Azure AD/Okta)  
3. **SAP/D365 connectors** — scaffolding only; needs customer ERP credentials  
4. **Weather API** — optional; uses deterministic fallback without `WEATHER_API_KEY`

---

## 5. Chaos Engineering Results

Executed via `scripts/run-chaos-scenarios.ps1` on 2026-06-27.

| Scenario | Description | Result |
|----------|-------------|--------|
| **C1** | Kill nlp-svc during non-NLP calls | PASS — feasibility, schedule, material OK |
| **C2** | Kill alert-svc during schedule | PASS — schedule HTTP 200 |
| **C3** | Kafka pause during approve | PASS — CDM persist, ERP event deferred |
| **C4** | Kafka pause 60s + schedule drain | PASS — 3× schedule 200 during outage |
| **C5** | PG connection count under load | PASS — within limits |
| **C6** | Full demo regression post-chaos | PASS — **20/20** |

Evidence: `docs/chaos/`, `docs/demo-run-report-post-chaos.txt`

---

## 6. Errors Found & Resolution

| ID | Error | Root Cause | Fix | Re-test |
|----|-------|------------|-----|---------|
| E1 | Copilot 503 `LLM_UNAVAILABLE` | No LLM configured; wrong env vars; invalid model slug | OpenRouter provider + `IPE_*` env + `google/gemini-2.5-flash` | PASS (prior session + this cycle) |
| E2 | Ollama DNS in fallback chain | `OLLAMA_ENDPOINT_URL` without `IPE_` prefix; empty URL still attempted | `IPE_OLLAMA_ENDPOINT_URL=""`; skip unconfigured providers | PASS |
| E3 | Intent classify fails on "hi" | LLM error propagated before fallback | Catch `LLMUnavailableError` → `general` intent | PASS |
| E4 | del-svc spurious `mock_anthropic_key` | Copy-paste in compose | Removed dead env var | PASS |
| E5 | CopilotPanel missing tenant header | Raw fetch without JWT tenant extraction | Added `X-Tenant-ID` from JWT payload | PASS |
| E6 | Kong Copilot timeout on Ollama | Default ~60s upstream limit | 300s read/write on nlp-svc | PASS |
| E7 | Tool chat ReadTimeout | 120s Ollama client timeout | Increased to 300s | PASS |

**No new failures** detected during QA cycles after Copilot + Ollama fixes.

---

## 7. Production Readiness Gate

### Ready for next phase: **Staging / UAT** ✅

The system is suitable for:
- Client demo walkthroughs  
- Human UAT (`docs/FULL-DEMO-GUIDE.md`)  
- Staging deployment with demo seed data  
- Integration testing with mock Odoo (`docker-compose.test.yml`)

### Not ready for production ❌

| Blocker | Severity | Reference |
|---------|----------|-----------|
| Keycloak / enterprise SSO | P0 | ADR-001, FR-P-13 |
| JWT secret is dev placeholder | P0 | `ipe-common.env` |
| Stripe live billing | P1 | `stripe_mock.py` |
| Legacy RLS gaps (22 tables) | P1 | ADR-002 |
| SAP/D365 live connectors | P2 | Connector scaffolding only |
| Non-root containers | P2 | POST-C4 backlog |

---

## 8. Test Artifacts

| Artifact | Path |
|----------|------|
| This report | `docs/qa-e2e-readiness-report.md` |
| Demo run (this cycle) | `docs/qa-e2e-demo-report.txt` |
| Demo run (P11 baseline) | `docs/final-regression-demo.txt` |
| Post-chaos demo | `docs/demo-run-report-post-chaos.txt` |
| Chaos evidence | `docs/chaos/C1.md` … `C6.md` |
| Coverage report | `docs/coverage-report-v7.md` |
| Release tag | `v7.0.0` |

---

## 9. Recommendations Before Staging Deploy

1. **Rotate OpenRouter API key** — key was exposed in chat; update `infrastructure/docker/.env`  
2. **Set production JWT secret** via secrets manager (`docker-compose.secrets.yml`)  
3. **Run human UAT** — 20 scenarios in demo guide with evidence screenshots  
4. **Enable monitoring overlay** — `scripts/run-monitoring-stack.ps1` for Grafana/Loki  
5. **Plan Keycloak cutover** — ADR-001 before production IdP requirement  
6. **Document accepted mocks** — Stripe, weather fallback, test-only mock-odoo-api

---

## 10. Final Verdict

**The IPE v7.0.0 demo stack passes comprehensive E2E validation:** 20/20 functional checkpoints, 6/6 chaos scenarios, cross-service data consistency, and live Copilot LLM integration. Mock elements required for demo (Stripe, weather fallback, local auth) are documented and do not block staging/UAT.

**Proceed to staging/UAT.** Production release requires closing P0/P1 blockers in §7.

---

*Generated by automated QA cycle — 2026-06-27T00:36–00:40 local time.*
