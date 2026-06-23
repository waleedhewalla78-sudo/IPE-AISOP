# IPE Platform — Speckit Checklist

**Generated**: 2026-06-21 | **Platform**: IPE v1.0.0 | **Overall**: 38/39 tasks DONE, 1 BLOCKED

---

## Summary Dashboard

| Category | Total | Done | Partial | Blocked | Not Started |
|----------|-------|------|---------|---------|-------------|
| Plan Tasks | 39 | 38 | 0 | 1 | 0 |
| Open Issues | 35 | 26 | 2 | 0 | 7 (deferred) |
| Quality FRs | 59 | 48 | 4 | 0 | 7 |
| Risks | 13 | 7 | 2 | 0 | 4 (open) |
| Cross-Artifact | 29 | 0 | 0 | 0 | 29 (inconsistencies) |

---

## Phase A: Foundation — ✅ COMPLETE

- [x] A-001: CDM schema (19 tables) with RLS
- [x] A-002: Shared library (ipe_shared) package
- [x] A-003: FastAPI service scaffold (8 services)
- [x] A-004: Docker Compose (28 containers)
- [x] A-005: CI pipeline (.github/workflows/ci.yml)

---

## Phase B: Production Readiness — ✅ COMPLETE

- [x] B-001: OpenTelemetry instrumentation (14 services)
- [x] B-002: Structured JSON logging (14 services)
- [x] B-003: Prometheus /metrics (14 services)
- [x] B-004: Alert Manager + PagerDuty integration
- [x] B-005: Kong rate limiting (300/min, 10000/hr)

---

## Phase C: Testing & Chaos — ⚠️ 7/8 DONE, 1 BLOCKED

- [x] C-001: Schemathesis CI integration (8h)
- [x] C-002: OR-Tools correctness tests — 22 scenarios (16h)
- [x] C-003: ISolver constraint passing (16h)
- [x] C-004: nlp-svc bare pass verification (8h)
- [x] C-005: Chaos Mesh manifests (MANIFESTS READY)
- [x] C-006: k6 200 VU load test (8h)
- [ ] C-007: Keycloak live IdP testing (24h) — **BLOCKED** (needs Azure AD sandbox)
- [x] C-008: Airflow scheduler + worker (16h)

---

## Phase D: Governance & Compliance — ✅ COMPLETE

- [x] D-001: Compliance evidence collector (40h)
- [x] D-002: FDA 21 CFR Part 11 e-signature (40h)
- [x] D-003: BYOK KMS — LocalKMSBackend (24h)
- [x] D-004: mTLS — Istio PeerAuthentication (24h)
- [x] D-005: ISO 27001 ISMS documentation (40h)
- [x] D-006: Kong developer portal (24h)
- [x] D-007: SAST — Bandit in CI (8h)
- [x] D-008: Dependency scanning — Dependabot (8h)

---

## Phase E: MLOps & Advanced — ✅ COMPLETE

- [x] E-001: Drift detection module (24h)
- [x] E-002: Shadow ROI validator (24h)
- [x] E-003: Progressive Autonomy state machine (40h)
- [x] E-004: Synchronous safety guardrail (16h)
- [x] E-005: SCN Portal frontend (40h)
- [x] E-006: Shop Floor PWA (80h)
- [x] E-007: MLOps Dashboard (24h)
- [x] E-008: MLflow model registry + approval (16h)
- [x] E-009: Unleash feature flag container (8h)
- [x] E-010: Auth0 tenant for SCN Portal (16h)

---

## Phase F: Infrastructure — ✅ COMPLETE

- [x] F-001: ArgoCD multi-environment (16h)
- [x] F-002: K3s edge manifests (40h)
- [x] F-003: Terraform for prod EKS (40h)
- [x] F-004: Argo Rollouts canary strategy (16h)
- [x] F-005: External Secrets Operator (24h)
- [x] F-006: PodDisruptionBudgets (8h)
- [x] F-007: HPA all stateless services (8h)
- [x] F-008: Airflow production hardening (16h)

---

## Phase G: Commercial & Polish — ✅ COMPLETE

- [x] G-001: Tiered pricing enforcement (40h)
- [x] G-002: Usage metering (40h)
- [x] G-003: Notification center (80h)
- [x] G-004: Production Grafana dashboards (16h)
- [x] G-005: Internal security review (16h)

---

## Open Issues — Status

| ID | Description | Status | Action Needed |
|----|-------------|--------|---------------|
| OI-001–OI-012 | Critical bugs (E2E, UUID, ports, seed, OTel, logging, alerts, Kong) | ✅ RESOLVED | None |
| OI-013 | mTLS not enforced in runtime | 🟡 MANIFESTS READY | Deploy to K8s |
| OI-014 | HS256 default JWT | 🟡 OPT-IN READY | Enable via JWT_USE_JWKS=True |
| OI-015–OI-025 | Schemathesis, Chaos, ArgoCD, K3s, MLflow, Airflow, Drift, PWA, SCN, Retention, E-Sign | ✅ RESOLVED | None |
| OI-026 | No SAP/D365 adapters | ✅ RESOLVED (Odoo only) | None |
| OI-027 | Federated learning | ⏸️ DEFERRED | Future scope |
| OI-028 | Mobile app (React Native) | ⏸️ DEFERRED | Future scope |
| OI-029–OI-034 | Notifications, Commercial, API docs, SAST, Dependabot | ✅ RESOLVED | None |
| OI-032 | Visual regression testing | ⏸️ DEFERRED | Future scope |
| OI-035 | WCAG 2.1 AA audit | ⏸️ DEFERRED | Future scope |

---

## Quality FR Checklist — Functional Requirements

### Core Business (FR-001–FR-015)
- [x] FR-001: 18 containers start + health check 90s
- [x] FR-002: JWKS JWT validation
- [x] FR-003: /metrics ALL 14 services
- [x] FR-004: OpenTelemetry all services
- [x] FR-005: Structured JSON logging all services
- [x] FR-006: Alert Manager + PagerDuty
- [x] FR-007: E2E tests 16/16
- [ ] FR-008: Keycloak OAuth 2.1/OIDC — 🟡 PARTIAL (mock config)
- [ ] FR-009: SAML 2.0 SSO — 🟡 PARTIAL (needs live IdP)
- [ ] FR-010: SCIM 2.0 endpoints — 🟡 PARTIAL (needs live IdP)
- [x] FR-011: mTLS via Istio
- [x] FR-012: RBAC ALL endpoints
- [x] FR-013: Kong rate limiting
- [x] FR-014: Structured JSON logging
- [x] FR-015: Grafana dashboards

### Sustainability (FR-101–FR-113)
- [x] FR-101: Circular supply chain
- [x] FR-102: End-of-life planning
- [x] FR-103: Recyclability scoring
- [x] FR-104: Sustainability events
- [x] FR-105: Supplier scorecards
- [x] FR-106: RFQ/RFP workflow
- [x] FR-107: Multi-tier supplier visibility
- [x] FR-108: SCN events emitted
- [x] FR-109: SPC charts + control limits
- [x] FR-110: Defect prediction
- [x] FR-111: SOC 2 + ISO 27001 evidence
- [x] FR-112: GDPR DSAR API
- [x] FR-113: FDA 21 CFR Part 11 e-signature

### Compliance (FR-201–FR-206)
- [x] FR-201: Compliance evidence 5 principles
- [x] FR-202: DSAR API 30-day return
- [x] FR-203: Data retention configurable
- [x] FR-204: E-signature fields
- [x] FR-205: Failed e-sign lockout
- [x] FR-206: Compliance dashboard

### Infrastructure (FR-301–FR-307)
- [x] FR-301: Kong API Gateway
- [x] FR-302: ArgoCD app-of-apps
- [x] FR-303: K3s edge manifests
- [x] FR-304: External Secrets Operator
- [x] FR-305: PodDisruptionBudgets
- [x] FR-306: HPA all stateless
- [x] FR-307: Environment promotion CI/CD

### MLOps (FR-401–FR-405)
- [x] FR-401: MLflow tracking server
- [x] FR-402: Airflow with DAGs
- [x] FR-403: Drift detection
- [ ] FR-404: Model registry + approval — 🟡 PARTIAL
- [ ] FR-405: Feature store — ❌ NOT STARTED

### Frontend (FR-501–FR-507)
- [x] FR-501: Shop Floor PWA
- [x] FR-502: SCN Portal
- [x] FR-503: Executive Dashboard
- [x] FR-504: Notification center
- [ ] FR-505: React Native mobile app — ❌ NOT STARTED
- [ ] FR-506: WCAG 2.1 AA — ❌ NOT STARTED
- [ ] FR-507: Visual regression CI — ❌ NOT STARTED

### Commercial (FR-601–FR-606)
- [x] FR-601: Tenant tier enforcement
- [x] FR-602: Usage metering
- [ ] FR-603: Stripe billing — ❌ NOT STARTED
- [ ] FR-604: Self-service onboarding — ❌ NOT STARTED
- [x] FR-605: API documentation portal
- [ ] FR-606: SLA monitoring — ❌ NOT STARTED

---

## Risks — Open Items

| ID | Description | Status | Mitigation |
|----|-------------|--------|------------|
| R-003 | Keycloak not tested against real IdP | 🟡 OPEN | Get Azure AD sandbox |
| R-004 | No mTLS in Docker | 🟡 MANIFESTS READY | Deploy to K8s |
| R-005 | HS256 default JWT | 🟡 OPT-IN READY | Enable JWKS |
| R-008 | No drift detection | 🟡 OPEN | Implement module |
| R-011 | Airflow not production-ready | 🟡 OPEN | Add auth + scheduler |
| R-012 | ISolver constraints ignored | 🟡 OPEN | Future enhancement |
| R-013 | nlp-svc bare pass statements | 🟡 OPEN | Replace with logging |

---

## Blockers

| ID | Description | Blocked On | Priority |
|----|-------------|------------|----------|
| C-007 | Keycloak live IdP testing | Azure AD / Okta sandbox credentials | P1 |

---

## Cross-Artifact Inconsistencies (29 total) — RESOLVED 2026-06-22

Reconciliation via `002-release-stabilization-gates` (clarify.md, analysis.md, READINESS.md). **0 CRITICAL/HIGH open.**

### CRITICAL (3) — resolved
- [x] C1: Sprint 16 / Phase F status → `000-project-completion/spec.md` updated; Sprint 16 COMPLETE
- [x] C2: Phase 6/7/8 status → spec tables aligned (Phase 6 PARTIAL, 7/8 COMPLETE)
- [x] C3: plan readiness contradiction → `001-production-readiness-convergence/plan.md` superseded; **85/100** in READINESS.md

### HIGH (9) — resolved
- [x] H1: Phase C → **PARTIAL**, C-007 BLOCKED in plan.md, tasks.md, checklist
- [x] H2: FR-011 mTLS → documented as manifests-only in READINESS residual risks
- [x] H3: Sprint 12 → aligned with tasks (infra manifests complete)
- [x] H4: Readiness scores → single **85/100** in READINESS.md (supersedes 87, 90, 99)
- [x] H5: Service count → **14 app + connector**
- [x] H6: Test count → **700+** (Gate 1 evidence)
- [x] H7–H9: plan projection/timeline → marked historical; measured score authoritative

### MEDIUM (14)
- [ ] M1–M14: Various arithmetic and mapping errors in plan.md, tasks.md, quality-checklists.md

### LOW (3)
- [ ] L1–L3: Minor formatting and deduplication issues

---

## Not Started — Future Scope

| ID | Description | Priority | Est. Effort |
|----|-------------|----------|-------------|
| FR-405 | Feature store for centralized ML features | P2 | 4-8 weeks |
| FR-505 | React Native mobile app | P3 | 4-6 weeks |
| FR-506 | WCAG 2.1 AA audit | P2 | 3-5 days |
| FR-507 | Visual regression testing CI | P3 | 2-3 days |
| FR-603 | Stripe billing integration | P3 | 2-3 weeks |
| FR-604 | Self-service onboarding wizard | P3 | 1-2 weeks |
| FR-606 | SLA monitoring uptime + credits | P3 | 1-2 weeks |
| OI-027 | Federated learning (cross-site ML) | LOW | 2-3 weeks |
| OI-028 | Mobile app (React Native) | LOW | 4-6 weeks |

---

## Recommended Next Actions

### Immediate (Documentation Sync) — 2h
1. Update spec.md status tables to match tasks.md completions
2. Fix plan.md readiness score (90→99)
3. Fix plan.md resource table arithmetic
4. Fix plan.md timeline "18 weeks"→"20 weeks"
5. Fix tasks.md Phase D hours (216→208)
6. Fix quality-checklists arithmetic

### Short-Term (Test Coverage) — 1-2 days
7. Write 23 API tests for 10 critical untested endpoints
8. Get Azure AD/Okta sandbox for C-007

### Medium-Term (Missing FRs) — 2-4 weeks
9. WCAG 2.1 AA baseline audit
10. Stripe billing mock implementation
11. Self-service onboarding wizard
12. Feature store for ML features

---

*Checklist generated 2026-06-21 · IPE Platform v1.0.0*
