# Tasks — 015 Enterprise Production Readiness

**Feature**: `015-enterprise-production-readiness`  
**Date**: 2026-07-04  
**Program duration**: 36 weeks (Phases 0–4)  
**Milestone tag**: `v9.3.0-p2` (Phase 2 complete)

---

## Summary

| Phase | Tasks | Status |
|-------|-------|--------|
| 0 Security | T001–T020 | ✅ Complete (Option B E2E) |
| 1 Hardening / K8s prep | T030–T050 | ✅ Phase 1 close (k6 profiles; Helm remainder deferred to Phase 3+) |
| **2 Gates / Observability** | **T060–T068 + T081–T130** | ✅ **Complete** |
| 3 Scale/Compliance | T090–T110 | 🔄 In progress (Helm + SAP/D365 scaffolds) |
| 4 GTM | T120–T140 | ⬜ Not started |
| Hygiene | T000 | ✅ |

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
| T007 | MFA policy documentation for Keycloak | P1 | ⬜ Deferred |
| T008 | Per-tenant custom RBAC roles design | P1 | ⬜ Deferred |
| T009 | `scripts/audit-secrets.sh` CI gate | P0 | ✅ |
| T010 | Pen-test scope document | P2 | ⬜ Deferred |

**Option B (Phase 0 combined E2E):** ✅ PASS — B1 Keycloak, B2 Vault, B3 TLS, B4 Audit, B5 Combined (`verify-gate5.ps1`)

---

## Phase 1 — Production Infrastructure / Hardening (Weeks 3–8)

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T030 | Helm: deploy all 22 services from values | P0 | ⬜ Deferred → Phase 3+ |
| T031 | HPA minReplicas=2 all stateless | P0 | ⬜ Deferred |
| T032 | PDB minAvailable=1 | P0 | ⬜ Deferred |
| T033 | PostgreSQL managed + read replica values | P0 | ⬜ Deferred |
| T034 | Kafka 3-broker Strimzi/MSK values | P0 | ⬜ Deferred |
| T035 | Redis Sentinel helm subchart | P0 | ⬜ Deferred |
| T036 | PgBouncer sidecar / external pooler | P1 | ⬜ Deferred |
| T037 | Graceful SIGTERM all FastAPI services | P0 | ✅ |
| T038 | pybreaker on inter-service httpx | P0 | ✅ |
| T039 | Network policies zero-trust | P1 | ✅ (Docker network isolation Gate 2) |
| T040 | cert-manager ClusterIssuer | P0 | ⬜ Deferred |

**Phase 1 close note:** Performance baselines, DR scripts, and k6 SLO/stress profile split delivered under Phase 1/2 close track (see T081–T090).

---

## Phase 2 — Observability + Enterprise Gates (Weeks 9–14) — ✅ COMPLETE

### Observability (original T060–T068)

| ID | Task | Priority | Status | Evidence |
|----|------|----------|--------|----------|
| T060 | Prometheus `/metrics` all services | P0 | ✅ | `infrastructure/docker/prometheus/prometheus.yml` |
| T061 | Grafana dashboards (system, API, business) | P0 | ✅ | 6 IPE dashboards; `scripts/monitoring/verify-gate1.sh` |
| T062 | structlog JSON + correlation_id middleware | P0 | ✅ | `ipe_shared` observability |
| T063 | OpenTelemetry trace propagation enable | P0 | ✅ | OTel in service setup |
| T064 | Loki or ELK log aggregation | P0 | ⬜ Deferred Phase 3 |
| T065 | Alertmanager rules (P1/P2/P3) | P0 | ✅ | `infrastructure/monitoring/alertmanager/` |
| T066 | PagerDuty/Opsgenie integration | P1 | ⬜ Deferred |
| T067 | SLO/SLI definitions doc | P1 | ✅ | `docs/qa/PERFORMANCE-BASELINE-v9.1.0.md` |
| T068 | Status page (Instatus) webhook | P2 | ⬜ Deferred |

### Gate close track (T081–T130)

| ID | Task | Priority | Status | Evidence |
|----|------|----------|--------|----------|
| T081 | Gate 1 — Observability verification | P0 | ✅ | `scripts/monitoring/verify-gate1.sh` |
| T082 | Gate 2 — Security (network, rate limit, CORS, tenant isolation) | P0 | ✅ | `scripts/security/verify-gate2.sh` |
| T083 | Gate 3 — Multi-tenant quotas + Kafka groups | P0 | ✅ | `scripts/security/verify-gate3.sh` |
| T084 | Gate 4 — Bidirectional Odoo sync + conflict resolver | P0 | ✅ | `scripts/odoo/verify-gate4.sh` |
| T085 | Gate 5 — Full E2E R1+R2 HTTPS + audit | P0 | ✅ | `scripts/security/verify-gate5.ps1` — **14/14 + 5/5** |
| T090 | k6 SLO profile (P95 &lt; 500ms, error &lt; 5%) | P0 | ✅ | `scripts/perf/k6-slo.js`, `docs/qa/k6-slo-baseline.json` |
| T091 | k6 stress profile (429 validates rate limiter) | P0 | ✅ | `scripts/perf/k6-stress.js`, `docs/qa/k6-stress-baseline.json` |
| T100 | Option B Phase 0 combined E2E (B1–B5) | P0 | ✅ | Keycloak, Vault, TLS, Audit, Combined |
| T110 | Demo HTTPS helpers (PS 5.1 TLS, Keycloak JWT) | P0 | ✅ | `scripts/demo-http.ps1` |
| T120 | Audit JSON serialization for asyncpg states | P0 | ✅ | `ipe_shared/audit/service.py` |
| T121 | Activate tenant Odoo credential fallback | P0 | ✅ | `connector/app/api/v1/activate.py` |
| T122 | Fix `sync_bom_details` dead code | P0 | ✅ | `connector/app/odoo/sync_engine.py` |
| T130 | Commit + tag `v9.3.0-p2` | P0 | ✅ | `git tag v9.3.0-p2` on `d5eb454` |

**Phase 2 milestone:** ✅ **COMPLETE** — 2026-07-04

---

## Phase 3 — Scale & Compliance (Weeks 15–22) — 🔄 In progress

| ID | Task | Priority | Status | Evidence |
|----|------|----------|--------|----------|
| T030 | Helm chart for all services | P0 | 🔄 | `helm/ipe/` |
| T031 | HPA minReplicas | P0 | 🔄 | `templates/hpa.yaml` |
| T032 | PDB minAvailable | P0 | 🔄 | `templates/pdb.yaml` |
| T039 | NetworkPolicy zero-trust | P1 | 🔄 | `templates/networkpolicy.yaml` |
| T090a | GDPR export production-harden | P1 | ⬜ | |
| T091a | GDPR erasure + retention purge jobs | P1 | ⬜ | |
| T092 | WCAG 2.1 AA audit + fix critical | P1 | ⬜ | |
| T093 | SOC 2 Type I gap assessment | P1 | ⬜ | |
| T094 | k6 500 VU load test in CI | P0 | ⬜ | |
| T095 | SAP S/4 connector (5 entities) | P1 | 🔄 Scaffold | `app/connectors/sap/` |
| T096 | D365 connector (5 entities) | P2 | 🔄 Scaffold | `app/connectors/d365/` |
| T097 | API v2 versioning Kong routes | P1 | ⬜ | |
| T098 | Tenant resource quotas (CPU/conn) — *app quotas done in P2* | P1 | ✅ (app-level) | |
| T099 | Customer readiness package (Track B) | P0 | ✅ | `docs/customer/star-trans/` |

---

## Phase 4 — GTM (Weeks 23–36) — ⬜ Not started

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T120a | Tenant self-service provision API | P1 | ⬜ |
| T121a | Stripe live mode + webhooks | P1 | ⬜ |
| T122a | Developer portal (aggregated OpenAPI) | P1 | ⬜ |
| T123 | Python SDK package | P2 | ⬜ |
| T124 | JavaScript SDK package | P2 | ⬜ |
| T125 | Knowledge base 50 articles | P2 | ⬜ |
| T126 | Customer health dashboard | P2 | ⬜ |
| T127 | Terraform one-click SaaS module | P1 | ⬜ |
| T128 | On-prem Ansible guide | P2 | ⬜ |

---

## Regression gates (all phases)

| ID | Task | Priority | Status |
|----|------|----------|--------|
| T200 | `run-release1-integration-demo.ps1` 14/14 HTTPS | P0 | ✅ |
| T201 | `run-release2-demo.ps1` 5/5 | P0 | ✅ |
| T202 | Full 32/32 on hybrid stack quarterly | P1 | ⬜ |

---

*Tasks version 2.0 — Phase 2 close 2026-07-04*
