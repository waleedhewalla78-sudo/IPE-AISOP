# IPE — Enterprise Deployment & Development Roadmap

**Product**: Intelligent Planning Engine (IPE) v8.2.0+  
**Document Type**: Strategic Transition Plan — Demo to Production Enterprise  
**Classification**: Internal / Strategic  
**Date**: 2026-07-01  
**Prepared For**: IPE Product Leadership  

---

## Table of Contents

1. [Transition Assessment — Demo vs. Enterprise-Ready](#1-transition-assessment)
2. [Enterprise Readiness Checklist](#2-enterprise-readiness-checklist)
3. [Competitive Positioning Analysis](#3-competitive-positioning-analysis)
4. [Phased Roadmap](#4-phased-roadmap)
5. [Sprint Breakdown — Phases 1–4](#5-sprint-breakdown)
6. [Technical Debt & Modernization](#6-technical-debt--modernization)
7. [Go-Live Checklist](#7-go-live-checklist)
8. [Timeline & Resource Estimate](#8-timeline--resource-estimate)

---

## 1. Transition Assessment

### 1.1 What Separates a Demo from an Enterprise Product

A demo proves capability. An enterprise product proves reliability at scale, under adversarial conditions, with contractual guarantees. The gap between these two states is not incremental — it is structural. IPE has demonstrated functional capability across 22 microservices, 32 demo checkpoints, and live Odoo 19 integration. But a CIO signing an enterprise contract evaluates an entirely different set of criteria: What happens when the database fails at 3 AM? How do you prevent Tenant A from seeing Tenant B's forecast? What is your mean time to recovery? Can you pass a SOC 2 audit? The answers to these questions determine whether a product gets a pilot or a purchase order.

The transition from demo to enterprise-ready requires closing gaps across seven dimensions, each of which represents a potential deal-killer in enterprise sales cycles. These dimensions are not equally weighted — security and data isolation are table stakes; scalability and observability are differentiators; and compliance is a market access requirement. Below, each dimension is assessed against IPE's current state with specific, evidence-based gap identification.

### 1.2 Dimension-by-Dimension Gap Analysis

#### Security Posture

**Current State**: IPE uses local JWT authentication via dpe-svc with 8 RBAC roles (admin, planner, procurement, viewer, etc.). Row-Level Security (RLS) is enabled on PostgreSQL 16 with tenant_id-based policies. A Keycloak SSO scaffold exists at `ipe_shared/auth/keycloak.py` but is non-functional. API keys for Odoo integration are stored in environment variables with a KMS encryption wrapper in the connector service. Secrets management is handled through `config/secrets_manager.py` — a stub that reads from environment variables, not a production vault.

**Enterprise Requirement**: Enterprise customers mandate SAML 2.0 or OpenID Connect SSO with their corporate identity provider (Azure AD, Okta, OneLogin). Passwords must never be stored in plaintext or environment files — a HashiCorp Vault or AWS Secrets Manager integration is non-negotiable. API keys must rotate automatically. JWT tokens must use RS256 (asymmetric) signing, not HS256 (symmetric), to support key rotation without service restart. Session management must support forced logout, token revocation, and multi-factor authentication. The current 8-role RBAC model is adequate for a single-tenant demo but insufficient for enterprise — customers will require custom roles, attribute-based access control (ABAC), and role hierarchy.

**Gap Severity**: P0 — blocks enterprise sales. No customer with a corporate IdP will accept local JWT only.

**Specific Gaps**:
- Keycloak integration is scaffold-only; no SAML/OIDC flow implemented
- JWT signing uses HS256 with static key — no rotation mechanism
- No MFA support in auth flow
- No session revocation capability
- API key rotation is manual (environment variable change + restart)
- RBAC roles are hardcoded, not configurable per tenant
- No attribute-based access control (ABAC) layer
- No IP allowlist or network-level access control for admin endpoints

#### Scalability & Performance

**Current State**: IPE runs as 22 Docker containers orchestrated via docker-compose on a single host. PostgreSQL 16 serves all services with connection pooling. Kafka handles 24+ topics for async communication. Redis provides caching. Kong acts as API gateway with basic rate limiting. No horizontal scaling is configured — each service runs a single instance. No load balancing between service replicas exists. No auto-scaling policies are defined. The k6 performance test suite exists but baselines are not documented for production-scale loads (1,000+ concurrent users).

**Enterprise Requirement**: Enterprise deployments must handle 500–5,000 concurrent users per tenant, with 10–100 tenants on a shared SaaS instance (or single-tenant on-premise). Database must support read replicas for reporting workloads. Kafka consumer groups must support rebalancing when instances scale. Services must be stateless to allow horizontal pod autoscaling (HPA) in Kubernetes. The API gateway must handle 10,000+ requests per minute with p95 latency under 200ms for read operations and under 2 seconds for complex planning operations (scenario simulation, OR-Tools optimization). Database query performance must be profiled and indexed for tables exceeding 1M rows.

**Gap Severity**: P0 for SaaS; P1 for single-tenant on-premise.

**Specific Gaps**:
- Single-instance services with no HPA or load balancing configuration
- No Kubernetes manifests (Deployments, Services, HPA, PDB, Ingress)
- No read replicas for PostgreSQL
- Kafka consumer group rebalancing not tested at scale
- No connection pool tuning for high-concurrency (PgBouncer not configured)
- No database query profiling or slow query logging
- No CDN or static asset caching for frontend
- No Redis cluster configuration for cache availability
- No API response caching strategy for expensive planning operations
- Planning algorithms (OR-Tools, Prophet, LSTM) not benchmarked for production dataset sizes

#### Reliability & Availability

**Current State**: Chaos tests (C1–C6) validate that the system recovers from individual service failures. Docker-compose restart policies exist (`restart: unless-stopped`). Health check endpoints exist on most services. Kong has a health wait script for stack startup. However, there is no documented Mean Time to Recovery (MTTR). No automated failover for database or Kafka. No circuit breaker pattern beyond Kong's basic upstream health checks. No Graceful shutdown handling (in-flight requests may be dropped on container termination).

**Enterprise Requirement**: Enterprise SLAs typically mandate 99.5%–99.9% uptime. This requires automated failover for all critical infrastructure (database, message broker, cache). Circuit breakers must be implemented at the service-to-service call level, not just at the gateway. Services must handle graceful shutdown (drain connections, complete in-flight Kafka messages, refuse new requests). Health checks must be deep (verifying dependency availability) not just shallow (process alive). A runbook must exist for every failure scenario with step-by-step recovery procedures. Incident management must integrate with customer communication (status page, PagerDuty/ServiceNow).

**Gap Severity**: P0 — SLA commitments require demonstrated reliability.

**Specific Gaps**:
- No database failover (no streaming replication, no Patroni, no PgBouncer failover)
- No Kafka cluster (single broker — no replication, no failover)
- No Redis Sentinel or Redis Cluster for high availability
- No graceful shutdown (SIGTERM handling) in service code
- No circuit breaker library (e.g., resilience4j, pybreaker) in service-to-service calls
- No health check depth (services check `/health` but don't verify DB/Kafka connectivity)
- No automated recovery runbooks
- No incident management integration
- No status page for customers
- No SLA monitoring and alerting

#### Observability & Monitoring

**Current State**: Services expose basic `/health` endpoints. Logs are written to stdout (Docker container logs). No structured logging format is confirmed (JSON with correlation IDs). No centralized log aggregation (no ELK/Loki stack). No metrics collection (no Prometheus endpoints, no Grafana dashboards). No distributed tracing (no Jaeger, Zipkin, or OpenTelemetry). Alerting is not configured (Alertmanager scaffold exists but not wired). Performance baselines are not documented.

**Enterprise Requirement**: Enterprise operations require three pillars of observability: metrics (Prometheus + Grafana), logs (Loki/ELK with structured JSON + correlation IDs), and traces (OpenTelemetry → Jaeger/Tempo). Every API request must have a trace ID propagated across all service calls. Dashboards must cover: service health (up/down, latency percentiles, error rates), business KPIs (forecast accuracy, schedule adherence, procurement cycle time), resource utilization (CPU, memory, disk, connections), and tenant-level metrics (API calls per tenant, data volume per tenant). Alerting must cover: service down, error rate spike, latency degradation, disk space, queue lag, certificate expiry. Alerts must route to on-call engineers via PagerDuty or Opsgenie with escalation policies.

**Gap Severity**: P0 — impossible to operate production without observability.

**Specific Gaps**:
- No Prometheus metrics endpoints on any service
- No Grafana dashboards
- No structured logging (correlation IDs, tenant IDs, JSON format)
- No centralized log aggregation
- No distributed tracing
- No business KPI dashboards
- No alerting rules or escalation policies
- No SLO/SLI definitions
- No on-call runbook
- No customer-facing status page

#### Compliance & Data Governance

**Current State**: RLS provides tenant data isolation at the database level. No GDPR-specific features exist (no consent management, no data export API, no right-to-erasure capability). No WCAG 2.1 AA accessibility audit has been performed. No SOC 2 Type II audit has been initiated. No data retention policies are enforced. No audit logging exists for who accessed or modified what data and when. Encryption at rest is not explicitly configured (depends on PostgreSQL/OS defaults). Encryption in transit exists within Docker network but TLS termination at Kong is not confirmed for external traffic.

**Enterprise Requirement**: Enterprise customers in regulated industries (manufacturing, energy, healthcare) require: GDPR compliance (data export, deletion, consent), SOC 2 Type II (access controls, audit logging, encryption, incident response), and increasingly ISO 27001. Data must be encrypted at rest (AES-256) and in transit (TLS 1.2+). Audit logs must capture every data access and modification with user, timestamp, tenant, and action. Data retention policies must be enforceable and auditable. WCAG 2.1 AA accessibility is required for public-facing applications and increasingly for B2B. Privacy impact assessments must be documentable.

**Gap Severity**: P0 for regulated industries; P1 for general enterprise.

**Specific Gaps**:
- No GDPR data export/deletion APIs
- No consent management
- No audit logging (who did what, when, to which tenant's data)
- No data retention policy enforcement
- No encryption-at-rest configuration (explicit)
- TLS termination at Kong not confirmed for external traffic
- No WCAG 2.1 AA audit
- No SOC 2 readiness assessment
- No privacy impact assessment documentation
- No data classification framework

#### Documentation & Developer Experience

**Current State**: Documentation exists in multiple locations: `docs/`, `specs/`, `.specify/`, `README.md`. Speckit artifacts (000–011) provide feature-level specifications. Demo scripts are documented. API documentation depends on FastAPI's auto-generated OpenAPI/Swagger (likely available at `/docs` per service but not confirmed as a centralized API portal). No onboarding guide for new developers is confirmed. No API versioning strategy is documented.

**Enterprise Requirement**: Enterprise customers require: comprehensive API documentation (OpenAPI 3.0 with examples, error codes, authentication), integration guides for common ERP systems (SAP, Oracle, Odoo, Microsoft), SDK or client libraries in at least Python and JavaScript, webhook documentation for event subscriptions, a sandbox/staging environment for integration testing, and a dedicated developer portal. Internal developer experience requires: local development setup guide (< 30 minutes to running stack), architecture decision records (ADRs), runbooks for common operations, and CI/CD pipeline documentation.

**Gap Severity**: P1 — impacts developer adoption and integration partner ecosystem.

**Specific Gaps**:
- No centralized API portal (each service has its own Swagger, no unified view)
- No API versioning strategy
- No SDK or client libraries
- No webhook/event subscription documentation
- No integration partner onboarding guide
- No architecture decision records (ADR directory)
- No local development quickstart guide
- No API rate limit documentation for partners
- No sandbox/staging environment provisioning automation

#### Support & Customer Success Infrastructure

**Current State**: No support infrastructure exists. No ticketing system integration. No knowledge base. No customer health scoring. No usage analytics. No automated onboarding. No customer communication channels (in-app messaging, email).

**Enterprise Requirement**: Enterprise customers expect: dedicated support channels (email, in-app, phone for premium tiers), a knowledge base with searchable articles, ticketing system integration (Zendesk, ServiceNow, Jira Service Management), SLA tracking with automated escalation, customer health dashboards (usage trends, adoption metrics, risk indicators), onboarding workflows with milestone tracking, and a customer success team playbook. For a lean team, this can start simple (email + shared inbox) but must be planned for from day one.

**Gap Severity**: P1 — required for customer retention and expansion.

**Specific Gaps**:
- No ticketing system or support workflow
- No knowledge base
- No customer onboarding automation
- No usage analytics or health scoring
- No customer communication channels
- No SLA tracking and escalation automation
- No feedback collection mechanism

### 1.3 Gap Priority Matrix

| Gap Area | Severity | Enterprise Impact | Demo Impact | Phase |
|----------|----------|-------------------|-------------|-------|
| SSO / IdP Integration | P0 | Blocks sales | None | Phase 1 |
| Secrets Management | P0 | Security deal-breaker | None | Phase 1 |
| TLS / Encryption | P0 | Compliance requirement | None | Phase 1 |
| Audit Logging | P0 | Compliance / forensic | None | Phase 1 |
| Database HA (failover) | P0 | SLA commitment | None | Phase 2 |
| Observability (metrics/logs/traces) | P0 | Operability | None | Phase 2 |
| Graceful Shutdown | P0 | Data integrity | None | Phase 2 |
| Circuit Breakers | P0 | Reliability | None | Phase 2 |
| Kubernetes Deployment | P0 | Scalability (SaaS) | None | Phase 2 |
| GDPR Compliance | P1 | Regulatory markets | None | Phase 3 |
| WCAG 2.1 AA | P1 | Public sector, accessibility law | None | Phase 3 |
| API Portal & Versioning | P1 | Partner ecosystem | Minor | Phase 3 |
| Customer Support Infra | P1 | Retention | None | Phase 4 |
| Automated Onboarding | P2 | Scale | None | Phase 4 |
| SDK / Client Libraries | P2 | Developer adoption | None | Phase 4 |

---

## 2. Enterprise Readiness Checklist

This checklist defines the non-negotiable requirements for production deployment. Every item must be verified and signed off before a customer-facing go-live. Items are grouped by domain and tagged with the target phase.

### 2.1 Infrastructure

- [ ] **INF-001**: Kubernetes cluster provisioned (EKS/AKS/GKE or on-premise k3s/rancher) with node pools for compute, memory-optimized (planning), and monitoring workloads
- [ ] **INF-002**: All 22+ services deployed as Kubernetes Deployments with resource limits (CPU/memory requests and limits) defined
- [ ] **INF-003**: Horizontal Pod Autoscaler (HPA) configured for all stateless services (minimum 2 replicas for production)
- [ ] **INF-004**: Pod Disruption Budget (PDB) set to ensure at least 1 replica available during disruptions
- [ ] **INF-005**: PostgreSQL deployed as a managed service (RDS, Cloud SQL, or Patroni on k8s) with primary + read replica, automated backups (daily, 30-day retention), point-in-time recovery enabled
- [ ] **INF-006**: Kafka deployed as a 3-broker cluster (MSK, Confluent, or Strimzi on k8s) with replication factor 3, min.insync.replicas 2, and retention policy configured per topic
- [ ] **INF-007**: Redis deployed in Sentinel mode (3 sentinels + 1 master + 1 replica minimum) or Redis Cluster mode for high availability
- [ ] **INF-008**: Kong gateway deployed with TLS termination (valid SSL certificate, TLS 1.2+ only), rate limiting per tenant, and request/response size limits
- [ ] **INF-009**: Ingress controller configured with proper health checks, connection timeouts, and WebSocket support if needed
- [ ] **INF-010**: Persistent volumes configured for PostgreSQL data, Kafka data, and any file storage (Separate storage classes for performance tiers)
- [ ] **INF-011**: Network policies defined to restrict service-to-service communication (only allowed connections, zero-trust within cluster)
- [ ] **INF-012**: DNS and TLS certificates managed via cert-manager with automatic renewal
- [ ] **INF-013**: Container registry (ECR, GCR, or Harbor) with image scanning enabled (Trivy, Snyk, or AWS Inspector)
- [ ] **INF-014**: Environment separation: development, staging, production with identical deployment manifests (parameterized via Helm values or Kustomize overlays)

### 2.2 Security

- [ ] **SEC-001**: Keycloak (or customer IdP via SAML 2.0/OIDC) integrated as the authentication authority — local JWT disabled in production
- [ ] **SEC-002**: All secrets (database passwords, API keys, encryption keys, OAuth client secrets) stored in HashiCorp Vault or AWS Secrets Manager — zero secrets in environment variables, ConfigMaps, or container images
- [ ] **SEC-003**: Secret rotation automated (database credentials rotate every 90 days, API keys rotate every 30 days or on compromise detection)
- [ ] **SEC-004**: JWT signing uses RS256 with key pair managed by Vault — private key never leaves Vault transit engine
- [ ] **SEC-005**: Token lifetime: access token 15 minutes, refresh token 24 hours, idle timeout 8 hours, absolute timeout 12 hours
- [ ] **SEC-006**: MFA enforced for all admin and planner roles; optional for viewer roles
- [ ] **SEC-007**: RBAC roles configurable per tenant (admin can create custom roles, assign permissions granularly)
- [ ] **SEC-008**: API rate limiting per tenant (configurable: default 1000 req/min, burst 100 req/sec)
- [ ] **SEC-009**: All inter-service communication within the cluster uses mTLS (cert-manager + service mesh or sidecar pattern)
- [ ] **SEC-010**: RLS policies verified on every table with tenant_id — penetration test confirms no cross-tenant data leakage
- [ ] **SEC-011**: SQL injection prevention verified (all queries use parameterized/ORM; no f-string SQL)
- [ ] **SEC-012**: XSS prevention verified (React auto-escaping confirmed; no dangerouslySetInnerHTML with user input)
- [ ] **SEC-013**: CSRF protection enabled on all state-changing endpoints
- [ ] **SEC-014**: Security headers configured: Content-Security-Policy, X-Frame-Options DENY, X-Content-Type-Options nosniff, Strict-Transport-Security
- [ ] **SEC-015**: Dependency vulnerability scanning in CI/CD (Snyk/Dependabot) with critical-high vulnerabilities blocking merge
- [ ] **SEC-016**: Penetration test completed by independent third party — all critical/high findings resolved before go-live

### 2.3 Data Handling

- [ ] **DAT-001**: All data encrypted at rest (AES-256) — verified for PostgreSQL (TDE or disk encryption), Kafka (encryption at rest), Redis (disk encryption), and object storage
- [ ] **DAT-002**: All data encrypted in transit (TLS 1.2+) — verified for external traffic (Kong), internal service-to-service (mTLS), database connections (SSL mode verify-full), and Kafka (TLS)
- [ ] **DAT-003**: Database backups encrypted and stored in a separate region/account
- [ ] **DAT-004**: Tenant data isolation verified: RLS policies on all tables, API gateway enforces X-Tenant-ID, Kafka messages scoped by tenant_id, no shared caches without tenant scoping
- [ ] **DAT-005**: Data retention policies defined and enforced (e.g., audit logs retained 2 years, planning history 1 year, raw Kafka events 7 days, aggregates indefinitely)
- [ ] **DAT-006**: GDPR data export API: `GET /api/v1/tenant/{id}/data-export` — generates downloadable archive of all tenant data
- [ ] **DAT-007**: GDPR right-to-erasure API: `DELETE /api/v1/tenant/{id}/data` — soft-deletes all tenant data with hard-delete after retention period
- [ ] **DAT-008**: Data classification framework defined (Public, Internal, Confidential, Restricted) with handling rules for each class
- [ ] **DAT-009**: Database connection pooling configured (PgBouncer) with per-tenant connection limits to prevent noisy-neighbor
- [ ] **DAT-010**: Large dataset handling: pagination on all list endpoints (cursor-based, not offset), streaming responses for bulk exports, batch processing for imports (> 10K records)

### 2.4 Uptime & Reliability

- [ ] **REL-001**: SLA defined and contractually committed: 99.5% (standard) or 99.9% (premium)
- [ ] **REL-002**: Automated failover tested for PostgreSQL (trigger primary failover, verify < 30s switchover)
- [ ] **REL-003**: Automated failover tested for Kafka (kill a broker, verify producer/consumer recovery < 60s)
- [ ] **REL-004**: Automated failover tested for Redis (kill master, verify sentinel promotion < 30s)
- [ ] **REL-005**: Circuit breaker implemented on all synchronous inter-service calls (threshold: 50% failure rate over 10 requests, open circuit 30s, half-open test 1 request)
- [ ] **REL-006**: Graceful shutdown implemented in all services (SIGTERM handler: stop accepting new requests, drain in-flight Kafka messages, close DB connections, then exit)
- [ ] **REL-007**: Rolling deployment tested (deploy new version while serving traffic — zero dropped requests)
- [ ] **REL-008**: Database migration strategy for zero-downtime (backward-compatible migrations, expand-contract pattern for schema changes)
- [ ] **REL-009**: Chaos testing automated in staging (weekly chaos run: pod kill, network partition, disk full, CPU stress, memory pressure)
- [ ] **REL-010**: Recovery procedures documented and tested for every failure scenario

### 2.5 Monitoring & Observability

- [ ] **OBS-001**: Prometheus deployed with service discovery for all IPE services
- [ ] **OBS-002**: Every service exposes `/metrics` endpoint with: request count, latency histogram (p50/p95/p99), error count by code, active connections, Kafka consumer lag, DB connection pool usage
- [ ] **OBS-003**: Grafana deployed with dashboards: System Overview, Per-Service Health, API Gateway, Database, Kafka, Tenant Usage, Business KPIs
- [ ] **OBS-004**: Structured logging: all logs in JSON format with fields: timestamp, level, service, trace_id, span_id, tenant_id, user_id, request_id, message, context
- [ ] **OBS-005**: Centralized log aggregation (Loki or ELK) with 30-day hot retention, 1-year cold storage
- [ ] **OBS-006**: Distributed tracing: OpenTelemetry SDK integrated in all services, traces propagated via Kafka and HTTP headers, trace backend (Jaeger or Tempo) deployed
- [ ] **OBS-007**: Alerting rules defined and operational:
  - Service down (immediate — P1)
  - Error rate > 5% over 5 minutes (P1)
  - p95 latency > 2s over 5 minutes (P2)
  - Kafka consumer lag > 1000 messages (P2)
  - Database connection pool > 80% utilization (P2)
  - Disk usage > 80% (P2)
  - Certificate expiry < 14 days (P3)
- [ ] **OBS-008**: Alerts route to PagerDuty or Opsgenie with escalation policy (L1 on-call → L2 after 15min → engineering manager after 30min)
- [ ] **OBS-009**: SLO/SLI defined and tracked: availability SLO (99.5%), latency SLO (p95 < 500ms for reads, < 5s for planning ops), error rate SLO (< 1%)
- [ ] **OBS-010**: Customer-facing status page deployed (e.g., Instatus, Statuspage) with automated incident creation

### 2.6 Compliance

- [ ] **CMP-001**: SOC 2 Type II audit initiated with a qualified auditor — Type I gap assessment completed
- [ ] **CMP-002**: GDPR compliance: privacy policy published, data processing agreement (DPA) template, consent management, data export/erasure APIs functional
- [ ] **CMP-003**: WCAG 2.1 AA audit completed — all critical and major violations resolved
- [ ] **CMP-004**: Audit logging functional: every API request logged with user_id, tenant_id, action, resource, timestamp, IP, user_agent
- [ ] **CMP-005**: Data retention policies implemented and auditable (automated purge jobs with audit trail)
- [ ] **CMP-006**: Incident response plan documented: detection, containment, eradication, recovery, communication, post-incident review
- [ ] **CMP-007**: Vulnerability management process: weekly dependency scans, monthly infrastructure scans, annual penetration tests
- [ ] **CMP-008**: Business continuity plan (BCP) and disaster recovery (DR) plan documented and tested

---

## 3. Competitive Positioning Analysis

### 3.1 Competitive Landscape

IPE competes in the AI-powered supply chain planning market. The primary competitive reference point is SAP Integrated Business Planning (IBP), augmented by SAP Joule for AI copilot capabilities. Secondary competitors include o9 Solutions, Blue Yonder (Luminate), Kinaxis RapidResponse, and Anaplan. The competitive analysis below focuses on SAP IBP as the primary benchmark because it represents the market incumbent that IPE's customers (currently Star Trans in the transformer manufacturing sector) are most likely evaluating as an alternative.

### 3.2 SAP IBP Capability Comparison

| Capability | SAP IBP | IPE Current | Gap | Priority |
|---|---|---|---|---|
| **Demand Planning** | Statistical + ML forecasting, demand sensing from POS/external signals, consensus demand planning | SES + Prophet + LSTM forecasters, demand signals from API/Odoo, no external signal ingestion (POS, weather, social) | External demand signals, consensus workflow | P1 |
| **Supply Planning** | Multi-echelon inventory optimization, constrained supply planning, safety stock optimization | Supply network modeling (facilities, lanes), safety stock calculation, no multi-echelon optimization | Multi-echelon optimization, constrained planning | P1 |
| **Response & S&OP** | What-if scenario planning, consensus S&OP process, executive dashboards, financial integration | Scenario workbench (scenario-svc), executive dashboards, no S&OP consensus workflow, no financial planning integration | S&OP workflow, financial integration | P2 |
| **Inventory** | Inventory optimization, DRP (Distribution Requirements Planning), multi-echelon visibility | Stock level tracking, safety stock, no DRP, limited multi-echelon | DRP, multi-echelon inventory | P2 |
| **Demand Sensing** | Real-time POS data, weather, social media signals, ML-powered short-term adjustment | No real-time external signal ingestion | Entire feature | P2 |
| **AI Copilot** | SAP Joule: natural language planning, role-based assistants, embedded AI actions | NLP service scaffold, Copilot role agents (planner, manager, supervisor, executive) require hybrid stack + Ollama — not production | Production-grade copilot, no LLM dependency on local Ollama | P1 |
| **Collaboration** | S&OP process workflow, approval chains, commentary, version control | No workflow engine, no approval chains, no collaboration features | Workflow engine, approval system | P2 |
| **Integration** | Native SAP S/4HANA integration, pre-built connectors for major ERPs, EDI support | Odoo 19 live (connector), SAP/D365 scaffolds only, no EDI | SAP/D365 live connectors, EDI | P1 |
| **Platform** | SAP BTP (cloud), on-premise option, mobile app, embedded analytics | Self-hosted Docker, no mobile app, React web UI, no embedded analytics platform | Mobile, embedded analytics, cloud deployment | P3 |
| **Security** | SOC 2, ISO 27001, GDPR, FedRAMP, SAP Trust Center | RLS tenant isolation, local JWT, no certifications | All compliance certifications | P0 |
| **Scalability** | Enterprise-grade, handles billions of rows, global deployments | Single-host Docker, no horizontal scaling, no benchmarks at scale | Horizontal scaling, performance benchmarks | P0 |

### 3.3 IPE Competitive Advantages

Despite the gaps, IPE has structural advantages over SAP IBP that should be leveraged in positioning:

**Speed of deployment**: SAP IBP implementations typically take 6–18 months with significant professional services engagement. IPE can be deployed and generating value within 2–4 weeks for a mid-market manufacturer. This is a decisive advantage for customers frustrated with SAP implementation timelines and cost overruns.

**Cost structure**: SAP IBP pricing is based on named users with significant per-user licensing costs. IPE's architecture supports usage-based or tenant-based pricing without per-user limits, making it dramatically more cost-effective for organizations with many planners and stakeholders.

**Flexibility and customization**: SAP IBP is a proprietary platform with limited customization options — customers adapt their processes to SAP's model. IPE's microservice architecture allows deep customization per industry vertical (transformer manufacturing at Star Trans is already a proven vertical template) without modifying core platform code.

**AI-native architecture**: SAP IBP layers AI on top of a legacy planning engine. IPE is designed AI-first — every service can consume ML predictions, and the architecture supports multiple LLM backends (Ollama for on-premise, OpenRouter/NVIDIA for cloud). This makes IPE more adaptable to emerging AI capabilities.

**Modern technology stack**: SAP IBP runs on SAP HANA (proprietary in-memory database) and SAP BTP (proprietary PaaS). IPE runs on open-source components (PostgreSQL, Kafka, Redis, FastAPI, React) that customers can inspect, audit, and self-manage. This resonates with CTOs who want technology transparency and avoid vendor lock-in.

### 3.4 Competitive Gap Prioritization

To win enterprise deals against SAP IBP, IPE must close these gaps in priority order:

**Immediate (Phase 1–2)**: Security posture (SSO, secrets, encryption, audit logs), infrastructure reliability (Kubernetes, database HA, observability), and live ERP connectors (SAP S/4HANA, Microsoft D365). These are table stakes — every enterprise RFP will require them.

**Short-term (Phase 3)**: S&OP workflow and collaboration features (currently absent, SAP excels here), multi-echelon optimization (SAP's core differentiator), and external demand signal integration (POS, weather). These are feature differentiators that enterprise buyers evaluate in POCs.

**Medium-term (Phase 4)**: Mobile application, embedded analytics platform, cloud-native deployment option (managed SaaS). These expand the addressable market and reduce friction in procurement processes.

---

## 4. Phased Roadmap

### Phase 0: Foundation Hardening (Weeks 1–4)
**Pre-requisite**: Current demo must be stabilized before any enterprise work begins.

**Business Objective**: Establish the non-negotiable security and infrastructure foundation that blocks all enterprise conversations. No customer will proceed past security review without SSO, secrets management, encryption, and audit logging.

**Key Deliverables**:
- Keycloak SSO integrated (SAML 2.0 + OIDC)
- HashiCorp Vault for secrets management
- TLS everywhere (external + internal mTLS)
- Audit logging framework
- Structured logging (JSON + correlation IDs)
- RLS verification (penetration test for tenant isolation)

**Success Metrics**:
- Keycloak login/logout flow functional with 3 test IdPs (Azure AD, Okta, Google)
- Zero secrets in environment variables or code (verified by automated scan)
- All inter-service traffic encrypted (verified by network packet capture)
- Audit log captures 100% of API requests with user, tenant, action, timestamp
- Tenant isolation penetration test: zero cross-tenant data access

**Dependencies**: HashiCorp Vault instance (cloud or self-hosted), Keycloak instance, SSL certificates, IdP test accounts.

**Risks**: Keycloak configuration complexity; Vault integration may require refactoring how services read configuration; mTLS may impact Kafka performance.

### Phase 1: Operational Readiness (Weeks 5–10)
**Business Objective**: Make the platform operable in production by a small team. This means full observability, automated deployments, and documented runbooks so that one engineer can keep the system running.

**Key Deliverables**:
- Kubernetes manifests (Helm chart) for all services
- Prometheus + Grafana monitoring stack
- Loki log aggregation
- OpenTelemetry distributed tracing
- CI/CD pipeline (GitHub Actions / GitLab CI)
- Automated database migrations in CI/CD
- Health checks upgraded to deep checks (dependency verification)
- Graceful shutdown in all services
- Circuit breakers on inter-service calls
- Incident response runbook

**Success Metrics**:
- `helm install ipe ./charts/ipe` deploys the full stack to a fresh Kubernetes cluster
- Grafana dashboards visible within 5 minutes of deployment
- CI/CD: PR merged → tests pass → image built → staging deployed in < 15 minutes
- Deep health check detects database failure within 10 seconds
- Graceful shutdown: zero dropped requests during rolling deployment (verified by load test)
- Circuit breaker: when a dependency is down, upstream returns 503 (not timeout) within 5 seconds

**Dependencies**: Kubernetes cluster (EKS/AKS/GKE or on-premise), container registry, CI/CD runner, PagerDuty/Opsgenie account.

**Risks**: Kubernetes learning curve; Helm chart complexity with 22+ services; OpenTelemetry instrumentation effort across all services; CI/CD pipeline flakiness.

### Phase 2: Enterprise Feature Parity (Weeks 11–18)
**Business Objective**: Close the feature gaps that enterprise buyers will evaluate in POCs against SAP IBP. This phase makes IPE competitive in head-to-head evaluations.

**Key Deliverables**:
- SAP S/4HANA live connector (replacing scaffold)
- Microsoft Dynamics 365 live connector (replacing scaffold)
- S&OP collaboration workflow (approval chains, commentary, version control)
- Consensus demand planning workflow (multi-stakeholder forecast review)
- Multi-echelon inventory optimization algorithm
- External demand signal ingestion (REST API for POS, weather, social data providers)
- Copilot agents production-ready (cloud LLM backend — OpenRouter/NVIDIA, not local Ollama dependency)
- API versioning (v1/v2 coexistence)
- Tenant self-service admin portal (create tenant, configure IdP, manage roles, view usage)

**Success Metrics**:
- SAP S/4HANA connector: bi-directional sync of 5 core entities (products, orders, inventory, BOMs, production orders) verified with SAP sandbox
- D365 connector: same 5 entities verified with D365 sandbox
- S&OP workflow: a multi-user planning cycle (create plan, share, comment, revise, approve) completes end-to-end
- Multi-echelon optimization: produces allocation recommendations for a 3-echelon network (plant → DC → customer) with measurable inventory cost reduction vs. single-echelon
- Copilot: responds to natural language planning queries in < 5 seconds with actionable recommendations
- API versioning: v1 endpoints continue working when v2 is deployed (backward compatibility verified)

**Dependencies**: SAP S/4HANA sandbox instance, D365 sandbox instance, LLM API keys (OpenRouter/NVIDIA), UX design for S&OP workflow.

**Risks**: SAP connector complexity (SAP API is notoriously complex); LLM cost management; S&OP workflow scope creep; multi-echelon algorithm accuracy validation.

### Phase 3: Scale & Compliance (Weeks 19–26)
**Business Objective**: Make the platform scalable for multi-tenant SaaS deployment and compliant for regulated industries. This unlocks the largest addressable market.

**Key Deliverables**:
- Horizontal scaling: HPA policies for all stateless services, load testing at 500+ concurrent users
- Database read replicas for reporting workloads
- Kafka consumer group rebalancing tested at scale
- GDPR compliance: data export API, right-to-erasure API, consent management UI, privacy policy
- WCAG 2.1 AA remediation (accessibility audit findings resolved)
- SOC 2 Type I audit completed
- Automated chaos testing in staging (weekly)
- Performance baselines documented and enforced in CI/CD (regression detection)
- Tenant resource isolation (CPU/memory limits per tenant, connection pool limits, storage quotas)

**Success Metrics**:
- Load test: 500 concurrent users, p95 < 500ms for reads, p95 < 5s for planning ops, zero errors
- Database: read replica handles 80% of read queries, primary CPU < 60%
- GDPR: data export generates complete archive in < 10 minutes for a tenant with 1M records
- WCAG 2.1 AA: zero critical/major violations
- SOC 2 Type I: auditor issues zero critical findings
- Chaos test: system recovers to full functionality within 60 seconds of any single service failure
- CI/CD: performance regression test blocks merge if p95 degrades > 20%

**Dependencies**: Load testing infrastructure (k6 cluster), SOC 2 auditor engagement, accessibility auditor, larger Kubernetes cluster for scale testing.

**Risks**: Scale testing may reveal architectural bottlenecks requiring rearchitecting; SOC 2 audit scope may expand; WCAG remediation may require significant frontend rework.

### Phase 4: Go-to-Market & Growth (Weeks 27–36)
**Business Objective**: Make the platform sellable and supportable at scale. This phase builds the commercial and operational infrastructure around the product.

**Key Deliverables**:
- Customer self-service onboarding (sign up → provision tenant → configure IdP → guided setup → first forecast in < 1 hour)
- Managed SaaS deployment option (one-click provision via Terraform/Pulumi)
- API developer portal (centralized OpenAPI docs, SDK downloads, sandbox access, rate limit dashboard)
- Python and JavaScript SDKs for IPE API
- Knowledge base (50+ articles covering common tasks, integration guides, troubleshooting)
- Customer health dashboard (usage trends, adoption metrics, at-risk indicators)
- Billing integration (Stripe live mode — metered usage, per-tenant invoicing)
- Mobile-responsive web application (full functionality on tablet, core functionality on mobile)
- On-premise deployment guide and automation (Ansible/Terraform for air-gapped deployment)
- Partner integration program (certified connector framework, partner SDK, co-marketing)

**Success Metrics**:
- Self-service onboarding: new customer creates account and generates first forecast in < 60 minutes without human assistance
- SaaS deployment: `terraform apply` provisions full IPE stack in < 30 minutes
- API portal: developer can find documentation, generate API key, make first API call in < 10 minutes
- Knowledge base: covers 90% of support ticket categories (measured by deflect rate)
- Billing: Stripe correctly meters and invoices based on usage (API calls, data volume, user seats)
- Mobile: all planning dashboards and approval workflows functional on iPad; forecast view and alerts on iPhone

**Dependencies**: Stripe production account, documentation platform (GitBook/ReadMe), Terraform Cloud or Pulumi, marketing website, customer support team (even if 1 person initially).

**Risks**: Self-service onboarding UX complexity; billing accuracy; mobile responsiveness may require frontend framework adjustment; partner program governance overhead.

---

## 5. Sprint Breakdown

### Phase 0 — Sprint 0.1 (Weeks 1–2): Security Foundation

**Sprint Goal**: Replace all local/demo authentication and secret handling with enterprise-grade SSO and vault integration.

| # | Task | Effort | Acceptance Criteria | Owner |
|---|------|--------|---------------------|-------|
| 1 | Deploy Keycloak in Docker/ Kubernetes alongside IPE stack | 4h | Keycloak accessible at `/auth`, admin console functional | DevOps |
| 2 | Configure Keycloak realm for IPE with OIDC and SAML 2.0 | 4h | Realm created with client for IPE, mapper for tenant_id and roles | Backend |
| 3 | Replace dpe-svc JWT issuance with Keycloak token validation | 8h | Login returns Keycloak JWT; dpe-svc validates it; existing RBAC roles mapped from Keycloak groups | Backend |
| 4 | Deploy HashiCorp Vault (dev mode initially) | 2h | Vault accessible, unseal functional, root token available | DevOps |
| 5 | Create Vault secret engine (KV v2) with IPE secret hierarchy | 3h | Secrets organized: `ipe/secret/<tenant_id>/db_password`, `ipe/secret/<tenant_id>/api_key`, etc. | Backend |
| 6 | Integrate Vault agent or sidecar with each service's Docker container | 6h | Services read secrets from Vault (via env or file mount), NOT from .env files | Backend |
| 7 | Refactor `config/secrets_manager.py` from stub to Vault client | 4h | `secrets_manager.get_secret("db_password", tenant_id="startrans")` returns value from Vault | Backend |
| 8 | Migrate all hardcoded secrets to Vault (DB passwords, API keys, JWT signing key) | 3h | `grep -r "password\|api_key\|secret" services/ --include="*.py" | grep -v "secrets_manager\|vault"` returns zero hits | Backend |
| 9 | Configure TLS termination at Kong (generate self-signed cert for dev, Let's Encrypt for staging) | 3h | `curl https://localhost:8443/health` returns 200 with valid certificate | DevOps |
| 10 | Configure mTLS between services via Kubernetes service mesh (Istio) or direct cert injection | 8h | `tcpdump` between two services shows TLS handshake, no plaintext | DevOps |
| 11 | Implement audit logging middleware (log every API request to audit_log table) | 6h | Every request to Kong results in a row in `audit_log` with user_id, tenant_id, method, path, status_code, timestamp, ip | Backend |
| 12 | Create Alembic migration for audit_log table with RLS | 2h | Table created, RLS policy ensures tenant isolation | Backend |
| 13 | Test complete auth flow: Keycloak login → JWT → API call → audit log | 3h | End-to-end test passes with all components verified | QA |

**Sprint total**: ~56 hours (~1.4 FTEs for 2 weeks)  
**Blockers**: Keycloak realm configuration complexity; Vault network policies in Kubernetes; mTLS certificate management.

### Phase 0 — Sprint 0.2 (Weeks 3–4): Security Verification & Documentation

**Sprint Goal**: Verify security implementation, fix vulnerabilities, and document the security architecture.

| # | Task | Effort | Acceptance Criteria | Owner |
|---|------|--------|---------------------|-------|
| 1 | Tenant isolation penetration test (automated script) | 6h | Script attempts 20 cross-tenant access scenarios — all blocked by RLS + auth | QA |
| 2 | SQL injection automated test (SQLMap or custom scanner against all endpoints) | 4h | Zero SQL injection vulnerabilities | QA |
| 3 | XSS automated test (OWASP ZAP or custom scanner) | 4h | Zero XSS vulnerabilities | QA |
| 4 | Security headers verification (all responses have CSP, X-Frame-Options, HSTS, etc.) | 2h | Security header scan returns A rating | QA |
| 5 | Dependency vulnerability scan (Snyk/Trivy) — fix all critical findings | 4h | Zero critical/high vulnerabilities in production dependencies | Backend |
| 6 | Implement JWT RS256 signing via Vault transit engine | 4h | JWT signed with RS256, public key distributed via JWKS endpoint | Backend |
| 7 | Token refresh flow: implement refresh token rotation | 4h | Access token expires in 15min, refresh token rotation works, old refresh tokens invalidated | Backend |
| 8 | MFA setup for admin role (TOTP via Keycloak) | 3h | Admin users required to set up TOTP; login requires TOTP code | Backend |
| 9 | RBAC per-tenant configuration: admin can create custom roles | 8h | Tenant admin can create role, assign permissions, assign to users — all enforced on API calls | Backend |
| 10 | API rate limiting per tenant in Kong (configurable via admin API) | 4h | Rate limit enforced; 429 returned when exceeded; configurable per tenant | Backend |
| 11 | Write Security Architecture ADR (ADR-003: Enterprise Authentication) | 2h | ADR documents Keycloak choice, JWT flow, RBAC model, MFA policy | Architect |
| 12 | Write Incident Response Runbook (security incidents) | 3h | Runbook covers: suspected breach, credential compromise, data leak, DDoS response | Architect |

**Sprint total**: ~48 hours (~1.2 FTEs for 2 weeks)  
**Blockers**: Pen test may reveal unexpected RLS gaps; RBAC per-tenant may require schema changes; MFA UX impact on demo.

### Phase 1 — Sprint 1.1 (Weeks 5–6): Kubernetes & CI/CD

**Sprint Goal**: Deploy IPE on Kubernetes with automated CI/CD pipeline.

| # | Task | Effort | Acceptance Criteria | Owner |
|---|------|--------|---------------------|-------|
| 1 | Create Helm chart structure: Chart.yaml, values.yaml, templates/ for all services | 12h | `helm lint ./charts/ipe` passes; all 22+ services defined as Deployments | DevOps |
| 2 | Create Kubernetes manifests for PostgreSQL (primary + replica) | 4h | StatefulSet with 2 replicas, connection pooling via PgBouncer sidecar | DevOps |
| 3 | Create Kubernetes manifests for Kafka (3-broker Strimzi or plain StatefulSet) | 4h | 3-broker Kafka cluster with topic auto-creation, replication factor 3 | DevOps |
| 4 | Create Kubernetes manifests for Redis (Sentinel mode) | 3h | 1 master + 1 replica + 3 sentinels, automatic failover tested | DevOps |
| 5 | Configure Kubernetes Ingress for Kong with TLS | 3h | External HTTPS traffic reaches Kong via Ingress; TLS certificate managed by cert-manager | DevOps |
| 6 | Set up container registry (ECR/GCR/Harbor) with image scanning | 2h | `docker push` works; Trivy scan runs on every push; critical findings block deployment | DevOps |
| 7 | Create GitHub Actions CI pipeline: lint → test → build → push image | 6h | PR triggers pipeline; all steps complete in < 10 minutes; test failure blocks merge | DevOps |
| 8 | Create GitHub Actions CD pipeline: staging deploy on merge to main | 4h | Merge to main → image deployed to staging Kubernetes cluster automatically | DevOps |
| 9 | Configure Helm values for dev/staging/prod environments (Kustomize or values files) | 4h | `helm install -f values-staging.yaml` and `helm install -f values-prod.yaml` produce correct configurations | DevOps |
| 10 | Test full deployment: `helm install ipe ./charts/ipe -f values-staging.yaml` | 4h | All services healthy, Kong routes working, demo script passes on Kubernetes | QA |

**Sprint total**: ~46 hours (~1.15 FTEs for 2 weeks)  
**Blockers**: Helm chart complexity with 22+ services; Kafka on Kubernetes (Strimzi learning curve); CI/CD pipeline flakiness.

### Phase 1 — Sprint 1.2 (Weeks 7–8): Observability Stack

**Sprint Goal**: Deploy full observability (metrics, logs, traces) and upgrade health checks.

| # | Task | Effort | Acceptance Criteria | Owner |
|---|------|--------|---------------------|-------|
| 1 | Deploy Prometheus with Kubernetes service discovery | 3h | Prometheus scraping all IPE service `/metrics` endpoints; targets page shows all services UP | DevOps |
| 2 | Add Prometheus client library to all 22 services; expose `/metrics` | 12h | Every service exposes: request_count, request_latency_seconds (histogram), error_count, active_requests, db_pool_size, kafka_consumer_lag | Backend |
| 3 | Deploy Grafana with provisioning (dashboards as code) | 4h | 4 dashboards provisioned: System Overview, Per-Service Health, API Gateway, Database | DevOps |
| 4 | Create Grafana dashboards: Tenant Usage, Business KPIs | 6h | Dashboard shows: API calls per tenant, forecast accuracy, schedule adherence, alerts per tenant | DevOps |
| 5 | Deploy Loki for log aggregation | 3h | All service logs ingested by Loki; queryable via LogQL | DevOps |
| 6 | Add structured JSON logging to all services (loguru or structlog) | 8h | Every log line is JSON with: timestamp, level, service, trace_id, tenant_id, user_id, message | Backend |
| 7 | Integrate OpenTelemetry SDK in all services (auto-instrumentation + manual spans) | 10h | Trace propagated across service calls; visible in Jaeger/Tempo; parent-child span relationships correct | Backend |
| 8 | Deploy Jaeger or Tempo as trace backend | 2h | Trace UI accessible; can query traces by trace_id, service, operation, tags | DevOps |
| 9 | Upgrade all service health checks to "deep" (verify DB + Kafka + Redis connectivity) | 6h | Health endpoint returns 503 with dependency status when any dependency is down (not just process alive) | Backend |
| 10 | Implement graceful shutdown (SIGTERM handler) in all services | 8h | `kubectl delete pod` → service stops accepting new requests, completes in-flight work, exits cleanly with zero errors | Backend |
| 11 | Configure alerting rules in Prometheus (5 rules from OBS-007) | 4h | Rules fire correctly; alerts sent to Alertmanager | DevOps |
| 12 | Wire Alertmanager to PagerDuty/Opsgenie | 2h | Alert → PagerDuty incident created → on-call engineer notified | DevOps |

**Sprint total**: ~68 hours (~1.7 FTEs for 2 weeks)  
**Blockers**: OpenTelemetry instrumentation across 22 services is labor-intensive; structured logging migration may break existing log parsing; trace context propagation through Kafka requires consumer/producer configuration.

### Phase 1 — Sprint 1.3 (Weeks 9–10): Reliability Engineering

**Sprint Goal**: Implement circuit breakers, rolling deployment verification, and chaos testing automation.

| # | Task | Effort | Acceptance Criteria | Owner |
|---|------|--------|---------------------|-------|
| 1 | Implement circuit breaker library (pybreaker or resilience4j equivalent) | 4h | Circuit breaker class with configurable threshold, timeout, half-open state | Backend |
| 2 | Add circuit breaker to all synchronous inter-service HTTP calls | 8h | When downstream is down, circuit opens in < 10 seconds; returns 503 immediately; recovers automatically | Backend |
| 3 | Implement retry with exponential backoff for transient failures | 4h | 5xx responses retried 3 times with 1s/2s/4s backoff; 4xx NOT retried | Backend |
| 4 | Test rolling deployment with zero downtime (kill pods while load test runs) | 4h | Load test shows zero failed requests during `helm upgrade` | QA |
| 5 | Create zero-downtime database migration guide and verify expand-contract pattern | 4h | Migration that adds a column does not break running services; documented pattern for future migrations | Backend |
| 6 | Automate chaos testing script (pod kill, network partition, CPU stress) | 8h | `./scripts/run-chaos-k8s.sh` runs C1-C6 on Kubernetes, captures results, generates report | QA |
| 7 | Schedule weekly chaos test in staging (GitHub Actions cron) | 2h | Chaos test runs every Monday 6AM; results posted to Slack/channel | DevOps |
| 8 | Write operational runbook: how to diagnose and recover from each failure type | 6h | Runbook covers: service crash, DB failover, Kafka broker loss, Redis failover, disk full, OOM | Architect |
| 9 | Test database failover: kill primary, verify replica promotion, verify app recovery | 3h | Application reconnects to new primary within 30 seconds; zero data loss | QA |
| 10 | Test Kafka broker failure: kill one broker, verify producer/consumer recovery | 2h | Producers continue publishing; consumers rebalance and resume within 60 seconds | QA |

**Sprint total**: ~45 hours (~1.1 FTEs for 2 weeks)  
**Blockers**: Circuit breaker configuration tuning (too aggressive = false positives, too lenient = real outages propagate); chaos testing may uncover deeper architectural issues that need fixing before proceeding.

### Phase 2 — Sprint 2.1 (Weeks 11–12): Live ERP Connectors

**Sprint Goal**: Replace SAP and D365 connector scaffolds with functional live connectors.

| # | Task | Effort | Acceptance Criteria | Owner |
|---|------|--------|---------------------|-------|
| 1 | SAP S/4HANA connector: implement OData API client (read products, orders, BOMs, inventory, production orders) | 16h | 5 entity types read from SAP sandbox; data transformed to IPE CDM format | Integration |
| 2 | SAP connector: implement write-back (push forecasts, procurement recs, schedule adjustments to SAP) | 12h | IPE demand forecast creates/updates SAP demand plan; procurement rec creates SAP purchase requisition | Integration |
| 3 | D365 connector: implement Dataverse/Web API client (same 5 entities) | 14h | 5 entity types read from D365 sandbox; data transformed to IPE CDM format | Integration |
| 4 | D365 connector: implement write-back (same 3 operations) | 10h | IPE recommendations pushed to D365 as draft records | Integration |
| 5 | Connector health monitoring: each connector reports sync status, lag, error count | 4h | Kong endpoint `/erp/sap/status` and `/erp/d365/status` return live sync metrics | Backend |
| 6 | Connector error handling: dead-letter queue for failed sync records, retry logic, alerting | 6h | Failed sync records go to DLQ; retried 3 times; alert if DLQ > 100 records | Backend |
| 7 | Integration test: end-to-end SAP flow (SAP SO → IPE demand → forecast → SAP) | 6h | Automated test creates SO in SAP, verifies it appears in IPE, verifies forecast generated, verifies push-back | QA |
| 8 | Integration test: end-to-end D365 flow | 6h | Same flow for D365 | QA |
| 9 | Documentation: SAP integration guide, D365 integration guide, connector troubleshooting | 4h | Guide covers: setup, configuration, sync schedule, error resolution, data mapping | Tech Writer |

**Sprint total**: ~78 hours (~1.95 FTEs for 2 weeks)  
**Blockers**: SAP OData API complexity and authentication (SAP certificates, OAuth2 client credentials flow); D365 API pagination and throttling; SAP sandbox availability; data mapping edge cases (SAP units of measure vs. IPE, SAP date formats, etc.).

### Phase 2 — Sprint 2.2 (Weeks 13–14): S&OP Workflow & Copilot

**Sprint Goal**: Implement S&OP collaboration workflow and production-grade AI Copilot.

| # | Task | Effort | Acceptance Criteria | Owner |
|---|------|--------|---------------------|-------|
| 1 | Design S&OP workflow data model (plan versions, comments, approvals, status machine) | 6h | Model supports: create draft → share → comment → revise → submit for approval → approve/reject → publish | Backend |
| 2 | Implement S&OP backend API (plan CRUD, versioning, comments, approval actions) | 12h | All API endpoints functional; version history preserved; approval status transitions enforced | Backend |
| 3 | Implement S&OP frontend (plan comparison view, comment thread, approval workflow) | 16h | UI: plan editor, side-by-side version comparison, comment thread per section, approve/reject buttons with confirmation | Frontend |
| 4 | Implement consensus demand planning (multiple stakeholders submit forecasts, system computes consensus) | 8h | Planner, sales, finance each submit demand figures; consensus computed (weighted average or statistical); variance highlighted | Backend |
| 5 | Copilot: replace Ollama dependency with cloud LLM API (OpenRouter primary, NVIDIA fallback) | 8h | Copilot queries route to OpenRouter API; response time < 5s; fallback to NVIDIA if OpenRouter fails | Backend |
| 6 | Copilot: implement RAG (Retrieval Augmented Generation) with IPE data context | 10h | Copilot references actual planning data (current forecasts, inventory levels, open orders) in responses | Backend |
| 7 | Copilot: role-based agents (planner, manager, supervisor, executive) with different system prompts | 6h | Each role agent provides domain-specific responses; executive gets KPI summaries, supervisor gets floor-level detail | Backend |
| 8 | Copilot frontend: chat interface integrated into planning pages (contextual sidebar) | 10h | Chat panel on demand, supply, scenario, and executive pages; pre-populated context based on current page | Frontend |
| 9 | LLM cost management: token counting, per-tenant usage tracking, rate limiting | 4h | Token usage logged per tenant; rate limited to prevent cost overrun; dashboard shows usage | Backend |

**Sprint total**: ~80 hours (~2.0 FTEs for 2 weeks)  
**Blockers**: S&OP workflow scope creep (enterprises have wildly different S&OP processes); LLM cost unpredictability; RAG accuracy for domain-specific planning questions; frontend effort for S&OP UI is significant.

### Phase 2 — Sprint 2.3 (Weeks 15–16): Multi-Echelon & Demand Sensing

**Sprint Goal**: Implement multi-echelon inventory optimization and external demand signal ingestion.

| # | Task | Effort | Acceptance Criteria | Owner |
|---|------|--------|---------------------|-------|
| 1 | Design multi-echelon network model (plants → DCs → customers, lead times, costs) | 6h | Model supports N echelons, inter-echelon transfers, transportation costs, holding costs | Backend |
| 2 | Implement multi-echelon optimization algorithm (guaranteed service time or stochastic) | 16h | Algorithm produces: safety stock per echelon, transfer quantities, total cost; runs in < 60s for 3-echelon/100-SKU network | Backend |
| 3 | Multi-echelon API endpoints (configure network, run optimization, view results) | 6h | API functional; results viewable in frontend | Backend |
| 4 | Multi-echelon frontend (network visualization, optimization results, cost breakdown) | 10h | Sankey diagram shows material flow; table shows per-node safety stock; cost comparison (before/after optimization) | Frontend |
| 5 | Design external demand signal ingestion API (generic webhook + polling) | 4h | API accepts: POS data, weather forecasts, social sentiment, economic indicators; normalized into demand signals | Backend |
| 6 | Implement 2 provider adapters: weather (OpenWeather API) and economic (World Bank API) | 8h | Weather data ingested and correlated with demand; economic indicators available as planning parameters | Backend |
| 7 | Integrate external signals into forecasting pipeline (feature engineering for Prophet/LSTM) | 8h | Forecast accuracy improves by measurable amount when external signals included (A/B test) | Backend |
| 8 | Performance validation: run multi-echelon optimization with realistic dataset (100 SKUs, 3 echelons) | 4h | Optimization completes in < 60s; results are economically sensible (verified by domain expert) | QA |

**Sprint total**: ~62 hours (~1.55 FTEs for 2 weeks)  
**Blockers**: Multi-echelon optimization algorithm complexity (may need academic reference implementation); external signal data quality and latency; forecast accuracy improvement may be marginal for some product categories.

### Phase 3 — Sprint 3.1 (Weeks 19–20): Scale & GDPR

**Sprint Goal**: Validate horizontal scaling, implement GDPR compliance features.

| # | Task | Effort | Acceptance Criteria | Owner |
|---|------|--------|---------------------|-------|
| 1 | Configure HPA for all stateless services (CPU-based, min 2, max 10) | 4h | HPA scales pods under load; verified by stress test | DevOps |
| 2 | Set up PostgreSQL read replica; configure service-to-replica routing for read queries | 6h | 80% of read queries go to replica; primary CPU < 60% under load | Backend |
| 3 | Run k6 load test at 500 concurrent users for 30 minutes | 4h | p95 < 500ms for reads, p95 < 5s for planning, zero errors, zero data corruption | QA |
| 4 | Implement GDPR data export API: `GET /api/v1/tenant/{id}/data-export` | 8h | Export generates JSON/CSV archive of all tenant data; completes in < 10min for 1M records | Backend |
| 5 | Implement GDPR right-to-erasure API: soft-delete + scheduled hard-delete | 8h | `DELETE /api/v1/tenant/{id}/data` soft-deletes all data; hard-delete job runs after retention period; audit log preserved | Backend |
| 6 | Implement consent management UI (privacy settings per tenant) | 6h | Admin can configure: data retention period, consent preferences, data processing purposes | Frontend |
| 7 | Implement data retention enforcement (automated purge job) | 6h | Cron job purges data older than retention period; audit log of purged records | Backend |
| 8 | Publish privacy policy and prepare DPA (Data Processing Agreement) template | 4h | Legal-reviewed privacy policy published; DPA template ready for customer signature | Legal/Product |
| 9 | Write GDPR compliance documentation (data flow maps, processing records) | 4h | GDPR Article 30 records of processing activities documented | Compliance |

**Sprint total**: ~50 hours (~1.25 FTEs for 2 weeks)  
**Blockers**: Load test may reveal bottlenecks requiring architectural changes (e.g., Kafka partition count, database connection pool); GDPR data export for 1M+ records may need streaming/chunked approach; legal review of privacy policy and DPA may take longer than 1 sprint.

### Phase 3 — Sprint 3.2 (Weeks 21–22): WCAG & SOC 2 Prep

**Sprint Goal**: Achieve WCAG 2.1 AA compliance and begin SOC 2 Type I audit preparation.

| # | Task | Effort | Acceptance Criteria | Owner |
|---|------|--------|---------------------|-------|
| 1 | Conduct WCAG 2.1 AA accessibility audit (automated: axe-core; manual: keyboard nav, screen reader) | 6h | Audit report with all violations categorized by severity | QA |
| 2 | Fix all critical WCAG violations (missing alt text, missing labels, color contrast) | 10h | Zero critical violations | Frontend |
| 3 | Fix all major WCAG violations (focus management, keyboard navigation, ARIA roles) | 12h | Zero major violations | Frontend |
| 4 | Add skip-to-content link, landmark regions, and focus trap for modals | 4h | Keyboard users can navigate entire application without mouse | Frontend |
| 5 | Verify screen reader compatibility (NVDA/VoiceOver for key workflows) | 4h | All planning workflows usable with screen reader | QA |
| 6 | Engage SOC 2 auditor; complete Type I readiness assessment | 8h | Auditor engaged; gap assessment document with remediation plan | Compliance |
| 7 | Implement missing SOC 2 controls (access reviews, change management, incident response evidence) | 8h | Evidence artifacts for each SOC 2 control category (security, availability, confidentiality) | Backend |
| 8 | Document security policies (acceptable use, access control, data classification, incident response, change management) | 6h | 5 policy documents reviewed and approved | Compliance |

**Sprint total**: ~58 hours (~1.45 FTEs for 2 weeks)  
**Blockers**: WCAG remediation for a complex planning UI may require significant frontend rework; SOC 2 auditor availability; policy documents require legal/compliance expertise.

---

## 6. Technical Debt & Modernization

### 6.1 Critical Debt (Must Fix Before Production)

| # | Debt Item | Current State | Enterprise Risk | Fix Effort | Priority |
|---|-----------|---------------|-----------------|------------|----------|
| TD-001 | **Single-instance services** | All services run 1 replica in docker-compose | SPOF — one container crash = service down | Kubernetes Deployment + HPA | P0 |
| TD-002 | **No database connection pooling** | Each service opens direct DB connections | Connection exhaustion under load; noisy-neighbor between tenants | PgBouncer deployment; per-service pool configuration | P0 |
| TD-003 | **No API versioning** | All endpoints at `/api/v1/` without version negotiation | Breaking changes require all clients to update simultaneously | URI versioning (`/api/v2/`) + deprecation headers | P1 |
| TD-004 | **Kafka consumer error handling** | Unknown — consumers may not handle poison pills | One bad message can crash a consumer, halting data flow | DLQ, error handler, skip + alert pattern | P0 |
| TD-005 | **No database migration rollback** | Alembic migrations may lack `downgrade()` | Cannot roll back a failed migration in production | Add `downgrade()` to all migrations; test in staging | P1 |
| TD-006 | **Hardcoded configuration values** | Unknown extent — may exist in service code | Cannot tune behavior without code change; different environments may need different values | Audit all services; move to environment variables / config service | P1 |
| TD-007 | **No request timeout configuration** | Services may wait indefinitely for downstream responses | Cascading failures; resource exhaustion under partial outages | Configure timeouts at HTTP client, Kong, and service levels | P0 |
| TD-008 | **No API response caching** | Every request hits the database | Unnecessary load; poor p95 latency for repeated queries | Redis caching for read-heavy endpoints (TTL-based, invalidation on write) | P2 |
| TD-009 | **Frontend bundle size** | Unknown — may include unused dependencies | Slow initial page load; poor mobile experience | Tree-shaking, code splitting, lazy loading, bundle analysis | P2 |
| TD-010 | **No feature flag system** | All features enabled for all tenants | Cannot roll out features gradually; cannot A/B test; no kill switch | LaunchDarkly, Unleash, or simple config-based flags | P2 |

### 6.2 Architectural Modernization (Phase 3–4)

| # | Modernization | Current State | Target State | Benefit | Effort |
|---|---------------|---------------|--------------|---------|--------|
| AM-001 | **Event sourcing for planning data** | CRUD-based — current state stored directly | All changes stored as immutable events; current state derived from event stream | Full audit trail, temporal queries, replay capability | 3–4 sprints |
| AM-002 | **CQRS separation** | Read and write use same models/endpoints | Separate read models (optimized for queries) from write models (optimized for consistency) | Independent scaling of reads vs. writes; better query performance | 2–3 sprints |
| AM-003 | **GraphQL API layer** | REST-only | GraphQL API for complex queries (join data across services in one request) | Fewer round trips for frontend; self-documenting API; flexible queries | 2 sprints |
| AM-004 | **Workflow engine** | Hardcoded approval flows | Pluggable workflow engine (Temporal or Cadence) for S&OP, procurement approvals, change management | Configurable workflows per tenant; visibility into process state | 2–3 sprints |
| AM-005 | **ML model serving infrastructure** | Models embedded in services | Centralized model serving (MLflow or custom) with A/B testing, canary deployment, model versioning | Independent model lifecycle; experiment tracking; production ML ops | 2 sprints |

### 6.3 Debt Impact vs. Fix Effort Matrix

```
High Impact
    ▲
    │  TD-001    TD-007
    │  (k8s)     (timeouts)
    │
    │  TD-004    TD-002
    │  (DLQ)     (pooling)
    │
    │  TD-005    TD-003
    │  (rollback) (versioning)
    │
    │  TD-006    TD-008
    │  (config)   (caching)
    │
    │  TD-010    TD-009
    │  (features) (bundle)
    └──────────────────────────► Low Effort → High Effort
```

Top-left quadrant (high impact, low effort) should be fixed first: TD-001, TD-007, TD-004, TD-002. These are the "quick wins" that dramatically improve reliability.

---

## 7. Go-Live Checklist

This is the final gate before any customer-facing production deployment. Every item must be verified and signed off by the engineering lead and product owner.

### 7.1 Pre-Launch Validation

- [ ] **GO-001**: All Phase 0–2 deliverables completed and verified
- [ ] **GO-002**: Full regression test suite passes (870+ unit tests, 28 frontend tests, 4 Playwright E2E, 6 chaos tests) with zero failures
- [ ] **GO-003**: Load test passed: 500 concurrent users, 30-minute duration, zero errors, p95 within SLO
- [ ] **GO-004**: Security penetration test passed: zero critical/high findings
- [ ] **GO-005**: WCAG 2.1 AA audit passed: zero critical/major findings
- [ ] **GO-006**: Database migration tested: forward and backward migration on production-like data (1M+ rows)
- [ ] **GO-007**: Backup and restore tested: full backup → destroy primary → restore → verify data integrity
- [ ] **GO-008**: Disaster recovery tested: simulate region failure (if multi-region) or full cluster failure → recover within RTO
- [ ] **GO-009**: Rolling deployment tested: upgrade from current version to new version with zero downtime and zero dropped requests
- [ ] **GO-010**: Failure recovery tested: kill each service individually, verify automatic recovery and no data loss
- [ ] **GO-011**: Chaos test suite passed: all C1–C6 scenarios pass on Kubernetes deployment
- [ ] **GO-012**: Monitoring verified: all dashboards showing data, all alerts firing correctly, PagerDuty integration confirmed
- [ ] **GO-013**: Logging verified: all services producing structured JSON logs with correlation IDs; searchable in Loki/ELK
- [ ] **GO-014**: Tracing verified: end-to-end trace visible in Jaeger/Tempo for a sample request flow
- [ ] **GO-015**: SSL certificate validity confirmed (expiration > 90 days)

### 7.2 Business Readiness

- [ ] **GO-016**: Pricing model finalized and documented
- [ ] **GO-017**: Terms of service and privacy policy published and legally reviewed
- [ ] **GO-018**: Data Processing Agreement (DPA) template ready for customer signature
- [ ] **GO-019**: SLA document ready (uptime, support response times, maintenance windows)
- [ ] **GO-020**: Customer support workflow established (ticket routing, escalation, on-call schedule)
- [ ] **GO-021**: Onboarding guide for new customers (setup, configuration, first forecast)
- [ ] **GO-022**: API documentation published and reviewed (OpenAPI spec, authentication guide, error codes)
- [ ] **GO-023**: Knowledge base launched with minimum 20 articles (getting started, common tasks, troubleshooting)
- [ ] **GO-024**: Status page configured and linked from product UI and documentation

### 7.3 Rollback Plan

- [ ] **GO-025**: Previous version Docker images tagged and available in registry
- [ ] **GO-026**: Database migration rollback tested and documented (Alembic downgrade command)
- [ ] **GO-027**: Helm chart rollback procedure documented: `helm rollback ipe <revision>`
- [ ] **GO-028**: Feature flags configured so new features can be disabled without deployment
- [ ] **GO-029**: Communication plan for rollback (customer notification template, status page update procedure)
- [ ] **GO-030**: Rollback decision criteria defined: who decides, based on what metrics, within what timeframe

### 7.4 Launch Day Procedure

1. **T-60min**: Final health check on staging — all green
2. **T-30min**: Notify on-call team of planned deployment; confirm PagerDuty escalation is active
3. **T-15min**: Database backup (full snapshot before migration)
4. **T-0**: Deploy to production via CI/CD pipeline (or `helm upgrade`)
5. **T+5min**: Run smoke test suite (automated: 10 critical API calls)
6. **T+10min**: Verify monitoring dashboards — no error spikes, latency within normal range
7. **T+15min**: Run full demo script (13-step integration + key planning workflows)
8. **T+30min**: Confirm with customer success that first customer can log in and perform basic planning operations
9. **T+60min**: If all green — broadcast "launch successful" to team; update status page to "All Systems Operational"
10. **T+60min (rollback trigger)**: If any red — execute rollback plan (GO-025 through GO-030); communicate to stakeholders

---

## 8. Timeline & Resource Estimate

### 8.1 Phase Timeline

| Phase | Duration | Cumulative | Key Milestone | FTEs Required |
|-------|----------|------------|---------------|---------------|
| Phase 0: Foundation Hardening | 4 weeks | Week 4 | SSO + Vault + Audit Logs operational | 2.0 (1 backend, 1 DevOps) |
| Phase 1: Operational Readiness | 6 weeks | Week 10 | Kubernetes + Observability + CI/CD + Chaos tested | 2.5 (1 backend, 1 DevOps, 0.5 QA) |
| Phase 2: Enterprise Feature Parity | 8 weeks | Week 18 | SAP/D365 connectors + S&OP + Copilot + Multi-echelon | 3.5 (1.5 backend, 1 frontend, 0.5 integration, 0.5 DevOps) |
| Phase 3: Scale & Compliance | 8 weeks | Week 26 | Load tested at 500 users + GDPR + WCAG + SOC 2 Type I | 3.0 (1 backend, 1 frontend, 0.5 QA, 0.5 compliance) |
| Phase 4: Go-to-Market | 10 weeks | Week 36 | Self-service onboarding + API portal + Billing + Mobile | 3.0 (1 backend, 1 frontend, 0.5 product, 0.5 DevOps) |
| **Total** | **36 weeks** | | | |

### 8.2 Resource Requirements by Role

| Role | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Notes |
|------|---------|---------|---------|---------|---------|-------|
| **Backend Engineer** | 1.0 | 1.0 | 1.5 | 1.0 | 1.0 | Core platform work: auth, vault, services, APIs |
| **Frontend Engineer** | 0.0 | 0.0 | 1.0 | 1.0 | 1.0 | S&OP UI, WCAG remediation, mobile, API portal |
| **DevOps / SRE** | 1.0 | 1.5 | 0.5 | 0.5 | 0.5 | Kubernetes, CI/CD, monitoring, scaling, billing infra |
| **Integration Engineer** | 0.0 | 0.0 | 1.0 | 0.0 | 0.0 | SAP/D365 connectors (specialized expertise — hire or outsource) |
| **QA Engineer** | 0.0 | 0.5 | 0.0 | 0.5 | 0.0 | Security testing, load testing, WCAG testing |
| **Product Manager** | 0.0 | 0.0 | 0.0 | 0.0 | 0.5 | GTM strategy, pricing, onboarding UX, partner program |
| **Compliance / Legal** | 0.0 | 0.0 | 0.0 | 0.5 | 0.0 | GDPR, SOC 2, privacy policy, DPA (outsource initially) |
| **UX Designer** | 0.0 | 0.0 | 0.5 | 0.0 | 0.5 | S&OP workflow design, mobile design, onboarding UX |

### 8.3 Hiring / Outsourcing Recommendations

**Must-hire (before Phase 2)**:
1. **Senior DevOps / SRE** (if not already on team) — Kubernetes, Terraform, Prometheus, Kafka operations. This person owns the production infrastructure. Without this role, Phase 1 will be slow and error-prone.
2. **Integration Engineer (SAP-certified)** — SAP S/4HANA OData API expertise is a niche skill. Either hire a contractor for Phase 2 (8 weeks) or partner with an SAP integration specialist firm. This is not a role you can upskill a generalist into in 2 weeks.

**Should-hire (before Phase 3)**:
3. **Senior Frontend Engineer** — WCAG remediation, mobile responsiveness, and the S&OP UI require experienced frontend work. If your current frontend resource is junior, augment with a senior contractor.
4. **QA Engineer (security-focused)** — Penetration testing, WCAG auditing, and load testing require specialized skills. A part-time contractor (2 days/week) across Phases 1 and 3 is sufficient.

**Can-outsource (on demand)**:
5. **SOC 2 audit preparation** — Engage a compliance consulting firm (e.g., Vanta, Drata, or a Big 4 advisory) for Phase 3. They provide templates, gap analysis, and auditor introduction.
6. **Legal review** — Privacy policy, DPA, ToS: use a technology law firm on a per-document basis. Do not hire in-house legal for a lean team.
7. **UX design** — Engage a product design agency for the S&OP workflow (Phase 2) and mobile design (Phase 4). This is project-based work, not a full-time role.

### 8.4 Cost Estimate (Indicative)

| Category | Monthly Cost (Lean Team) | Notes |
|----------|--------------------------|-------|
| Engineering team (4 FTEs) | $40,000–60,000 | Senior backend, mid frontend, senior DevOps, mid QA (US/EU rates; lower if MENA-based) |
| Infrastructure (staging) | $500–1,000 | Kubernetes cluster, managed DB, Kafka, monitoring |
| Infrastructure (production, 1 tenant) | $1,000–2,000 | Scales with tenants |
| Third-party tools | $500–1,500 | LLM API (OpenRouter), PagerDuty, container registry scanning, compliance tools |
| Contractors / consultants | $5,000–15,000 | Integration engineer (Phase 2), SOC 2 prep (Phase 3), UX design (Phases 2,4) |
| Legal / compliance | $2,000–5,000 | Privacy policy, DPA, SOC 2 audit |
| **Total per month** | **$49,000–84,500** | |
| **Total for 36-week program** | **$441,000–760,500** | |

### 8.5 Risk Register

| # | Risk | Probability | Impact | Mitigation | Phase |
|---|------|-------------|--------|------------|-------|
| R-001 | Keycloak integration more complex than expected | Medium | High | Start with simplest OIDC flow; defer SAML to Phase 2; consider Auth0 as alternative | Phase 0 |
| R-002 | Vault integration breaks service startup | Medium | High | Implement fallback to env vars with warning; phased rollout per service | Phase 0 |
| R-003 | Kubernetes migration uncovers architectural issues | High | High | Run discovery sprint before Phase 1; fix blocking issues first | Phase 1 |
| R-004 | SAP connector requires SAP-certified developer | High | High | Budget for SAP-certified contractor; start engagement early (Phase 1) | Phase 2 |
| R-005 | LLM costs exceed budget | Medium | Medium | Implement token limits, caching, rate limiting; consider open-source LLM for on-prem | Phase 2 |
| R-006 | S&OP workflow scope creeps | High | Medium | Strictly define MVP workflow; defer customization to Phase 4 | Phase 2 |
| R-007 | Load test reveals fundamental scaling bottleneck | Medium | High | Architectural review before Phase 3; budget 2-week buffer for rearchitecting | Phase 3 |
| R-008 | SOC 2 auditor finds unexpected gaps | Medium | Medium | Pre-audit self-assessment using Vanta/Drata before engaging auditor | Phase 3 |
| R-009 | WCAG remediation requires frontend rework | Medium | Medium | Budget 2 extra sprints; consider accessibility-first component library | Phase 3 |
| R-010 | Key team member leaves during critical phase | Low | Critical | Cross-training from Phase 0; documentation of all decisions; no single point of knowledge | All |
| R-011 | Customer demands features not in roadmap | High | Medium | Feature request process with prioritization framework; clear communication of roadmap | All |
| R-012 | Odoo 19 API changes break connector | Low | Medium | Pin Odoo version in docker-compose; monitor Odoo release notes; integration test on every Odoo update | Phase 2 |

### 8.6 Acceleration Options

If the timeline of 36 weeks is too slow for competitive reasons, consider these acceleration strategies:

1. **Parallel Phase 0 + Phase 1**: Security foundation and Kubernetes deployment can partially overlap — Vault and Keycloak can be deployed on Kubernetes from the start. This could save 2–3 weeks.

2. **Outsource SAP connector**: A specialized SAP integration firm can deliver the SAP connector in 4 weeks instead of 8. Budget $20K–40K for this. Saves 4 weeks.

3. **Buy, don't build**: For feature flags (LaunchDarkly), monitoring (Datadog), and compliance automation (Vanta/Drata), use SaaS tools instead of building custom solutions. Saves 4–6 weeks of engineering effort across phases.

4. **Reduce scope for initial go-live**: Ship Phase 0–2 as "Enterprise Beta" with a limited number of design partners (3–5 customers). Defer multi-echelon optimization and S&OP workflow to a fast-follow release. This could achieve initial enterprise deployment by Week 18 instead of Week 36.

5. **Hire aggressively for Phase 1–2**: Adding 1–2 senior contractors for the 14-week Phase 1–2 window can parallelize backend and frontend work, potentially saving 3–4 weeks.

**Fastest credible path to first enterprise customer deployment**: Week 18 (Phase 0–2 complete, Enterprise Beta with limited scope). This requires the core team of 3–4 FTEs plus 1 SAP contractor for Phase 2.

---

*This roadmap is a living document. Reassess priorities and timelines at the end of each phase based on actual velocity, customer feedback, and competitive intelligence.*
