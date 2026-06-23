# IPE Platform — Release Notes

## v1.0.0 — Autonomous Production Planning (V5.0 Convergence)

**Release Date**: 2026-06-21

**Feature**: `003-autonomous-planning-v5` — closes the 80/20 gap from demo-ready (~78%) to enterprise-ready production release.

### R1 — Closed-loop scheduling
- Schedule persistence to CDM (`cdm_work_order.version`, MO optimistic locking)
- `GET /capacity/schedule/active`, `POST /capacity/schedule/approve`
- Demand priority wiring via `priority_score`
- Kafka `ipe.schedule.approved` + connector Odoo sync
- Demo checkpoint 16/16 (persist-after-approve)

### R2 — Planner UX & AI brain
- Heuristic CP-SAT fallback, schedule control panel, XAI explain panel
- Tiered LLM: Anthropic → Ollama → HTTP 503 (no silent rule fallback when routing enabled)
- Admin LLM tier status (`GET /copilot/llm-status`)

### R3 — Enterprise governance
- MDR composite gate (70%) before scheduling
- MDR dashboard (`/mdr`), Digital Twin sandbox on Schedule page
- Resolution Center financial columns (COGM / revenue / margin)
- War Room auto-aggregate on supplier delay (`GET /war-room/aggregate`)

### R4 — Production hardening
- Chaos Mesh staging runner + evidence collection (`infrastructure/chaos/`)
- SAP / D365 sandbox validation scripts (`scripts/test-sap-sandbox.*`, `scripts/test-d365-sandbox.*`)
- Airflow in default docker-compose (LocalExecutor + init DB)
- k6 200 VU re-cert (`tests/performance/k6/load-test-200vu.js`, SC-012: p95 <5s, errors <1%)
- R4 orchestrator: `scripts/r4-verify.ps1`

### Tag instructions

When staging evidence is attached under `specs/003-autonomous-planning-v5/evidence/r4/`:

```bash
git tag -a v1.0.0 -m "IPE v1.0.0 — Autonomous Production Planning V5.0"
git push origin v1.0.0
```

---

## v1.0.0-rc1 (Prior stabilization)

**Release Date**: 2026-06-15

**Product**: Intelligent Planning Engine (IPE) — An ERP-agnostic Advanced Planning & Scheduling (APS) platform.

### Capabilities Delivered

| Phase | Domain | Key Deliverables |
|-------|--------|-----------------|
| 0 | Foundation | Monorepo, CDM schema, migration system, RLS, CI pipeline, 72 unit tests |
| 1 | Core AI | Demand priority engine, material netting, probabilistic ATP, Monte Carlo simulations, feasibility scoring, OR-Tools CP-SAT scheduler |
| 2 | Orchestration | Airflow DAGs (retrain, evaluate, promote), SSE Copilot streaming, Executive Analytics, Weather signal integration via NWS API |
| 3 | Demand Sensing | Multi-horizon demand classification, weather-correlated demand signals, Kafka event-driven architecture |
| 4 | Enterprise | SAP/D365 adapter scaffolding, Kong API Gateway (JWT + rate limiting), MLflow model tracking, Playwright E2E tests |
| 5 | Hardening | Alert Engine (rules + SMTP), What-If simulation, audit log immutability, Locust performance tests |
| 6 | Go-Live | Helm chart + ArgoCD manifests, DR/IR/onboarding runbooks, k6 validation, gitleaks security scan, Grafana dashboards, Prometheus SLA alerts |

### v1.0.0-rc1 Stabilization Verification (2026-06-22)

Gate 2 integration evidence (`specs/002-release-stabilization-gates/evidence/gate-2/`):

| Suite | Result |
|-------|--------|
| `test_sprint2_e2e.py` | 25 passed, 1 skipped |
| `test_phase5_6_e2e.py` | 16 passed |
| `critical_path_test.py` | 5/5 steps |
| k6 `load-test-phase56.js` | 0% http_req_failed, p95 ~1.6s |

Published readiness: **85/100** — see `READINESS.md`.

---

### Known limitations

| Issue | Scope | Rationale |
|-------|-------|-----------|
| vitest v2.1.9 (critical) | Dev dependency | Test runner only; not shipped to production |
| SAP/D365 live connectors | R4 sandbox only | Mapper + optional live OData when credentials provided |
| Keycloak enterprise IdP | Residual risk | SAML/SCIM blocked until Azure AD/Okta sandbox available |

---

### Upgrade Instructions (Staging → Production)

1. **Verify ArgoCD health**: `argocd app list`
2. **Promote database migrations**: `alembic upgrade head`
3. **Run R4 verification**: `.\scripts\r4-verify.ps1` and `.\scripts\run-k6-200vu.ps1`
4. **Attach chaos evidence** from staging: `infrastructure/chaos/collect-evidence.ps1`
5. **Tag release**: see v1.0.0 tag instructions above

### Rollback Procedure

- **ArgoCD**: `argocd app rollback ipe-services --to-revision <N-1>`
- **Database**: Restore RDS snapshot (see `docs/runbooks/disaster-recovery.md`)
- **ML Models**: Revert S3 model artifact to previous version
