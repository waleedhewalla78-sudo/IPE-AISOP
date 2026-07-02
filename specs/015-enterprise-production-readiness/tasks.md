# Tasks — 015 Enterprise Production Readiness

**Feature**: `015-enterprise-production-readiness`  
**Date**: 2026-06-24  
**Program duration**: 36 weeks (Phases 0–4)

---

## Summary

| Phase | Tasks | Status |
|-------|-------|--------|
| 0 Security | T001–T020 | Pending |
| 1 K8s HA | T030–T050 | Pending |
| 2 Observability | T060–T080 | Pending |
| 3 Scale/Compliance | T090–T110 | Pending |
| 4 GTM | T120–T140 | Pending |
| Hygiene | T000 | Pending |

---

## Phase 0 — Security Foundation (Weeks 1–2)

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T000 | Import roadmap → `docs/strategy/` + `ENTERPRISE-PROGRAM-STATUS.md` | P0 | ✅ |
| T001 | Activate Keycloak OIDC login flow (spec 011) | P0 | ✅ |
| T002 | RS256 JWT signing + key rotation docs | P0 | ✅ |
| T003 | Implement HashiVaultSecretsProvider (hvac) | P0 | ✅ |
| T004 | Implement AwsSecretsProvider (boto3) | P0 | ✅ |
| T005 | Kong TLS termination + HSTS headers | P0 | ✅ |
| T006 | API request audit middleware | P0 | ✅ |
| T007 | MFA policy documentation for Keycloak | P1 | ⬜ |
| T008 | Per-tenant custom RBAC roles design | P1 | ⬜ |
| T009 | `scripts/audit-secrets.sh` CI gate | P0 | ⬜ |
| T010 | Pen-test scope document | P2 | ⬜ |

---

## Phase 1 — Production Infrastructure (Weeks 3–8)

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T030 | Helm: deploy all 22 services from values | P0 | ⬜ |
| T031 | HPA minReplicas=2 all stateless | P0 | ⬜ |
| T032 | PDB minAvailable=1 | P0 | ⬜ |
| T033 | PostgreSQL managed + read replica values | P0 | ⬜ |
| T034 | Kafka 3-broker Strimzi/MSK values | P0 | ⬜ |
| T035 | Redis Sentinel helm subchart | P0 | ⬜ |
| T036 | PgBouncer sidecar / external pooler | P1 | ⬜ |
| T037 | Graceful SIGTERM all FastAPI services | P0 | ⬜ |
| T038 | pybreaker on inter-service httpx | P0 | ⬜ |
| T039 | Network policies zero-trust | P1 | ⬜ |
| T040 | cert-manager ClusterIssuer | P0 | ⬜ |

---

## Phase 2 — Observability (Weeks 9–14)

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T060 | Prometheus `/metrics` all services | P0 | ⬜ |
| T061 | Grafana dashboards (system, API, business) | P0 | ⬜ |
| T062 | structlog JSON + correlation_id middleware | P0 | ⬜ |
| T063 | OpenTelemetry trace propagation enable | P0 | ⬜ |
| T064 | Loki or ELK log aggregation | P0 | ⬜ |
| T065 | Alertmanager rules (P1/P2/P3) | P0 | ⬜ |
| T066 | PagerDuty/Opsgenie integration | P1 | ⬜ |
| T067 | SLO/SLI definitions doc | P1 | ⬜ |
| T068 | Status page (Instatus) webhook | P2 | ⬜ |

---

## Phase 3 — Scale & Compliance (Weeks 15–22)

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T090 | GDPR export production-harden | P1 | ⬜ |
| T091 | GDPR erasure + retention purge jobs | P1 | ⬜ |
| T092 | WCAG 2.1 AA audit + fix critical | P1 | ⬜ |
| T093 | SOC 2 Type I gap assessment | P1 | ⬜ |
| T094 | k6 500 VU load test in CI | P0 | ⬜ |
| T095 | SAP S/4 connector (5 entities) | P1 | ⬜ |
| T096 | D365 connector (5 entities) | P2 | ⬜ |
| T097 | API v2 versioning Kong routes | P1 | ⬜ |
| T098 | Tenant resource quotas (CPU/conn) | P1 | ⬜ |

---

## Phase 4 — GTM (Weeks 23–36)

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T120 | Tenant self-service provision API | P1 | ⬜ |
| T121 | Stripe live mode + webhooks | P1 | ⬜ |
| T122 | Developer portal (aggregated OpenAPI) | P1 | ⬜ |
| T123 | Python SDK package | P2 | ⬜ |
| T124 | JavaScript SDK package | P2 | ⬜ |
| T125 | Knowledge base 50 articles | P2 | ⬜ |
| T126 | Customer health dashboard | P2 | ⬜ |
| T127 | Terraform one-click SaaS module | P1 | ⬜ |
| T128 | On-prem Ansible guide | P2 | ⬜ |

---

## Regression gates (all phases)

| ID | Task | Priority |
|----|------|----------|
| T200 | `run-release1-integration-demo.ps1` 13/13 | P0 |
| T201 | `run-release2-demo.ps1` 5/5 | P0 |
| T202 | Full 32/32 on hybrid stack quarterly | P1 |

---

*Tasks version 1.0 — `/speckit.tasks`*
