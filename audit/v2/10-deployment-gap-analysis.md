# 10 — Deployment Gap Analysis (V2 Audit)

**Generated**: 2026-06-20

## Per-Service Deployment Gaps

### dpe-svc
| Gap | Severity | Evidence |
|-----|----------|----------|
| ctp.py imports broken module → startup crash | CRITICAL | ctp.py:7-8 — `app.core.ctp` + `get_current_tenant` don't exist |
| No /metrics endpoint exposed | CRITICAL | main.py — `setup_metrics()` called, route not mounted |
| Port: Dockerfile 8001 vs Compose 8002 | HIGH | Dockerfile EXPOSE vs compose ports value |
| No RBAC on any endpoint | HIGH | 12 functional endpoints, 0 require_roles |

### mat-svc
| Gap | Severity | Evidence |
|-----|----------|----------|
| No /metrics endpoint exposed | CRITICAL | All services share this gap |
| Port: Dockerfile 8002 vs Compose 8003 | HIGH | |
| No RBAC on 12 endpoints | HIGH | |

### cap-svc
| Gap | Severity | Evidence |
|-----|----------|----------|
| No /metrics endpoint exposed | CRITICAL | |
| Port: Dockerfile 8003 vs Compose 8004 | HIGH | |
| 5 labor endpoints + diff endpoint missing RBAC | HIGH | |

### fea-svc
| Gap | Severity | Evidence |
|-----|----------|----------|
| No /metrics endpoint exposed | CRITICAL | |
| Port: Dockerfile 8004 vs Compose 8006 vs Helm 8005 | CRITICAL | 3-way port drift |
| /ready Kafka check hardcoded "ok" | MEDIUM | health.py — not a real check |

### res-svc
| Gap | Severity | Evidence |
|-----|----------|----------|
| No /metrics endpoint exposed | CRITICAL | |
| Dockerfile has duplicate `RUN uv sync` | LOW | Lines 9-11 |
| No RBAC on POST /scenarios (create) | HIGH | |

### del-svc
| Gap | Severity | Evidence |
|-----|----------|----------|
| No /metrics endpoint exposed | CRITICAL | |
| No RBAC on 8 endpoints | HIGH | |
| Port: Dockerfile 8006 vs Compose 8007 | HIGH | |

### nlp-svc
| Gap | Severity | Evidence |
|-----|----------|----------|
| No /metrics endpoint exposed | CRITICAL | |
| Port: Dockerfile 8007 vs Compose 8009 vs Helm 8008 | CRITICAL | 3-way port drift |

### rec-svc
| Gap | Severity | Evidence |
|-----|----------|----------|
| No /metrics endpoint exposed | CRITICAL | |
| No individual K8s manifest | HIGH | |
| No RBAC on 3 endpoints | HIGH | |
| No DLQ topic | MEDIUM | |

### alert-svc
| Gap | Severity | Evidence |
|-----|----------|----------|
| No /metrics endpoint exposed | CRITICAL | |
| No /ready endpoint | CRITICAL | Only /health, no dependency checks |
| No individual K8s manifest | HIGH | |
| Consumer broken (non-existent `create_consumer`) | CRITICAL | consumers.py:15 |
| 3 endpoints completely unauthenticated | CRITICAL | alerts.py:42,54,69 |
| Dockerfile CMD missing --no-sync | LOW | |
| No DLQ topic | MEDIUM | |
| Not in Prometheus scrape targets | MEDIUM | prometheus.yml |

### connector
| Gap | Severity | Evidence |
|-----|----------|----------|
| No /metrics endpoint exposed | CRITICAL | |
| Missing from docker-compose.yml | CRITICAL | |
| No individual K8s manifest | HIGH | |
| No DLQ topic | MEDIUM | |

### mock-odoo-api
| Gap | Severity | Evidence |
|-----|----------|----------|
| Missing from docker-compose.yml | HIGH | Test-only |
| Missing from K8s, Helm, CI | HIGH | |
| No observability | HIGH | |
| No tests | MEDIUM | Only `__init__.py` |

## Systemic Gaps (Affecting All/All Services)

| Gap | Services Affected | Severity |
|-----|------------------|----------|
| No /metrics endpoint | All 11 services | CRITICAL |
| Port inconsistency | 8 of 10 services | CRITICAL |
| No OpenTelemetry tracing | All 11 services | HIGH |
| No rate limiting | All 10 API services | HIGH |
| RLS missing for 22 tables | All services | CRITICAL |
| 11 event topics not created | 5 services | HIGH |
| 3 frontend import bugs | 3 feature pages | CRITICAL |
| 5 frontend API calls have no backend | 3 feature pages | HIGH |
