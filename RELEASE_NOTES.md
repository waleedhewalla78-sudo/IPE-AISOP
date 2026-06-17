# IPE Platform — Release Notes

## v1.0.0 (Initial Production Release)

**Release Date**: 2026-06-15

**Product**: Intelligent Planning Engine (IPE) — An ERP-agnostic Advanced Planning & Scheduling (APS) platform.

---

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

---

### Known Limitations & Accepted Exceptions

| Issue | Scope | Rationale |
|-------|-------|-----------|
| vitest v2.1.9 (critical) | Dev dependency | Test runner only; not shipped to production. Patched version 3.2.6+ available. |
| esbuild v0.21.5 (high) | Dev dependency | Build tool used at compile time; not exposed in production runtime. |
| vite v5.4.21 (high) | Dev dependency | Dev server only; production serves via nginx/Kong. |
| Multi-echelon ATP | Deferred to Phase 3 | Current pATP handles single-echelon. Multi-echelon (multi-site) deferred for scope containment. |
| SAP/D365 live connectors | Deferred | Adapter scaffolding complete. Live integration requires enterprise customer engagement. |
| What-If Scenario UI | Deferred | API endpoint exists (POST /simulate). Frontend implementation planned post-launch. |
| Mobile app | Deferred | Responsive web UI delivered. Native mobile app (Flutter) planned for v1.2. |
| mypy strict type-checking | See note | Config added to `pyproject.toml`. Full enforcement blocked by transitively-typed dependencies. |

---

### Upgrade Instructions (Staging → Production)

1. **Verify ArgoCD health**:
   ```bash
   argocd app list
   argocd app get ipe-infrastructure --refresh
   ```

2. **Promote database migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Promote ML models**:
   ```bash
   # Run evaluation and promote if better than current production model
   airflow dags trigger evaluate_and_promote_models
   ```

4. **Verify all 9 microservices + frontend are Healthy**:
   ```bash
   kubectl get pods -n ipe-platform
   ```

5. **Run smoke test**:
   ```bash
   make perf-k6   # Verify p95 < 2000ms
   make e2e-test  # Verify critical path
   ```

6. **Switch DNS**:
   ```bash
   # Update Route53 record to point at production Kong proxy
   ```

### Rollback Procedure

In the event of a failed deployment:
- **ArgoCD**: `argocd app rollback ipe-services --to-revision <N-1>`
- **Database**: Restore RDS snapshot (see `docs/runbooks/disaster-recovery.md`)
- **ML Models**: Revert S3 model artifact to previous version
