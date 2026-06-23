# 01 — Service Readiness Matrix (V2 Audit)

**Generated**: 2026-06-20 | **Repository**: D:\AISOP\ipe
**Audit Rule**: DEPLOYMENT GATE = FAIL if ANY criterion fails.

## Scoring Legend

| Symbol | Meaning |
|--------|---------|
| PASS | Criterion met with evidence |
| FAIL | Criterion missing or broken |
| — | Not applicable for this service |
| WARN | Met but with documented concerns |

## Readiness Criteria

| # | Criterion | Category |
|---|-----------|----------|
| 1 | Dockerfile complete (COPY/WORKDIR/CMD) | Deployment |
| 2 | Service in docker-compose.yml | Deployment |
| 3 | Individual K8s manifest exists | Deployment |
| 4 | Helm template coverage | Deployment |
| 5 | CI pipeline job present | Deployment |
| 6 | /health endpoint | Observability |
| 7 | /ready endpoint with dependency checks | Observability |
| 8 | Structured JSON logging | Observability |
| 9 | Correlation ID middleware | Observability |
| 10 | /metrics endpoint exposed for Prometheus | Observability |
| 11 | All core imports resolve (no broken imports) | Functional |
| 12 | All routes are reachable | Functional |
| 13 | RBAC applied to write/mutating endpoints | Security |
| 14 | Port consistent across Dockerfile/compose/K8s/Helm | Deployment |
| 15 | No hardcoded secrets | Security |

## Service Matrix

| Service | F-Imp. | F-Rch. | CI | Docker | Compose | K8s | Helm | Port Consist | /health | /ready | Logger | CorrID | /metrics | RBAC | Secrets | Score | Gate |
|---------|--------|--------|----|--------|---------|-----|------|-------------|---------|--------|--------|--------|----------|------|---------|-------|------|
| **dpe-svc** | FAIL | FAIL | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | PASS | PASS | FAIL | FAIL | PASS | **10/15 (67%)** | **FAIL** |
| **mat-svc** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | PASS | PASS | FAIL | FAIL | PASS | **12/15 (80%)** | **FAIL** |
| **cap-svc** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | PASS | PASS | FAIL | PASS | PASS | **13/15 (87%)** | **FAIL** |
| **fea-svc** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | WARN | PASS | PASS | FAIL | PASS | PASS | **12/15 (80%)** | **FAIL** |
| **res-svc** | PASS | PASS | PASS | WARN | PASS | PASS | PASS | FAIL | PASS | WARN | PASS | PASS | FAIL | FAIL | PASS | **10/15 (67%)** | **FAIL** |
| **del-svc** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | WARN | PASS | PASS | FAIL | FAIL | PASS | **11/15 (73%)** | **FAIL** |
| **nlp-svc** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | WARN | PASS | PASS | FAIL | PASS | PASS | **12/15 (80%)** | **FAIL** |
| **rec-svc** | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | FAIL | PASS | WARN | PASS | PASS | FAIL | FAIL | PASS | **10/15 (67%)** | **FAIL** |
| **alert-svc** | PASS | PASS | PASS | WARN | PASS | FAIL | PASS | PASS | PASS | FAIL | PASS | PASS | FAIL | FAIL | PASS | **11/15 (73%)** | **FAIL** |
| **connector** | PASS | PASS | PASS | PASS | FAIL | FAIL | PASS | FAIL | PASS | WARN | PASS | PASS | FAIL | — | PASS | **8/14 (57%)** | **FAIL** |
| **mock-odoo-api** | PASS | — | FAIL | PASS | FAIL | FAIL | FAIL | — | WARN | FAIL | FAIL | FAIL | FAIL | — | PASS | **2/11 (18%)** | **FAIL** |

## Critical Failure Details

### ALL SERVICES fail: /metrics endpoint
**Status**: FAIL (service-wide)
**Evidence**: `setup_metrics()` is called in all service main.py files, but `/metrics` path is NEVER mounted. Prometheus cannot scrape any service.
**Impact**: No service-level metrics visible in Grafana dashboards. All 13 scrape targets in prometheus.yml will get 404.
**Blocking Deployment**: YES

### ALL SERVICES fail: Port inconsistency
**Status**: FAIL (service-wide)
**Evidence**: 3 incompatible port assignment schemes exist:
- Dockerfile EXPOSE: 8001-8009 (1-up from service index)
- docker-compose.yml: 8002-8010 (2-up from service index)  
- Helm values.yaml: 8001-8010 (mixed scheme)
**Impact**: Services fail to connect to each other in production.
**Blocking Deployment**: YES

### dpe-svc: Broken ctp.py module
**Status**: FAIL
**Evidence**: `services/dpe-svc/app/api/v1/ctp.py:7` imports `from app.core.ctp import evaluate_ctp` — module does not exist. Line 8 imports `from app.deps import get_current_tenant` — function does not exist.
**Impact**: dpe-svc will crash at startup when loading the ctp module.
**Blocking Deployment**: YES

### 5 services: No RBAC on any endpoint
**Services**: dpe-svc, mat-svc, del-svc, rec-svc, alert-svc
**Evidence**: 0 `require_roles()`/`require_any_permission()` calls across all endpoints in these services.
**Impact**: Any authenticated user can access all operations including mutations.
**Blocking Deployment**: YES

### alert-svc: No /ready endpoint
**Status**: FAIL
**Evidence**: Only `GET /health` exists. No `/ready` with DB/Kafka/Redis checks.
**Impact**: Kubernetes readiness probe will fail or use invalid endpoint.
**Blocking Deployment**: YES

### connector: Missing from docker-compose.yml
**Status**: FAIL
**Evidence**: connector service is not defined in `infrastructure/docker/docker-compose.yml`.
**Impact**: Cannot deploy the full stack locally for development/testing.
**Blocking Deployment**: YES

### rec-svc, alert-svc, connector: Missing individual K8s manifests
**Status**: FAIL
**Evidence**: No YAML files in `infrastructure/k8s/services/` for these services.
**Impact**: Cannot deploy to Kubernetes without Helm (and Helm has issues too).
**Blocking Deployment**: YES

## Warnings

| Service | Warning |
|---------|---------|
| res-svc | Dockerfile has duplicate `RUN uv sync` (line 9-11) |
| alert-svc | Dockerfile CMD missing `--no-sync` flag |
| 4 services | /ready only checks DB (no Kafka/Redis verification) |
| fea-svc | /ready Kafka check hardcoded to "ok" (not actually tested) |
| cap-svc | cap-svc has RBAC on schedule endpoints but no RBAC on analyze/simulate |
| res-svc | POST /resolution/scenarios (create) has no RBAC — only POST /approve has it |

## Final Verdict

**OVERALL GATE: FAIL — 0 of 11 services pass deployment readiness gates.**

Primary blockers:
1. No /metrics endpoints on any service (11/11 FAIL)
2. Port inconsistencies across all configuration layers (10/11 FAIL)  
3. Broken dpe-svc ctp module prevents startup
4. 5 services lack any application-level RBAC
5. 22 database tables lack RLS policies
6. 11 event topics have no creation scripts
