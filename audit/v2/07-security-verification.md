# 07 — Security Verification (V2 Audit)

**Generated**: 2026-06-20 | **Scope**: All 11 services, database, Kong gateway, event bus

## Executive Security Assessment

| Domain | Status | Critical Issues |
|--------|--------|-----------------|
| Authentication (JWT) | PARTIALLY IMPLEMENTED | No auth service (login/me endpoints not found) |
| Authorization (RBAC) | PARTIALLY IMPLEMENTED | 5 of 10 services have ZERO RBAC |
| Tenant Isolation (RLS) | PARTIALLY IMPLEMENTED | 22 of 46 tables MISSING RLS |
| Secrets Management | PARTIALLY IMPLEMENTED | Dev defaults in code; Docker secrets config exists |
| API Security | FAIL | No rate limiting; 3 open endpoints |
| Dependency Security | WARN | 3 dev CVEs (non-production) |

---

## 1. RBAC Coverage Audit

### Services WITH Application RBAC

| Service | RBAC Endpoints | Protected | Unprotected |
|---------|---------------|-----------|-------------|
| cap-svc | schedule, cost-optimized, network-optimize, green-schedule, scenario clone/solve | 9 | 11 |
| fea-svc | auto-confirm, compliance-kpis | 2 | 6 |
| res-svc | approve | 1 | 2 |
| nlp-svc | chat, query | 2 | 0 |

### Services WITHOUT ANY Application RBAC

| Service | Endpoints | Risk |
|---------|-----------|------|
| **dpe-svc** | 15 production endpoints | Any user can classify demand, modify config, view analytics |
| **mat-svc** | 12 computation endpoints | Any user can run Monte Carlo, generate POs, trigger CTP |
| **del-svc** | 8 classification/quality endpoints | Any user can classify delays, create quality events |
| **rec-svc** | 3 reconciliation endpoints | Any user can trigger daily reconciliation, view drift |
| **alert-svc** | 5 endpoints + 3 completely OPEN | Anyone can list/acknowledge alerts; no auth on 3 endpoints |

---

## 2. RLS Coverage Audit

### Migration 001: 19 tables — ALL have RLS via dynamic loop ✓

### Migrations 002–012: 27 tables created — 22 with tenant_id but ZERO RLS

| Migration | Table | tenant_id | RLS |
|-----------|-------|-----------|-----|
| 002 | cdm_model_registry | YES | **MISSING** |
| 003 | cdm_customer | YES | **MISSING** |
| 003 | cdm_resource_calendar | YES | **MISSING** |
| 004 | cdm_disruption_event | YES | **MISSING** |
| 004 | cdm_duration_prediction | YES | **MISSING** |
| 005 | cdm_scenario | YES | **MISSING** |
| 005 | cdm_delay_root_cause | YES | **MISSING** |
| 006 | cdm_skill | YES | **MISSING** |
| 006 | cdm_worker | YES | **MISSING** |
| 006 | cdm_shift | YES | **MISSING** |
| 008 | cdm_plant | YES | **MISSING** |
| 008 | cdm_transfer_route | YES | **MISSING** |
| 008 | cdm_transport_fleet | YES | **MISSING** |
| 009 | cdm_quality_event | YES | **MISSING** |
| 010 | cdm_emission_factor | YES | **MISSING** |
| 010 | cdm_material_carbon | YES | **MISSING** |
| 010 | cdm_transport_emission | YES | **MISSING** |
| 011 | cdm_financial_projection | YES | **MISSING** |
| 012 | cdm_edge_gateway | YES | **MISSING** |
| 012 | cdm_edge_sync_batch | YES | **MISSING** |
| 012 | cdm_edge_sync_record | YES | **MISSING** |
| 012 | cdm_edge_schedule_delta | YES | **MISSING** |

**Result**: Every migration from 002–012 that creates a tenant_id-bearing table does NOT add RLS. This is a systemic gap — the dynamic loop approach in migration 001 only covers the initial 19 tables. Multi-tenant isolation is **broken** for 22 production tables.

---

## 3. Hardcoded Values Audit

| File | Value | Severity | Overrideable? |
|------|-------|----------|---------------|
| `ipe_shared/config.py:10` | `JWT_SECRET_KEY = "dev-only-change-in-production-min-32-chars-long!!"` | **HIGH** | Yes (`IPE_JWT_SECRET_KEY`) |
| `ipe_shared/config.py:5` | DB URL default: `postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev` | **MEDIUM** | Yes (`IPE_DATABASE_URL`) |
| `ipe_shared/config.py:9` | Redis URL default: `redis://localhost:6379/0` | **LOW** | Yes (`IPE_REDIS_URL`) |
| `migrations/001_initial_schema.py:23` | `PASSWORD 'ipe_app_pass'` | **MEDIUM** | No — hardcoded in SQL migration |
| `migrations/001_initial_schema.py:25` | `PASSWORD 'ipe_audit_writer_pass'` | **MEDIUM** | No — hardcoded in SQL migration |
| `docker-compose.yml` (del-svc) | `ANTHROPIC_API_KEY=mock_anthropic_key` | **LOW** | Placeholder value |
| `docker-compose.yml` (nlp-svc) | `ANTHROPIC_API_KEY=mock_anthropic_key` | **LOW** | Placeholder value |

---

## 4. Kong Gateway Security

| Check | Status | Evidence |
|-------|--------|----------|
| JWT plugin on all routes | ✅ | All 9 services in `kong.yml` |
| claims_to_verify: ["exp"] | ✅ | Token expiry enforced |
| X-Tenant-ID header injection | ✅ | Via `request-transformer` plugin |
| Rate limiting | ❌ | NOT configured |
| TLS termination | ❌ | NOT configured in compose |

---

## 5. API Security Gaps

### Completely Open Endpoints (No Auth)
Alert Service:
- `GET /api/v1/alerts/{alert_id}` — anyone can read any alert
- `POST /api/v1/alerts/{alert_id}/acknowledge` — anyone can acknowledge any alert
- `GET /api/v1/alerts/rules/active` — anyone can list alert rules

### Rate Limiting
- **ZERO** rate limiting configured anywhere — no service uses slowapi or any throttle mechanism
- Kong does not have rate-limiting plugin configured

### CORS Configuration
- All services: `allow_origins=["http://localhost:3000"]` — properly restricted (not wildcard)
- `allow_methods=["GET","POST","PUT","DELETE","OPTIONS"]` — properly scoped
- `allow_headers=["Authorization","Content-Type","X-Tenant-ID"]` — properly scoped
- **STATUS**: VERIFIED — but needs override for production domains

---

## 6. Dependency Vulnerabilities

| Package | Version | CVE Severity | Type | Risk |
|---------|---------|-------------|------|------|
| vitest | ^2.0.5 | Critical | Dev only | Test runner; not in production image |
| vite | ^5.4.0 | High | Dev only | Build tool; production serves via nginx/Kong |
| esbuild | 0.21.5 (transitive) | High | Dev only | Bundle dependency; not shipped |

---

## Security Risk Register

| ID | Risk | Impact | Likelihood | Severity | Blocker |
|----|------|--------|-----------|----------|---------|
| SEC-01 | 22 tables without RLS → cross-tenant data exposure | Critical | High | **10/10** | **YES** |
| SEC-02 | 5 services with ZERO RBAC → unauthorized mutations | High | High | **9/10** | **YES** |
| SEC-03 | 3 alert-svc endpoints completely open | Medium | High | **7/10** | **YES** |
| SEC-04 | No rate limiting → DoS vulnerability | High | Medium | **7/10** | YES |
| SEC-05 | Hardcoded DB passwords in migration SQL | Medium | Low | **4/10** | No |
| SEC-06 | Dev JWT secret as default | Medium | Medium | **5/10** | YES |
| SEC-07 | 3 dev CVEs (non-production) | Low | Low | **2/10** | No |
