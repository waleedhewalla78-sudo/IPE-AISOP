# 12 — Configuration Drift Analysis (V2 Audit)

**Generated**: 2026-06-20 | **Scope**: All configuration layers across development, CI, staging, and production targets.

---

## Drift Type 1: Port Scheme Inconsistency (CRITICAL)

The codebase has THREE incompatible port assignment schemes:

| Service | Dockerfile EXPOSE | docker-compose map | K8s Individual | Helm values | Prometheus target | README |
|---------|-------------------|-------------------|----------------|-------------|-------------------|--------|
| dpe-svc | **8001** | **8002** | 8001 | 8002 | 8001 | 8001 |
| mat-svc | **8002** | **8003** | 8002 | 8003 | 8002 | 8002 |
| cap-svc | **8003** | **8004** | 8003 | 8004 | 8003 | 8003 |
| fea-svc | **8004** | **8006** | 8004 | **8005** | 8004 | 8004 |
| res-svc | **8005** | **8005** | 8005 | **8006** | 8005 | 8005 |
| del-svc | **8006** | **8007** | 8006 | 8007 | 8006 | 8006 |
| nlp-svc | **8007** | **8009** | 8007 | **8008** | 8007 | 8007 |
| rec-svc | **8008** | **8008** | — | **8009** | 8008 | 8008 |
| alert-svc | **8010** | **8010** | — | 8010 | **MISSING** | 8010 |
| connector | **8009** | **MISSING** | — | **8001** | 8009 | 8009 |

**Scheme 1 (Dockerfile/README/Prometheus)**: Sequential 8001-8010
**Scheme 2 (Compose)**: Sequential 8002-8010 (1-up shift for dpe through nlp)
**Scheme 3 (Helm)**: Mixed — some match Dockerfile, some match Compose, some unique

**Impact**: Services configured with different port schemes will fail to connect. NGINX proxy, Kong routes, and inter-service calls all depend on correct ports.

**Root Cause**: Compose port numbers were shifted up by 1 for dpe-svc through cap-svc to avoid conflicts (8000 used by frontend/nginx). This was not propagated to Dockerfiles, Helm, or README.

---

## Drift Type 2: Environment Variable Naming (HIGH)

| Variable | .env.example | docker-compose.yml | K8s configmap | Settings class |
|----------|-------------|-------------------|---------------|----------------|
| Database URL | `IPE_DATABASE_URL` | `DATABASE_URL` | Uses configmap `DATABASE_URL` | Reads `IPE_DATABASE_URL` then `DATABASE_URL` |
| Kafka Bootstrap | `IPE_KAFKA_BOOTSTRAP_SERVERS` | `KAFKA_BOOTSTRAP_SERVERS` | Uses configmap `KAFKA_BOOTSTRAP_SERVERS` | Reads `IPE_KAFKA_BOOTSTRAP_SERVERS` |
| Redis URL | `IPE_REDIS_URL` | `REDIS_URL` | Uses configmap `REDIS_URL` | Reads `IPE_REDIS_URL` |
| Service URLs | `IPE_DPE_SVC_URL` | `DPE_SVC_URL` | Not in configmap | Reads `IPE_DPE_SVC_URL` |
| JWT Settings | `IPE_JWT_SECRET_KEY` | **NOT SET** | Uses secret | Reads `IPE_JWT_SECRET_KEY` |
| Anthropic Key | `IPE_ANTHROPIC_API_KEY` | `ANTHROPIC_API_KEY` | Uses secret | Reads `IPE_ANTHROPIC_API_KEY` |
| Environment | `IPE_ENVIRONMENT` | **NOT SET** | `ENVIRONMENT` (Helm) | Reads `IPE_ENVIRONMENT` then `ENVIRONMENT` |

**Impact**: Services use `IPE_`-prefixed env vars but Compose provides non-prefixed names. If Settings class handles BOTH conventions (confirmed it does via dual read), this is a warning. If not, services won't find their config.

**Note**: `ipe_shared/config.py` line 22 mode shows `case_sensitive=False` which handles case but NOT prefix differences. Need to verify dual-naming support.

---

## Drift Type 3: Helm Template Bugs (HIGH)

| Issue | File | Line | Impact |
|-------|------|------|--------|
| Resources indentation off-by-1 | `_service.tpl` | ~40 | May cause YAML parse error |
| Readiness probe uses `/health` not `/ready` | `_service.tpl` | probe section | K8s won't detect dependency failures |
| `ENVIRONMENT` var uses no `IPE_` prefix | `_service.tpl` | env section | Settings class expects `IPE_ENVIRONMENT` |
| Helm ports for fea-svc (8005), res-svc (8006), nlp-svc (8008), rec-svc (8009) differ from Dockerfile/Compose | `values.yaml` | service definitions | Services unreachable via K8s service discovery |

---

## Drift Type 4: Service Presence Gaps (HIGH)

| Service | docker-compose.yml | docker-compose.test.yml | K8s individual | Helm | CI matrix |
|---------|-------------------|------------------------|---------------|------|-----------|
| dpe-svc | ✅ | ✅ | ✅ | ✅ | ✅ |
| mat-svc | ✅ | ✅ | ✅ | ✅ | ✅ |
| cap-svc | ✅ | ✅ | ✅ | ✅ | ✅ |
| fea-svc | ✅ | ✅ | ✅ | ✅ | ✅ |
| res-svc | ✅ | ✅ | ✅ | ✅ | ✅ |
| del-svc | ✅ | ✅ | ✅ | ✅ | ✅ |
| nlp-svc | ✅ | ✅ | ✅ | ✅ | ✅ |
| rec-svc | ✅ | ✅ | **MISSING** | ✅ | ✅ |
| alert-svc | ✅ | ✅ | **MISSING** | ✅ | ✅ |
| connector | **MISSING** | **MISSING** | **MISSING** | ✅ | ✅ |
| mock-odoo-api | **MISSING** | ✅ | **MISSING** | **MISSING** | **MISSING** |

---

## Drift Type 5: CI vs Local Configuration (MEDIUM)

| Config | Local (.env.example) | CI (ci.yml services section) | Drift |
|--------|---------------------|------------------------------|-------|
| PostgreSQL port | 5432 | 5432 | ✅ Match |
| Kafka port | 9092 | 9092 (localhost:9092 in CI) | ✅ Match |
| Redis port | 6379 | 6379 | ✅ Match |
| Kafka advertised listener | `localhost:9092` | `localhost:9092` | ✅ Match |
| Schema Registry port | 8081 (not in .env.example) | N/A | — |

---

## Drift Type 6: CORS Configuration (LOW)

| Service | allow_origins | Compose overrides? |
|---------|---------------|-------------------|
| All 11 services | `http://localhost:3000` | No |

**Impact**: Production deployment must set `IPE_CORS_ORIGINS` to production domain. Current default would block all production requests.

---

## Drift Type 7: Feature Flag / Autonomy Mode (MEDIUM)

| Config | Default | Override Method |
|--------|---------|-----------------|
| Autonomy mode | `suggest` | `PUT /api/v1/admin/config` |
| Coverage threshold | 40% | Per-service `pyproject.toml` |
| Solver timeout | 30s | Hardcoded in `scheduler.py` |

---

## Drift Type 8: Prometheus Scrape Targets vs Actual Services (HIGH)

prometheus.yml has 13 scrape targets. Missing:
- `alert-svc` (no scrape target at all)
- `schema-registry` (added in compose but not in prometheus config)
- `frontend` (no metrics endpoint)
- `airflow` (no scrape target)
- `prometheus` self-target (localhost:9090 — may not resolve in Docker)

---

## Summary

| Drift Type | Severity | Services Affected | Fix Effort |
|-----------|----------|-------------------|------------|
| Port scheme inconsistency | CRITICAL | 8 of 10 | 2 days |
| Env var naming | HIGH | 10 of 10 | 0.5 days |
| Helm template bugs | HIGH | All via Helm | 0.5 days |
| Service presence gaps | HIGH | 3 services | 1 day |
| CI vs Local config | MEDIUM | N/A | 0 days |
| CORS production override | LOW | All services | 0.25 days |
| Feature flag inconsistency | MEDIUM | dpe-svc, cap-svc | 0.5 days |
| Prometheus target gaps | HIGH | alert-svc, airflow | 0.25 days |

**Total drift fixes**: 9 distinct categories requiring ~5 days effort.
