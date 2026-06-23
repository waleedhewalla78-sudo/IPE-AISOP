# Execution Plan: IPE Platform Production Readiness — Convergence Plan

**Plan Branch**: `001-production-readiness-convergence`
**Created**: 2026-06-20
**Status**: Superseded by Gate 2 validation — see [`READINESS.md`](../../READINESS.md)
**Baseline**: Spec v4 — **85/100** readiness (measured 2026-06-22, not projection)

---

## Executive Summary

The IPE platform **handover threshold (≥85/100) is met** per Gate 2 E2E evidence (`specs/002-release-stabilization-gates/`). This plan's projection table below is **historical planning**; do not cite 99/100 without new audit.

**Current State**: **700+** pytest functions (Gate 1), 26 Docker containers, 21 migrations, 14 app services + connector, Keycloak live IdP **BLOCKED** (C-007).

---

## Completed Work (No Action Needed)

These items from the previous plan are **DONE** and should not be re-implemented:

| Task | Previous Phase | Completion Reference |
|------|---------------|----------------------|
| /metrics on all services | P0 | setup_observability() on all 14 services |
| Structured JSON logging | P0 | IPEJsonFormatter with correlation_id |
| Fix cdm_user seed | P0 | password_hash + full_name + is_active columns |
| Fix cdm_location table | P0 | migration 014 |
| StrEnum deprecation | P0 | 5 classes migrated |
| OpenTelemetry instrumentation | P0 | ipe_shared/observability/ on all 14 services |
| Alert Manager / PagerDuty | P0 | PagerDutyClient + AlertManagerClient |
| S&OP solver (real DB) | P5 | sop_solver.py + migration 016 |
| Financial Translation (GL) | P5 | cost_accounting.py + configurable GL mapping |
| Executive Dashboard | P5 | /executive with P&L, gap analysis, what-if |
| AI Trust Dashboard | P5 | /ai-trust with 5 trust scores |
| Digital Twin (recursive CTE) | P6 | DigitalTwinService with real DB queries |
| War Room UX | P6 | /war-room with disruption aggregation |
| WebSocket disruption broadcast | P6 | fea-svc/app/ws/disruption.py |
| ISolver interface | P3 | ipe_shared/solver/interface.py + ORToolsSolver |
| RBAC enforcement scan | P1 | scripts/scan-endpoints-auth.py |
| RLS 48/48 tables | P1 | RLS audit complete, migration 020 for cdm_maintenance_window |
| XAI standardization | P1 | contributing_factors float-only fix |
| Kong rate limiting | P1 | 300/min, 10000/hr per consumer |
| X-Tenant-ID strip | P1 | Kong request-transformer plugin |
| SOC 2 controls framework | P1 | 21 controls, 5 trust principles, DB persistence |
| GDPR DSAR API | P1 | 7 endpoints, DB persistence |
| Audit log immutability | P9 | REVOKE UPDATE/DELETE, trigger, ipe_audit_writer role |
| Data retention policies | P9 | RetentionService, 7 policies, Airflow DAG |
| Tiered LLM routing | P2 | TieredRouter with SAAS/PRIVATE_VPC/ON_PREM |
| PII stripping middleware | P2 | PIIStripper regex + PIIStrippingMiddleware |
| Schemathesis schemas | P2 | 10 service schemas defined |
| ArgoCD app-of-apps | P2 | ipe-infrastructure + ipe-platform-services |
| Airflow DAGs | P2 | 3 DAGs + retention enforcement DAG |
| MLflow container | P2 | Docker compose, port 5000 |
| Real analytics/DT/GL data | P2 | DB queries replacing mock data |
| AI testing framework | P2 | 6 agents in testing/ai/ |
| Capacity/labor gate scoring | P2 | _compute_capacity_gate + _compute_labor_gate |

---

## Remaining Work — Phase-by-Phase Plan

### Phase C: Testing & Quality Completion (Weeks 1-3) 🟡 PARTIAL (C-007 BLOCKED)

**Goal**: Close all testing gaps; integrate AI testing into CI; complete ISolver constraint passing.

| ID | Task | Deliverable | Effort | Spec Ref | Dependencies | Status |
|----|------|------------|--------|----------|-------------|--------|
| C1 | Integrate Schemathesis into CI pipeline | GitHub Actions job runs `schemathesis run` for all 12 service schemas on PR | 1 day | OI-015 | schemas exist | ✅ DONE |
| C2 | 20-scenario OR-Tools correctness tests | Parameterized pytest suite: 5-level BOM, skill constraints, multi-work-center, frozen ops, tardiness, cost-optimized, green scheduling, warm start, 1000-MO scaling | 2 days | Sprint 13 | ISolver interface | ✅ DONE (22 tests) |
| C3 | Complete ISolver constraint passing | ORToolsSolver `_build_constraint_map()` dispatches constraints to scheduler params | 2 days | R-012 | P3-001/002 done | ✅ DONE |
| C4 | Fix nlp-svc bare pass statements (7 locations) | Verified correct: all `pass` inside `except asyncio.QueueEmpty/QueueFull` — intentional exception handling | 1 day | R-013 | None | ✅ VERIFIED |
| C5 | Deploy Chaos Mesh in staging K8s | 5 manifests created: kafka-pod-kill, postgres-failover, redis-pod-kill, network-partition, cpu-pressure + runner script | 3 days | OI-016 | Staging K8s | ✅ MANIFESTS READY |
| C6 | k6 scale to 200 VUs + CI gate | `load-test-200vu.js` — ramps to 200 VUs, p95 < 5s, <2% error rate | 1 day | Sprint 6 | existing k6 | ✅ DONE |
| C7 | Keycloak live IdP testing | Test SAML 2.0 SSO against Azure AD/Okta sandbox; test SCIM 2.0 provisioning | 3 days | R-003 | Azure AD/Okta tenant | ⏳ BLOCKED (needs IdP sandbox) |
| C8 | Configure Airflow DAGs + basic execution | `airflow-scheduler` + `airflow-worker` services added to docker-compose.yml | 2 days | R-011 | DAGs exist | ✅ DONE |

**VERIFY Gates**:
- V-C1: `schemathesis run` passes for all 10 services with 0 unhandled 5xx ✅
- V-C2: All 22 OR-Tools scenarios pass (22/22) ✅
- V-C5: Chaos Mesh manifests ready; deploy to K8s for live testing ⏳
- V-C8: Airflow scheduler + worker in docker-compose ✅

**Phase C Result**: 7/8 tasks complete, 1 blocked (Keycloak sandbox credentials)

---

### Phase D: Governance & Compliance Completion (Weeks 4-7)

**Goal**: Complete remaining governance items for SOC 2 Type II readiness.

| ID | Task | Deliverable | Effort | Spec Ref | Dependencies |
|----|------|------------|--------|----------|-------------|
| D1 | Implement compliance evidence collector | Automated evidence gathering from logs, KPI endpoints, code scans for all 5 trust principles; `GET /compliance/soc2/evidence` endpoint | 1 week | FR-201 | SOC 2 controls exist |
| D2 | Implement FDA 21 CFR Part 11 e-signature | Electronic signature: user ID, NIST timestamp, signature meaning, full record; N-attempt lockout; audit trail | 1 week | FR-204, FR-205 | Audit log immutable |
| D3 | Implement BYOK KMS (AWS KMS) | Terraform for KMS key policy denying root `kms:Decrypt`; tenant-specific DEK wrapping; in-memory DEK cache with 1h TTL | 3 days | Sprint 14 | K8s cluster |
| D4 | Deploy mTLS in K8s cluster | Apply PeerAuthentication STRICT + DestinationRule; configure cert-manager for auto-rotation; phased rollout: PERMISSIVE→STRICT | 3 days | SC-010 | K8s cluster |
| D5 | ISO 27001 ISMS documentation | Document information security policies, risk assessment, SoA (Statement of Applicability) mapping 114 Annex A controls | 1 week | Gap 3 | SOC 2 controls |
| D6 | Kong developer portal | Configure Kong Dev Portal with API documentation, SDK generation, rate limit tiers | 3 days | FR-301 part | Kong configured |
| D7 | SAST in CI (Bandit) | Add Bandit security scanning to CI pipeline; block merge on critical/high findings | 1 day | OI-033 | None |
| D8 | Dependency scanning (Dependabot) | Configure Dependabot/Renovate for Python + Node dependencies; auto-PR on vulnerabilities | 1 day | OI-034 | None |

**VERIFY Gates**:
- V-D1: `GET /compliance/soc2/evidence` returns evidence for all 5 trust principles with >80% coverage
- V-D2: E-signature captures user ID, timestamp, meaning; account locks after 5 failed attempts
- V-D3: Enterprise tenant encrypted with tenant KMS key; SaaS root AWS credentials denied `kms:Decrypt`
- V-D4: `tcpdump` on any pod shows TLS handshake with client certificate; pod without sidecar cannot connect

---

### Phase E: MLOps & Advanced Features (Weeks 8-13, parallel with D)

**Goal**: Complete MLOps pipeline, drift detection, Progressive Autonomy, and remaining frontends.

| ID | Task | Deliverable | Effort | Spec Ref | Dependencies |
|----|------|------------|--------|----------|-------------|
| E1 | Implement drift detection module | Monitor NLP accuracy, pATP reliability (XmR charts), feasibility PSI; alert via PagerDuty when drift >5%; store in MLflow | 3 days | FR-403, R-008 | MLflow deployed |
| E2 | Build shadow_roi_validator.py | `scipy.stats` OTD delta calculation; 95% CI; filter cancelled/scrapped MOs; statistical significance test | 3 days | Sprint 15 | Historical data |
| E3 | Implement Progressive Autonomy state machine | States: Shadow → Suggest → Autonomous; per-tenant config; Unleash feature flags (self-hosted, free) | 1 week | Sprint 15 | State tracking |
| E4 | Implement synchronous safety guardrail | Feasibility <85% blocks ERP write-back synchronously; async Kafka alert to Slack | 2 days | Sprint 15 | fea-svc |
| E5 | Build SCN Portal frontend | Supplier list with scorecards, RFQ management, risk flags, Auth0 external tenant | 1 week | OI-023, US5 | scn-svc APIs |
| E6 | Complete Shop Floor PWA | Service Worker + IndexedDB offline cache; barcode scanning via WebRTC camera; IoT dashboard | 2 weeks | OI-022, FR-501 | None |
| E7 | Build MLOps Dashboard | Experiment list, model registry, drift metrics, Data Steward approval queue | 3 days | FR-404 | MLflow |
| E8 | MLflow model registry + approval workflow | Version staging → production with Data Steward approval; one-click rollback | 2 days | FR-404 | E1 |
| E9 | Deploy Unleash feature flag container | Self-hosted Unleash for Progressive Autonomy flags (shadow/suggest/autonomous per tenant) | 1 day | Sprint 15, OI-023 | None |
| E10 | Configure Auth0 tenant for SCN Portal | Auth0 org-based multi-tenant auth for external suppliers; M2M app for SCN API | 2 days | OI-023, US5 | E5 |

**VERIFY Gates**:
- V-E1: Inject synthetic data drift → model flagged, blocked from auto-promotion, PagerDuty alert within 60s
- V-E2: Shadow validation script filters out cancelled/scrapped MOs; reports >10% OTD improvement at 95% CI
- V-E3: Set tenant to Autonomous, create MO with 82% feasibility → ERP write-back blocked synchronously
- V-E5: Supplier logs in via Auth0, sees their scorecard and RFQ list; cross-tenant data returns 403

---

### Phase F: Infrastructure & Production Readiness (Weeks 14-17)

**Goal**: Kubernetes deployment, service mesh, GitOps pipeline, canary deployment strategy.

| ID | Task | Deliverable | Effort | Spec Ref | Dependencies |
|----|------|------------|--------|----------|-------------|
| F1 | Configure ArgoCD multi-environment | dev → staging → prod promotion pipeline; auto-sync for dev, manual sync for staging/prod | 2 days | FR-302 | ArgoCD app-of-apps |
| F2 | Create K3s edge manifests | Lightweight IPE deployment: dpe-svc + mat-svc + cap-svc + fea-svc within 1GB RAM; SQLite local cache | 1 week | FR-303, SC-020 | None |
| F3 | Implement Terraform for prod EKS | Multi-AZ RDS, MSK, ElastiCache Redis, S3 for artifacts, IAM roles | 1 week | FR-305 | None |
| F4 | Argo Rollouts canary strategy | 5% → 25% → 100% based on error rate + latency; automatic rollback | 2 days | Sprint 16 | ArgoCD |
| F5 | External Secrets Operator | Kubernetes ESO syncing from AWS Secrets Manager; no env vars in manifests | 3 days | Gap 4 | Terraform |
| F6 | PodDisruptionBudgets for critical services | PDBs for dpe-svc, mat-svc, cap-svc, fea-svc (minAvailable: 1) | 1 day | FR-305 | K8s |
| F7 | HPA for all stateless services | CPU 70% target; minReplicas: 2; custom metric for request queue depth | 1 day | FR-306 | K8s |
| F8 | Harden Airflow for production | Enable webserver auth; configure production logging; add health checks; TLS for Airflow UI | 2 days | R-011 | F1-F7 (infra ready) |

**VERIFY Gates**:
- V-F1: Git push to staging branch → ArgoCD syncs within 60s
- V-F2: K3s cluster runs core services within 1GB RAM; data syncs within 2s post-reconnection
- V-F4: Inject 5% error rate into canary → Argo Rollouts auto-halts and reverts in <2 minutes

---

### Phase G: Commercial & Polish (Weeks 18-20)

**Goal**: Tiered pricing, metering, notification center, and production hardening.

| ID | Task | Deliverable | Effort | Spec Ref | Dependencies |
|----|------|------------|--------|----------|-------------|
| G1 | Implement tiered pricing enforcement | Professional ($5K/mo), Enterprise ($15K/mo), Unlimited ($50K/mo); feature flags per tier; middleware to enforce limits | 1 week | FR-601 | None |
| G2 | Implement usage metering | Per-tenant API call counts, user seat counts, storage consumption; daily aggregation to metering DB | 1 week | FR-602 | G1 |
| G3 | Build notification center | In-app notifications + email (SMTP) + SMS (Twilio) + push (Firebase Cloud Messaging); event-driven from Kafka | 2 weeks | FR-504 | None |
| G4 | Production Grafana dashboards | Service health, event mesh, scheduler performance, financial KPIs, SLA monitoring | 2 days | FR-015 | OTel deployed |
| G5 | Conduct internal security review | SAST (Bandit) + DAST (ZAP) scan across all 14 services; RLS bypass test; mTLS verification; 0 Critical/High findings required | 3 days | Sprint 14 | All security items |

**VERIFY Gates**:
- V-G1: Professional tier user hits Enterprise-only endpoint → 403 Forbidden
- V-G2: API call counter increments correctly; monthly metering report shows per-tenant usage
- V-G3: Notification created → delivered to in-app, email, SMS within 30s
- V-G5: Security report shows 0 Critical/High findings; RLS bypass attempts return 0 rows

---

## Dependency Graph

```
Phase C (Testing) ─────────────────────────────────────────────┐
    │                                                           │
    ├──► Phase D (Governance) ───────────────────────────┐     │
    │         │                                           │     │
    │         └──► Phase E (MLOps + Frontend) ──────┐    │     │
    │              ├── E9 (Unleash) ────► E3 (Autonomy)   │     │
    │              └── E10 (Auth0) ─────► E5 (SCN Portal) │     │
    │                                               │    │     │
    └───────────────────────────────────────────────┼────┼─────┘
                                                    │    │
                                              Phase F (Infra)
                                                    │
                                              Phase G (Commercial)
```

**Critical Path**: C1 (Schemathesis CI) → D1-D5 (Governance) → G5 (Internal security review) = ~12 weeks
**Parallel Tracks**:
- E1-E4 (MLOps/Autonomy) can run parallel with Phase D
- E5-E6 (Frontend) can run parallel with Phase D
- F1-F8 (Infrastructure) can start once D4 (mTLS) is ready

---

## Resource Requirements

| Role | Phase C | Phase D | Phase E | Phase F | Phase G | **Total** |
|------|---------|---------|---------|---------|---------|-----------|
| Backend Engineer | 1 | 2 | 2 | 1 | 1 | **~7 weeks** |
| Frontend Engineer | — | — | 1 | — | — | **~1 week** |
| DevOps/Platform | 1 | 1 | — | 1 | 1 | **~4 weeks** |
| ML/AI Engineer | — | — | 1 | — | — | **~1 week** |
| **Total (engineer-weeks)** | **~2** | **~4** | **~5** | **~3** | **~3** | **~17** |

### Effort Estimate Methodology

plan.md estimates include buffer for: research, documentation, environment setup, iteration, and unknowns (~30% overhead). tasks.md hours represent pure implementation time (coding, config, testing) at 8h/day. The gap between the two is intentional — plan.md is for scheduling, tasks.md is for execution tracking.

Example: Phase E plan.md = 41 days includes 33 days implementation (tasks.md) + 8 days buffer for Unleash/Auth0 configuration, research, and iteration.

---

## Risk Register Updates

| ID | Risk | Probability | Impact | Mitigation | Phase |
|----|------|------------|--------|------------|-------|
| R-003 | Keycloak SAML/SCIM live IdP testing delays | Medium | Medium | Test against Azure AD sandbox early; document per-IdP integration steps | C |
| R-004 | mTLS deployment causes service disruption | Medium | High | Phased rollout: PERMISSIVE → STRICT; Istio monitoring for connection failures | D |
| R-008 | No drift detection — silent model degradation | Medium | High | Implement XmR control charts with 5% threshold; PagerDuty alerting | E |
| R-011 | Airflow not production-ready | Medium | Medium | Enable auth, start scheduler/worker; test DAG execution end-to-end | C |
| R-012 | ISolver constraints ignored | Low | Low | Implement constraint dispatch in ORToolsSolver.solve() | C |
| R-013 | nlp-svc bare pass in error handlers | Low | Low | Replace with logging + fallback responses | C |
| R-014 | K3s edge hardware procurement | Medium | Medium | Test on VMs first; K3s lightweight profile within 1GB constraint | F |
| R-015 | Shadow Mode requires 30+ days of production data | High | Medium | Start collecting Shadow data during Phase C; statistical analysis can begin with 7 days | E |

---

## Constitution Compliance Matrix (Updated)

| Principle | Phase C | Phase D | Phase E | Phase F | Phase G |
|-----------|---------|---------|---------|---------|---------|
| I. RLS | ✓ Schemathesis tests RLS isolation per tenant | ✓ mTLS tenant isolation | ✓ SCN Portal RLS enforced | ✓ K3s edge RLS | ✓ Metering respects tenant boundaries |
| II. Auth | ✓ SCIM 2.0 validates auth | ✓ mTLS cert auth | ✓ Autonomy auth per tenant | ✓ K8s RBAC + mTLS | ✓ Tier-based auth enforcement |
| III. Tests | ✓ Schemathesis CI; 20 solver scenarios; Chaos Mesh; 200 VU k6 | ✓ ACA e-sign tests; BYOK KMS tests | ✓ Shadow validation; guardrail tests | ✓ Canary deployment tests; K3s resilience tests | ✓ Pen-test |
| IV. Events | — | ✓ Governance events (DSAR, retention) logged | ✓ Autonomy state change events | ✓ K3s sync events | ✓ Metering events |
| V. Arch | ✓ Schemathesis as CI gate | ✓ Kong dev portal; KMS tenant isolation | ✓ Progressive Autonomy state machine; PWA offline | ✓ K3s edge profile; Terraform IaC | ✓ Tier enforcement middleware |
| VI. Observability | ✓ k6 CI gate; Chaos observability | ✓ mTLS cert expiry alerts | ✓ Drift metrics in MLflow; pager alerting | ✓ Prod Grafana dashboards; ArgoCD sync alerts | ✓ SLA monitoring dashboard |

---

## Verification Strategy (Updated)

### Per-Phase VERIFY Gates

| Phase | V1 | V2 | V3 |
|-------|----|----|-----|
| C | Schemathesis 0 unhandled 5xx | OR-Tools 20/20 scenarios pass | Airflow DAG executes on schedule |
| D | BYOK denies root `kms:Decrypt` | E-signature locks after 5 failures | mTLS enforced: pod without sidecar cannot connect |
| E | Drift >5% triggers PagerDuty alert | Shadow ROI >10% OTD delta at 95% CI | Guardrail blocks <85% feasibility |
| F | ArgoCD sync within 60s | K3s runs within 1GB RAM | Canary rollback in <2 min |
| G | Professional tier blocked from Enterprise features | Pen-test 0 Critical/High | Notification delivered to 4 channels in <30s |

### Release Gates

| Gate | Phase | Criteria |
|------|-------|----------|
| Testing Gate | End of C | Schemathesis CI green; 200 VU k6 green; Chaos Mesh recovery verified |
| Governance Gate | End of D | SOC 2 evidence collected for 5 trust principles; e-signature working; BYOK KMS functional |
| MLOps Gate | End of E | Drift detection alerting; shadow validation passed; autonomy guardrail tested |
| Infrastructure Gate | End of F | K8s deployment operational; mTLS enforced; canary strategy validated |
| Production Gate | End of G | Internal security review 0 Critical/High; tiered pricing enforced; monitoring dashboards live |

---

## Updated Readiness Projection

> **Superseded (2026-06-22)**: Published score is **85/100** in `READINESS.md`. Table below retained for historical phase tracking only.

| Phase | Start Readiness | End Readiness | Delta | Status |
|-------|-----------------|---------------|-------|--------|
| C | 87 | 90 | +3 | 🟡 PARTIAL (7/8; C-007 BLOCKED) |
| D | 90 | 99 | +9 | ✅ COMPLETE (code delivered) |
| E | 99 | 99 | +0 | ✅ COMPLETE (code delivered) |
| F | 99 | 99 | +0 | ✅ COMPLETE (manifests) |
| G | 99 | 99 | +0 | ✅ COMPLETE (code delivered) |
| **Measured (Gate 2)** | — | **85** | — | **Authoritative** |

**Current Readiness**: **85/100** — see `READINESS.md` (Keycloak C-007 deferred; not 99/100 until production hardening audit)

Key readiness improvements per phase:
- **Phase C** ✅: Testing 80→90 (+10), Governance 75→78 (+3)
- **Phase D**: Security 85→93 (+8), Governance 78→88 (+10)
- **Phase E**: MLOps 40→65 (+25), Frontend 70→82 (+12)
- **Phase F**: Infrastructure 65→85 (+20)
- **Phase G**: Frontend 82→90 (+8), Core Services 98→100 (+2)