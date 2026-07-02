# Feature Specification: Enterprise Production Readiness (015)

**Feature**: `015-enterprise-production-readiness`  
**Version**: 1.0  
**Date**: 2026-06-24  
**Status**: Specify complete  
**Depends on**: `014-release2-growth` (commercial R2), `013-release1-odoo-mena` (Odoo R1), platform `v8.2.0`  
**Release target**: `v10.0.0-enterprise` (phased; no single big-bang tag)  
**Source documents**:
- `docs/strategy/IPE_Enterprise_Deployment_Roadmap.md` (36-week Phases 0–4)
- `IPE_v8.2.0_Gap_Closure_Action_Plan` (P1/P2 closure — largely complete)
- `IPE_v8_Upgrade_Proposal_SAP_Gap_Analysis` (U1–U8 — implemented in v8.2.0)
- `IPE_vs_SAP_Joule_IBP_Gap_Analysis` (competitive positioning)
- `IPE-v6-Master-Execution-Plan` (historical baseline; superseded by Speckit 000–015)

---

## 1. Vision (what we want to build)

> **Transform IPE from a demo-proven planning platform (32/32 checkpoints, 13/13 Odoo R1) into an enterprise-contractable product: SSO, vault secrets, K8s HA, observability, GDPR/SOC2 readiness, ERP expansion (SAP/D365), and GTM infrastructure — without breaking Release 1/2 customer demos.**

| Dimension | Today (v8.2.0 + R1/R2) | Enterprise target |
|-----------|------------------------|-------------------|
| Auth | Local JWT + RBAC scaffold | Keycloak/OIDC + RS256 + MFA |
| Secrets | `config/secrets_manager.py` env stub | Vault / AWS SM activation |
| Deploy | docker-compose single host | Helm/K8s + HPA + PDB |
| Observability | `/health` only | Prometheus + Grafana + OTel traces |
| Compliance | `cdm_audit_log` append-only | GDPR APIs + SOC2 Type I path |
| ERP | Odoo 19 R1 (13/13) | + SAP S/4 + D365 connectors |
| Commercial | R2 Outcomes/Copilot | Self-service SaaS + Stripe live |

---

## 2. What we have built (baseline)

| Asset | Status | Evidence |
|-------|--------|----------|
| Platform v8.2.0 (U1–U8) | ✅ | `READINESS.md`, tag `v8.2.0` |
| 32/32 demo (hybrid stack) | ✅ | `docs/demo-data/` |
| Release 1 Odoo 13/13 | ✅ | `release1-integration-demo-final.txt` |
| Release 2 streams A–D | 🔄 In progress | `specs/014-release2-growth` |
| Keycloak scaffold | ✅ POST-B | `ipe_shared/auth/keycloak.py`, spec 011 |
| Secrets manager scaffold | ✅ POST-B | `config/secrets_manager.py` |
| Stripe adapter scaffold | ✅ POST-B | `ipe_shared/billing/stripe_adapter.py` |
| Helm chart skeleton | ✅ | `infrastructure/k8s/helm/ipe-platform/` |
| Audit log immutability | ✅ | migration 021, `cdm_audit_log` |
| GDPR DSAR scaffold | ✅ | `dpe-svc/dsar.py` |
| Enterprise roadmap doc | ✅ | `docs/strategy/IPE_Enterprise_Deployment_Roadmap.md` |

---

## 3. Scope — Enterprise phases (from roadmap)

### Phase 0 — Security Foundation (Weeks 1–2) P0

**User story:** As a **CISO**, I need corporate IdP SSO and vault-backed secrets so I can approve a security review.

**FR-015-01** Keycloak OIDC/SAML integration (activate scaffold)  
**FR-015-02** RS256 JWT signing with key rotation  
**FR-015-03** HashiCorp Vault / AWS SM provider activation in `secrets_manager.py`  
**FR-015-04** TLS termination at Kong with cert-manager pattern documented  
**FR-015-05** API request audit logging middleware (user, tenant, action, IP)

### Phase 1 — Production Infrastructure (Weeks 3–8) P0

**FR-015-10** Helm deploy all 22+ services with resource limits  
**FR-015-11** HPA min 2 replicas stateless services  
**FR-015-12** PostgreSQL HA (managed RDS or Patroni) + read replica  
**FR-015-13** Kafka 3-broker cluster config  
**FR-015-14** Redis Sentinel / cluster  
**FR-015-15** PgBouncer connection pooling  
**FR-015-16** Graceful SIGTERM shutdown all services  
**FR-015-17** Circuit breakers on inter-service HTTP (pybreaker)

### Phase 2 — Observability & Reliability (Weeks 9–14) P0

**FR-015-20** Prometheus `/metrics` on every service  
**FR-015-21** Grafana dashboards (system + business KPIs)  
**FR-015-22** Structured JSON logging + correlation IDs  
**FR-015-23** OpenTelemetry trace propagation  
**FR-015-24** Alertmanager rules + PagerDuty integration  
**FR-015-25** SLO/SLI definitions + error budget tracking  
**FR-015-26** Customer status page integration

### Phase 3 — Scale & Compliance (Weeks 15–22) P1

**FR-015-30** GDPR data export + erasure APIs production-hardened  
**FR-015-31** WCAG 2.1 AA audit remediation  
**FR-015-32** SOC 2 Type I gap assessment  
**FR-015-33** Load test 500 concurrent users (k6) in CI  
**FR-015-34** SAP S/4HANA connector (5 entities)  
**FR-015-35** D365 connector (5 entities)  
**FR-015-36** API versioning strategy v1/v2

### Phase 4 — GTM & Growth (Weeks 23–36) P1–P2

**FR-015-40** Tenant self-service provisioning API  
**FR-015-41** Stripe billing live mode + metered usage  
**FR-015-42** Developer portal (unified OpenAPI)  
**FR-015-43** Python + JS SDKs  
**FR-015-44** Knowledge base (50 articles)  
**FR-015-45** Customer health dashboard

---

## 4. Out of scope (015)

- Replacing Odoo as system of record (IPE remains planning layer)
- On-prem air-gapped full automation (document only in Phase 4)
- Full SAP IBP feature parity (positioning doc only)
- Breaking Release 1 8 GB VM profile

---

## 5. Success criteria

| ID | Criterion | Target |
|----|-----------|--------|
| SC-015-01 | Enterprise checklist Phase 0 items | 100% SEC-001–005 signed off |
| SC-015-02 | K8s staging deploy | `helm install` green in < 30 min |
| SC-015-03 | Observability | All services scraped + 3 Grafana dashboards |
| SC-015-04 | Load test | 500 users p95 read < 500ms |
| SC-015-05 | Compliance | GDPR export < 10 min for 1M rows |
| SC-015-06 | No R1/R2 regression | 13/13 + 5/5 demos PASS after each phase gate |

---

*Spec version 1.0 — `/speckit.specify`*
