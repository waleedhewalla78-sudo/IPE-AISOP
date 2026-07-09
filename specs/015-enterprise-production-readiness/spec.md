# Feature Specification: Enterprise Production Readiness (015)

**Feature**: `015-enterprise-production-readiness`  
**Version**: 1.3  
**Date**: 2026-07-05  
**Status**: Phase 2 complete — Phase 3 ~60% (Gates 6–7, 10 PASS; Gate 8 partial)  
**Depends on**: `014-release2-growth` (commercial R2), `013-release1-odoo-mena` (Odoo R1), platform `v8.2.0`  
**Release target**: `v9.4.0-p3` (Phase 3) after Gates 8–9, 11; Phase 2 tagged `v9.3.0-p2`; Phase 4 target `v10.0.0-e4`  
**Source documents**:
- `docs/strategy/IPE_Enterprise_Deployment_Roadmap.md` (36-week Phases 0–4)
- `IPE_Enterprise_Deployment_Roadmap (4).md` (Downloads — canonical checklist SEC/INF/OBS)
- `PHASE3-VERIFICATION-PROMPT (3).md`
- `IPE-Phase4-Proposal (1).docx` — GTM/SaaS scope
- `IPE-Phase5-Proposal-Gap-Audit.docx` — 131-gap audit + Phase 5 streams
- `IPE_v8_Upgrade_Proposal_SAP_Gap_Analysis (4).md` — v8 Tier 1–3 → Phase 5 Stream B
- `docs/strategy/ENTERPRISE-PROGRAM-STATUS.md`
- `docs/PRD-IPE-COMPREHENSIVE-AS-IS.md`
- Customer readiness: `docs/customer/star-trans/`

---

## Clarifications

### Session 2026-07-04

- Q: Which Odoo version is canonical for Star Trans R1? → A: **Odoo 17 primary; Odoo 19 supported** (customer confirms in field mapping worksheet).
- Q: Does Star Trans R1 require Kubernetes? → A: **No — docker-compose.release1 on 8GB VM**; K8s is enterprise Phase 3 track for multi-customer scale.
- Q: When do SAP/D365 connectors go live? → A: **Scaffold only until customer #2**; Odoo path MUST remain default and fully tested.
- Q: What evidence closes Phase 3? → A: **Gates 6–11 PASS** + git tag `v9.4.0-p3` (see tasks.md).
- Q: How is performance validated post–profile split? → A: **k6-slo.js** for latency SLO; **k6-stress.js** for rate limiter — never combined.

### Session 2026-07-04-b (Phase 4/5 proposals + roadmap v4)

- Q: When does Phase 4 engineering start? → A: **After Gate 11 PASS and tag `v9.4.0-p3`**; PM may parallelize wireframes/pricing (AD-08, OQ-7).
- Q: Terraform or Pulumi for managed SaaS? → A: **Terraform primary** under `infra/terraform/` (AD-07); Pulumi optional later.
- Q: Mobile app in Phase 4? → A: **Responsive web only** (Vite/Tailwind); native apps out of scope (AD-04).
- Q: Where do GDPR/WCAG/SOC2 land? → A: **Phase 5 Stream A** (Gap Audit); Phase 3 closes on K8s gates only.
- Q: Phase 5 vs roadmap Phase 4? → A: **Phase 5 is post-GTM** (compliance cert, Copilot prod, live SAP/D365); not in original 36-week roadmap title but in Gap Audit doc.
- Q: Phase 3 % complete? → A: **~60%** — Gates 6, 7, 10 PASS; Gate 8 partial (`/health` only); 9, 11 pending.

### Session 2026-07-05 (v8 gap doc + Helm R1 fix)

- Q: Where do v8 SAP gap upgrades (Copilot, demand sensing, scenario workbench) land? → A: **Phase 5 Stream B** (FR-015-53–56); Tier 1 = post-GTM priority backlog, not Phase 3 blockers.
- Q: Why did K8s cap-svc CrashLoop? → A: Default `KAFKA_BOOTSTRAP_SERVERS=localhost:9092` — fixed via `IPE_KAFKA_BOOTSTRAP_SERVERS=""` in `values-dev.yaml`.
- Q: What closes Gate 8 feasibility 500? → A: **`scripts/k8s/migrate-k8s-db.ps1 -Seed`** then re-run parity script.
- Q: Is Gate 9 required for R1 tag? → A: **Yes per Constitution VIII** — use `values-prod.yaml` HPA profile; P1 if time-constrained but tag policy says all 6–11.

---

## 1. Vision (what we want to build)

> **Transform IPE from a demo-proven planning platform (32/32 checkpoints, 14/14 Odoo R1 HTTPS) into an enterprise-contractable product: SSO, vault secrets, K8s HA, observability, GDPR/SOC2 readiness, ERP expansion (SAP/D365 scaffolds), and GTM infrastructure — without breaking Release 1/2 customer demos.**

| Dimension | Baseline (v9.3.0-p2) | Enterprise target (Phase 3–4) |
|-----------|----------------------|-------------------------------|
| Auth | Keycloak OIDC + RS256 ✅ | MFA policy docs |
| Secrets | Vault KV + env fallback ✅ | AWS SM for AWS tenants |
| Deploy | docker-compose + Gate scripts ✅ | Helm/K8s + HPA + PDB |
| Observability | Prometheus + Grafana + k6 ✅ | Loki/ELK, status page |
| Compliance | Audit log + DSAR scaffold | GDPR hardened + SOC2 Type I path |
| ERP | Odoo R1 14/14 HTTPS ✅ | + SAP/D365 connector scaffolds → live with customer #2 |
| Commercial | R2 Outcomes/Copilot ✅ | Self-service SaaS + Stripe live |

---

## 2. What we have built (baseline)

| Asset | Status | Evidence |
|-------|--------|----------|
| Platform v8.2.0 (U1–U8) | ✅ | `READINESS.md`, tag `v8.2.0` |
| Release 1 Odoo 14/14 HTTPS | ✅ | `scripts/security/verify-gate5.ps1` |
| Release 2 5/5 | ✅ | Gate 5 bundle |
| Enterprise Phase 0 | ✅ | Option B B1–B5 |
| Enterprise Phase 1 | ✅ | SIGTERM, pybreaker, k6 profile split |
| Enterprise Phase 2 | ✅ | Gates 1–5, k6 SLO/stress, tag `v9.3.0-p2` |
| Helm chart (`helm/ipe`) | 🔄 Scaffold | Chart.yaml, values-*, ranged templates |
| SAP/D365 scaffolds | 🔄 | `services/connector/app/connectors/` |
| Customer readiness (Track B) | ✅ | `docs/customer/star-trans/*` |

---

## 3. Scope — Enterprise phases

### Phase 0 — Security Foundation ✅ COMPLETE

**User story:** As a **CISO**, I need corporate IdP SSO and vault-backed secrets so I can approve a security review.

| ID | Requirement | Status |
|----|-------------|--------|
| FR-015-01 | Keycloak OIDC integration | ✅ |
| FR-015-02 | RS256 JWT signing + rotation docs | ✅ |
| FR-015-03 | Vault provider in secrets_manager | ✅ |
| FR-015-04 | TLS termination at Kong + HSTS | ✅ |
| FR-015-05 | API request audit middleware | ✅ |

### Phase 1 — Production Infrastructure ✅ COMPLETE (compose track)

| ID | Requirement | Status |
|----|-------------|--------|
| FR-015-10 | Helm deploy all services | 🔄 Deferred to Phase 3 |
| FR-015-16 | Graceful SIGTERM | ✅ |
| FR-015-17 | Circuit breakers (pybreaker) | ✅ |
| FR-015-39 | Network isolation | ✅ Docker Gate 2 |

### Phase 2 — Observability & Reliability ✅ COMPLETE

| ID | Requirement | Status |
|----|-------------|--------|
| FR-015-20 | Prometheus `/metrics` | ✅ Gate 1 |
| FR-015-21 | Grafana dashboards | ✅ 6 dashboards |
| FR-015-22 | Structured JSON logging | ✅ |
| FR-015-23 | OpenTelemetry traces | ✅ |
| FR-015-25 | SLO/SLI + k6 baselines | ✅ P95 293ms SLO; stress 429 |
| FR-015-26 | Gates 1–5 + R1/R2 regression | ✅ |

### Phase 3 — Scale & Compliance 🔄 IN PROGRESS

**User story:** As a **platform operator**, I need Kubernetes packaging and ERP expansion scaffolds so we can onboard enterprise tenants and future SAP/D365 customers without rewriting Odoo.

| ID | Requirement | Status |
|----|-------------|--------|
| FR-015-30 | GDPR export/erasure production-hardened | ⬜ |
| FR-015-31 | WCAG 2.1 AA audit remediation | ⬜ |
| FR-015-32 | SOC 2 Type I gap assessment | ⬜ |
| FR-015-33 | Load test 500 VU in CI | ⬜ |
| FR-015-34 | SAP S/4HANA connector (5 entities) | 🔄 Scaffold |
| FR-015-35 | D365 connector (5 entities) | 🔄 Scaffold |
| FR-015-36 | API versioning v1/v2 | ⬜ |
| FR-015-37 | Helm chart lint + kind deploy (Gate 6–7) | ✅ Gates 6–7 PASS |
| FR-015-38 | Compose–K8s parity (Gate 8) | ✅ Gate 8 PASS 2026-07-05 |
| FR-015-39 | HPA smoke + R1 on K8s (Gate 9–11) | ⬜ |

### Phase 4 — GTM & Growth ⬜ NOT STARTED

| ID | Requirement | Status |
|----|-------------|--------|
| FR-015-40 | Tenant self-service provisioning API | ⬜ |
| FR-015-41 | Stripe billing live mode | ⬜ |
| FR-015-42 | Developer portal (OpenAPI) | ⬜ |
| FR-015-43 | Python + JS SDKs | ⬜ |
| FR-015-44 | Knowledge base (50 articles) | ⬜ |
| FR-015-45 | Customer health dashboard | ⬜ |
| FR-015-46 | Managed SaaS Terraform module (<30 min deploy) | ⬜ |
| FR-015-47 | Mobile-responsive web (dashboard + approvals) | ⬜ |
| FR-015-48 | On-prem Ansible / air-gap automation package | ⬜ |

### Phase 5 — Enterprise Maturity ⬜ PROPOSED (post-GTM)

**User story:** As a **regulated enterprise buyer**, I need SOC 2 evidence, WCAG compliance, and advanced planning capabilities **so that** IPE competes credibly with SAP IBP in enterprise RFPs.

| ID | Requirement | Status | Stream |
|----|-------------|--------|--------|
| FR-015-50 | SOC 2 Type II evidence path | ⬜ | A |
| FR-015-51 | GDPR export/erasure production-hardened | ⬜ | A |
| FR-015-52 | WCAG 2.1 AA remediation (core screens) | ⬜ | A |
| FR-015-53 | S&OP collaboration workflow | ⬜ | B |
| FR-015-54 | Copilot production (v8 U1) | ⬜ | B |
| FR-015-55 | Scenario workbench + demand sensing (v8 U2–U3) | ⬜ | B |
| FR-015-55a | Supply orchestration + order mgmt (v8 U4–U5) | ⬜ | B |
| FR-015-55b | Predictive maintenance + design AI (v8 U6–U7) | ⬜ | B |
| FR-015-56 | Event sourcing / CQRS / GraphQL (architectural) | ⬜ | B |
| FR-015-57 | Live SAP S/4HANA connector (customer #2+) | ⬜ | C |
| FR-015-58 | Live D365 connector (customer #2+) | ⬜ | C |
| FR-015-59 | Partner program + advanced analytics | ⬜ | C |

---

## 4. User stories (active)

### US-015-P3-01 — Platform operator deploys Release 1 on Kubernetes

**As a** platform operator, **I want** to install IPE via Helm on a kind/AKS cluster **so that** we validate K8s parity before enterprise customers request HA.

**Acceptance:**
- `helm lint` passes for `values-release1.yaml` and `values-prod.yaml`
- All R1 pods reach Ready; in-pod `/health` returns 200
- Compose–K8s parity script reports equivalent JSON structure on core endpoints

### US-015-P3-02 — Architect evaluates SAP/D365 expansion

**As an** integration architect, **I want** SAP and D365 connector scaffolds with a unified registry **so that** customer #2 onboarding does not fork the Odoo codebase.

**Acceptance:**
- Registry returns scaffold engines for `sap` and `d365`
- Unit tests pass without live ERP credentials
- Odoo live path unchanged (existing sync API)

### US-015-R1-01 — Star Trans goes live on compose (Track B)

**As** Star Trans IT, **I want** deployment guide, UAT plan, and field mapping worksheet **so that** we can sign SOW and run UAT on staging Odoo.

**Acceptance:**
- All five Track B documents published under `docs/customer/star-trans/`
- UAT blocked only on external: signed SOW + Odoo staging access

---

## 5. Out of scope (015)

- Replacing Odoo as system of record (IPE remains planning layer)
- Live SAP/D365 sync without contracted customer credentials
- On-prem air-gapped full automation (document only in Phase 4)
- Full SAP IBP feature parity (positioning doc only)
- Breaking Release 1 8 GB VM compose profile

---

## 6. Success criteria

| ID | Criterion | Target | Status |
|----|-----------|--------|--------|
| SC-015-01 | Enterprise Phase 0 items | SEC-001–005 signed off | ✅ |
| SC-015-02 | K8s staging deploy | `helm install` green in < 30 min | 🔄 |
| SC-015-03 | Observability | All services scraped + 6 Grafana dashboards | ✅ |
| SC-015-04 | Load test | k6 SLO P95 read < 500ms; stress confirms 429 | ✅ |
| SC-015-05 | Compliance | GDPR export < 10 min for 1M rows | ⬜ |
| SC-015-06 | No R1/R2 regression | 14/14 + 5/5 after each phase gate | ✅ |
| SC-015-07 | Phase 3 gates | Gates 6–8, 10 PASS; 9, 11 pending | 🔄 ~70% |
| SC-015-08 | Customer readiness | Track B package complete | ✅ |
| SC-015-09 | Phase 4 GTM | Self-service + Stripe sandbox | ⬜ |
| SC-015-10 | Phase 5 maturity | SOC 2 path + WCAG critical fixes | ⬜ |

---

## 7. Assumptions

- Star Trans R1 go-live uses **docker-compose.release1.yml**, not K8s.
- Helm/kind validation runs in CI or engineer workstation with kubectl + helm installed.
- SAP/D365 remain **scaffold** until second ERP customer is contracted.
- Commercial pricing (OQ-7) does not block engineering Phase 3 but blocks customer SOW signature.

---

*Spec version 1.3 — `/speckit.specify` 2026-07-05*
