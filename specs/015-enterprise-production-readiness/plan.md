# Plan — 015 Enterprise Production Readiness

**Feature**: `015-enterprise-production-readiness`  
**Date**: 2026-06-24  
**Tech stack**: Existing IPE stack (FastAPI, React, PostgreSQL 16, Kafka, Redis, Kong, Helm/K8s)

---

## 1. Architecture decisions

| Decision | Choice | Alternatives rejected |
|----------|--------|----------------------|
| Identity | Keycloak 24+ OIDC | Custom JWT only (blocks enterprise) |
| Secrets | Vault primary, AWS SM for AWS tenants | Env vars in prod |
| Orchestration | Helm → EKS | Raw manifests only |
| Observability | Prometheus + Grafana + OTel → Tempo | ELK-only |
| ERP expansion | Connector pattern (like Odoo) | Monolithic ERP adapter |
| Demo preservation | `release1` compose frozen | Merge profiles |

---

## 2. Phase implementation map

### Phase 0 — Security (weeks 1–2)

| Workstream | Touch points |
|------------|--------------|
| Keycloak | `ipe_shared/auth/keycloak.py`, `dpe-svc/auth.py`, `apps/web` login redirect |
| RS256 JWT | `ipe_shared/auth/jwt.py`, env `JWT_SIGNING_MODE=rs256` |
| Vault | `config/secrets_manager.py` — implement `HashiVaultSecretsProvider` |
| TLS | `infrastructure/kong/` TLS plugin + cert-manager docs |
| Audit middleware | `ipe_shared/middleware/audit_request.py` (new) |

### Phase 1 — K8s HA (weeks 3–8)

| Workstream | Touch points |
|------------|--------------|
| Helm completeness | `infrastructure/k8s/helm/ipe-platform/templates/services.yaml` — all 22 svcs |
| HPA | `templates/hpa.yaml` — per-service values |
| PG HA | External RDS chart values; remove single-container PG for prod |
| Graceful shutdown | `app/main.py` lifespan hooks all services |
| Circuit breaker | `ipe_shared/http/resilient_client.py` |

### Phase 2 — Observability (weeks 9–14)

| Workstream | Touch points |
|------------|--------------|
| Metrics | `ipe_shared/observability/metrics.py` — Prometheus instrumentator |
| Logging | structlog JSON formatter in shared middleware |
| Tracing | OTel already stubbed — enable `IPE_OTEL_TRACING_ENABLED` |
| Dashboards | `infrastructure/monitoring/grafana/dashboards/` |
| Alerts | `infrastructure/monitoring/prometheus/alerts.yml` |

### Phase 3 — Scale & compliance (weeks 15–22)

| Workstream | Touch points |
|------------|--------------|
| GDPR | Harden `dpe-svc/dsar.py`, retention jobs |
| SAP connector | `services/connector/app/erp/sap_adapter.py` (new) |
| Load tests | `tests/performance/k6/enterprise-500vu.js` |
| API versioning | Kong routes `/api/v2/` prefix pattern |

### Phase 4 — GTM (weeks 23–36)

| Workstream | Touch points |
|------------|--------------|
| Tenant API | `dpe-svc/admin.py` provision endpoints |
| Stripe live | `stripe_billing.py` + webhook handler |
| Dev portal | Static site or ReadMe sync from OpenAPI aggregate |
| SDK | `packages/ipe-sdk-python`, `packages/ipe-sdk-js` |

---

## 3. Testing strategy

| Layer | Gate |
|-------|------|
| Unit | Vault provider, JWT RS256, audit middleware |
| Integration | Keycloak login flow, GDPR export |
| E2E | R1 13/13 + R2 5/5 after each phase |
| Load | k6 500 VU staging |
| Chaos | C1–C6 on K8s staging weekly |

---

## 4. Rollout milestones

| Milestone | Tag | Gate |
|-----------|-----|------|
| E0 Security | `v10.0.0-e0` | Keycloak login + vault read |
| E1 K8s | `v10.0.0-e1` | Helm staging all healthy |
| E2 Observability | `v10.0.0-e2` | Grafana + alerts firing |
| E3 Compliance | `v10.0.0-e3` | GDPR export + k6 pass |
| E4 GTM | `v10.0.0-e4` | Stripe sandbox invoice |

---

*Plan version 1.0 — `/speckit.plan`*
