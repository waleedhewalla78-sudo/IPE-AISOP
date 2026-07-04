# Plan — 015 Enterprise Production Readiness

**Feature**: `015-enterprise-production-readiness`  
**Date**: 2026-07-04  
**Plan version**: 2.0  
**Tech stack**: FastAPI, React/Vite, PostgreSQL 16 + RLS, Redis, Kafka, Kong, Keycloak, Vault, Prometheus/Grafana, Helm 3, Kubernetes 1.28+

---

## 1. Architecture decisions

| Decision | Choice | Alternatives rejected |
|----------|--------|----------------------|
| Identity | Keycloak 24+ OIDC + RS256 | Custom JWT only (blocks enterprise) |
| Secrets | Vault primary, AWS SM for AWS tenants | Env vars in prod |
| Orchestration | Helm 3 (`helm/ipe`) → kind/AKS/EKS | Raw manifests only; legacy `infrastructure/k8s/helm/ipe-platform` superseded by `helm/ipe` |
| Observability | Prometheus + Grafana + OTel | ELK-only |
| ERP expansion | `app/connectors/` registry (Odoo live via existing API; SAP/D365 scaffold) | Monolithic ERP adapter |
| Demo preservation | `release1` compose frozen; K8s `values-release1.yaml` mirrors profile | Merge profiles |
| Performance testing | Two k6 profiles (SLO + stress) | Single overloaded script |

---

## 2. Phase status map

| Phase | Tag | Gate evidence | Status |
|-------|-----|---------------|--------|
| 0 Security | — | Option B B1–B5 | ✅ |
| 1 Hardening | — | SIGTERM, pybreaker, network isolation | ✅ |
| 2 Observability + Gates | `v9.3.0-p2` | Gates 1–5, k6, R1 14/14, R2 5/5 | ✅ |
| 3 Scale/Compliance | `v9.4.0-p3` | Gates 6–11 | 🔄 |
| 4 GTM | `v10.0.0-e4` (TBD) | Stripe sandbox, tenant API | ⬜ |

---

## 3. Phase 3 implementation (active)

### Stream 1 — Kubernetes / Helm (PRIMARY)

| Component | Path | Notes |
|-----------|------|-------|
| Chart | `helm/ipe/Chart.yaml` | appVersion `9.4.0-p3` |
| Values | `values.yaml`, `values-dev.yaml`, `values-release1.yaml`, `values-prod.yaml` | R1 minimal vs full enterprise |
| Templates | `templates/deployments.yaml`, `services.yaml`, `hpa.yaml`, `pdb.yaml`, `networkpolicy.yaml`, `configmap.yaml`, `secrets.yaml`, `web-ui.yaml` | Ranged over `.Values.services` |
| Scripts | `scripts/k8s/deploy-kind.sh`, `verify-k8s.sh`, `test-compose-k8s-parity.py` | kind-first validation |
| Docs | `docs/operations/K8S-DEPLOYMENT-GUIDE.md` | |

**Gate 6:** `helm lint` + `helm template` dry-run (prod + release1 values)  
**Gate 7:** kind deploy; all pods Ready; in-pod health 200  
**Gate 8:** parity script — same JSON keys on `/health`, feasibility, material endpoints  
**Gate 9:** HPA scales under synthetic CPU load (full profile only)

### Stream 2 — SAP / D365 scaffolds

| Component | Path | Notes |
|-----------|------|-------|
| Registry | `services/connector/app/connectors/registry.py` | `ERPTYPE` enum; Odoo via existing handlers |
| SAP | `app/connectors/sap/mapper.py`, `sync_engine.py` | OData field maps; no-op sync until credentials |
| D365 | `app/connectors/d365/sync_engine.py` | Dataverse pattern; no-op sync |
| Tests | `services/connector/tests/test_erp_scaffolds.py` | Import + no-op sync unit tests |

**Gate 10:** pytest scaffold tests green; no live ERP network

### Stream 3 — Compliance (deferred within Phase 3)

| Workstream | Touch points |
|------------|--------------|
| GDPR | Harden `dpe-svc/dsar.py`, retention jobs |
| WCAG | Audit `apps/web` core R1 screens |
| SOC 2 | Gap doc under `docs/compliance/` |
| k6 500 VU CI | `.github/workflows/` job on staging |

### Stream 4 — Customer Track B (parallel) ✅

Deliverables under `docs/customer/star-trans/` — complete; UAT waits on SOW.

---

## 4. Testing strategy

| Layer | Gate | Script / path |
|-------|------|---------------|
| Unit | Vault, JWT, ERP scaffolds | pytest |
| Integration | Keycloak, Odoo sync | Gate 4, Option B |
| E2E | R1 + R2 | `verify-gate5.ps1` |
| Load | k6 SLO + stress | `k6-slo.js`, `k6-stress.js` |
| K8s | Helm + parity | Gates 6–8 |
| Regression | R1/R2 after P3 | T200–T201 |

---

## 5. Constitution check

| Principle | Phase 3 compliance |
|-----------|-------------------|
| I RLS | No new tenant tables without RLS in same migration |
| II Auth | K8s ingress preserves Kong auth; no open routes |
| III Tests | Scaffold tests required before Gate 10 PASS |
| IV Events | R1 profile may omit Kafka; document in values-release1 |
| V Architecture | Helm ports match Dockerfile canonical map |
| VI Observability | ServiceMonitor or prometheus.io annotations on K8s pods |
| VII Customer-first | R1 compose path unchanged; K8s optional for Star Trans |
| VIII Gates | No `v9.4.0-p3` tag without Gates 6–11 evidence |

---

## 6. Rollout milestones (revised)

| Milestone | Tag | Gate |
|-----------|-----|------|
| E2 Observability + Security | `v9.3.0-p2` | Gates 1–5 ✅ |
| E3 K8s + ERP scaffolds | `v9.4.0-p3` | Gates 6–11 |
| E4 Compliance hardening | `v9.5.0-p3b` | GDPR + SOC2 gap close |
| E5 GTM | `v10.0.0-e4` | Stripe + tenant API |

---

*Plan version 2.0 — `/speckit.plan` 2026-07-04*
