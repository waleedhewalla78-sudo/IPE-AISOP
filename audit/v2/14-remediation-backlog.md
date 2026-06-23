# 14 — Remediation Backlog (V2 Audit)

**Generated**: 2026-06-20 | **Priority**: Risk × Business Impact × Implementation Effort

## Priority Legend

| Priority | Description | Deployment Blocker |
|----------|-------------|-------------------|
| P0-CRITICAL | Must fix before ANY deployment | YES |
| P1-HIGH | Must fix before production | YES |
| P2-MEDIUM | Fix within 2 releases | No |
| P3-LOW | Fix opportunistically | No |

---

## P0-CRITICAL (5 items — all deployment blockers)

### R-001: Add RLS Policies to 22 Tables
- **Root Cause**: Migration 001 uses a dynamic DO $$ loop that only covers its own tables. Migrations 002-012 create 22 tables with tenant_id but no RLS policy.
- **Business Impact**: Cross-tenant data exposure — SOC 2 violation, potential data breach
- **Technical Impact**: Every table created after migration 001 is unprotected
- **Files**: `migrations/versions/002_add_model_registry.py` through `012_add_edge_sync_tables.py`
- **Fix**: Add `CREATE POLICY tenant_isolation ON cdm_xxx USING (tenant_id = current_setting(...))` to each migration's upgrade()
- **Dependencies**: None
- **Effort**: 2 days
- **Owner**: Security Architect / Data Architect
- **Acceptance Criteria**: All 46 tables verified with RLS; integration test passes for each table

### R-002: Add RBAC to 5 Unprotected Services
- **Root Cause**: 5 of 10 services (dpe-svc, mat-svc, del-svc, rec-svc, alert-svc) have zero `require_roles()` or `require_any_permission()` calls.
- **Business Impact**: Any authenticated user can modify demand config, generate POs, acknowledge alerts — no audit trail per role.
- **Technical Impact**: Mutations not role-gated; compliance KPI data unreliable.
- **Files**: 5 service `app/api/v1/*.py` files
- **Fix**: Add `Depends(require_roles([...]))` to write/mutate endpoints
- **Dependencies**: None
- **Effort**: 3 days
- **Owner**: Security Architect
- **Acceptance Criteria**: All mutate endpoints have RBAC; test verifies 403 on unauthorized roles

### R-003: Fix dpe-svc ctp.py Broken Imports
- **Root Cause**: `ctp.py:7` imports `app.core.ctp` (does not exist); `ctp.py:8` imports `get_current_tenant` (does not exist in deps.py)
- **Business Impact**: dpe-svc WILL CRASH at startup — all demand services down
- **Technical Impact**: Module load error prevents dpe-svc from starting
- **Files**: `services/dpe-svc/app/api/v1/ctp.py`, needs `app/core/ctp.py` or removal
- **Fix**: Either implement `app/core/ctp.py` with evaluate_ctp function, or remove the ctp router entirely from dpe-svc (mat-svc already has CTP)
- **Dependencies**: None
- **Effort**: 1 day
- **Owner**: Engineering
- **Acceptance Criteria**: dpe-svc starts without import errors

### R-004: Fix Frontend Import Bugs (3 files)
- **Root Cause**: `schedule/api.ts:1`, `compliance/api.ts:1`, `shop-floor/api.ts:1` use `import { api }` but `lib/api.ts` uses `export default api`
- **Business Impact**: Schedule, Compliance, Shop Floor pages entirely broken — no API calls succeed
- **Technical Impact**: `Uncaught SyntaxError: does not provide an export named 'api'`
- **Files**: `apps/web/src/features/schedule/api.ts:1`, `apps/web/src/features/compliance/api.ts:1`, `apps/web/src/features/shop-floor/api.ts:1`
- **Fix**: Change to `import api from '@/lib/api'`
- **Dependencies**: None
- **Effort**: 0.5 days
- **Owner**: Frontend
- **Acceptance Criteria**: All 3 files import correctly; `pnpm tsc --noEmit` passes

### R-005: Fix alert-svc Broken Consumer
- **Root Cause**: `alert-svc/app/events/consumers.py:15` calls `create_consumer()` — function does not exist in ipe_shared
- **Business Impact**: Alert engine never receives events; no automated alerts in production
- **Technical Impact**: alert-svc crashes at startup when consumer initializes
- **Files**: `services/alert-svc/app/events/consumers.py`
- **Fix**: Rewrite to use `KafkaConsumer` class (same as all other services)
- **Dependencies**: None
- **Effort**: 1 day
- **Owner**: Engineering
- **Acceptance Criteria**: alert-svc consumer starts and processes events

---

## P1-HIGH (8 items — all production blockers)

### R-006: Mount /metrics Endpoint on All Services
- **Root Cause**: `setup_metrics()` is called but no `/metrics` route is registered
- **Files**: All 11 service `main.py` files
- **Fix**: Add `from prometheus_client import generate_latest; app.add_route("/metrics", ...)` or similar
- **Effort**: 1 day
- **Owner**: DevOps

### R-007: Standardize Port Scheme
- **Root Cause**: 3 incompatible port schemes across Dockerfile EXPOSE, Compose, Helm
- **Fix**: Choose one scheme (recommend: Dockerfile ports) and update Compose, Helm, Prometheus, README
- **Effort**: 2 days
- **Owner**: DevOps

### R-008: Add Auth to 3 Open alert-svc Endpoints
- **Files**: `alert-svc/app/api/v1/alerts.py:42,54,69`
- **Fix**: Add `tenant_ctx.get()` check at minimum; RBAC for acknowledge
- **Effort**: 0.5 days
- **Owner**: Security

### R-009: Create 11 Missing Kafka Topics
- **Root Cause**: 11 event topics referenced in code but absent from topic creation scripts
- **Fix**: Add to `create-kafka-topics.sh` and/or `create_sprint3_topics.py`
- **Effort**: 1 day
- **Owner**: DevOps

### R-010: Implement 5 Missing Backend Dashboard Endpoints
- **Root Cause**: Frontend calls `/dashboard/demands`, `/dashboard/capacity`, `/dashboard/alerts`, `/auth/login`, `/auth/me` — none exist
- **Fix**: Create aggregation endpoints in appropriate services; create auth service endpoint
- **Effort**: 5 days
- **Owner**: Engineering

### R-011: Fix Helm Template Bugs
- **Root Cause**: Resources indentation off-by-1; readiness probe uses `/health` instead of `/ready`
- **Files**: `_service.tpl`
- **Effort**: 0.5 days
- **Owner**: DevOps

### R-012: Add Connector to docker-compose.yml
- **Root Cause**: connector service missing from production compose
- **Files**: `infrastructure/docker/docker-compose.yml`
- **Effort**: 0.5 days
- **Owner**: DevOps

### R-013: Fix Environment Variable Naming in Compose
- **Root Cause**: Compose uses non-prefixed names (DATABASE_URL), .env.example uses IPE_ prefix
- **Fix**: Standardize on one convention
- **Effort**: 0.5 days
- **Owner**: DevOps

---

## P2-MEDIUM (8 items)

| ID | Title | Effort | Owner |
|----|-------|--------|-------|
| R-014 | Add missing Avro schemas for 4 send_avro calls | 1 day | Data Architecture |
| R-015 | Add DLQ topics for rec-svc, connector, alert-svc | 0.5 days | DevOps |
| R-016 | Fix seed-data.sh (password_hash, full_name, cdm_location) | 1 day | Data |
| R-017 | Add /ready endpoints to alert-svc | 0.5 days | Engineering |
| R-018 | Remove cdm_tenant RLS self-referencing policy | 0.5 days | Data Architecture |
| R-019 | Fix res-svc Dockerfile duplicate RUN uv sync | 0.25 days | DevOps |
| R-020 | Register weather signal router in dpe-svc | 0.5 days | Engineering |
| R-021 | Raise coverage threshold from 40% to 60% | 5 days | Engineering |

## P3-LOW (5 items)

| ID | Title | Effort | Owner |
|----|-------|--------|-------|
| R-022 | Add missing K8s manifests for rec-svc, alert-svc, connector | 1 day | DevOps |
| R-023 | Connect OpenTelemetry tracing in all services | 2 days | DevOps |
| R-024 | Add rate limiting (Kong plugin or per-service) | 2 days | DevOps |
| R-025 | Add SBOM generation and container scanning to CI | 1 day | DevOps |
| R-026 | Fix Helm readiness probe to use /ready | 0.5 days | DevOps |

---

## Summary

| Priority | Count | Total Effort | Deployment Blocker |
|----------|-------|-------------|-------------------|
| P0-CRITICAL | 5 | 7.5 days | YES (5/5) |
| P1-HIGH | 8 | 11.5 days | YES (8/8) |
| P2-MEDIUM | 8 | 9.75 days | No |
| P3-LOW | 5 | 6.5 days | No |
| **TOTAL** | **26** | **35.25 days** | **13 blockers** |

**Estimated timeline to production ready**: 7 weeks (5 weeks critical+high, 2 weeks medium)
