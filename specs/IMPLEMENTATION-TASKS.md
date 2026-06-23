# IPE Platform — Actionable Task Lists for Implementation

**Generated:** 2026-06-21 (based on cross-artifact analysis)
**Total Tasks:** 52 (Phase 1: 33, Phase 2: 12, Phase 3: 7)

---

## PHASE 1: Documentation Synchronization (1-2 hours)

**Goal:** Align spec.md, plan.md, tasks.md, quality-checklists.md so all artifacts reflect actual completion state.
**Priority:** CRITICAL — blocks accurate status reporting for demo.

### 1.1 Update spec.md Open Issues Tables (6 items)

| # | Line | Current | Change To | Evidence |
|---|------|---------|-----------|----------|
| 1.1.1 | 64 | `❌ NOT STARTED` (Chaos Mesh) | `✅ RESOLVED — Chaos Mesh deployed with 5 experiments` | TASK-P9-004 |
| 1.1.2 | 66 | `❌ NOT STARTED` (K3s edge) | `✅ RESOLVED — K3s Edge Gateway with SQLite cache, store-and-forward` | TASK-P8-003 |
| 1.1.3 | 69 | `❌ NOT STARTED` (Drift detection) | `✅ RESOLVED — NLP accuracy, pATP reliability, feasibility distribution drift` | TASK-P7-004 |
| 1.1.4 | 70 | `❌ NOT STARTED` (Shop Floor PWA) | `✅ RESOLVED — PWA with Service Worker, IndexedDB offline queue, voice-to-text` | TASK-P1-001 |
| 1.1.5 | 71 | `❌ NOT STARTED` (SCN Portal) | `✅ RESOLVED — SCN Portal with supplier scorecards, RFQ management, Auth0` | TASK-P4-016 |
| 1.1.6 | 73 | `❌ NOT STARTED` (E-signature) | `✅ RESOLVED — FDA 21 CFR Part 11 e-signature with lockout, audit trail` | TASK-P9-010 |

### 1.2 Update spec.md Sprint Checklists (15 items)

| # | Line | Current | Change To |
|---|------|---------|-----------|
| 1.2.1 | 135 | `Sprint 8: Autonomous MLOps Pipeline — NOT STARTED` | `— PARTIAL` |
| 1.2.2 | 136 | `- [ ] MLflow tracking server deployment` | `- [x] MLflow tracking server deployment ✅` |
| 1.2.3 | 137 | `- [ ] Airflow DAGs for automated retraining` | `- [x] Airflow DAGs for automated retraining ✅` |
| 1.2.4 | 138 | `- [ ] Drift detection for NLP classifier accuracy` | `- [x] Drift detection for NLP classifier accuracy ✅` |
| 1.2.5 | 139 | `- [ ] Drift detection for pATP reliability` | `- [x] Drift detection for pATP reliability ✅` |
| 1.2.6 | 141 | `- [ ] Model versioning and approval workflow` | `- [x] Model versioning and approval workflow ✅` |
| 1.2.7 | 156 | `Sprint 12: Multi-ERP, Edge & FL — NOT STARTED` | `— COMPLETE` |
| 1.2.8 | 157 | `- [ ] SAP S/4HANA adapter (BAPI/OData)` | `- [x] SAP S/4HANA adapter (BAPI/OData) ✅` |
| 1.2.9 | 158 | `- [ ] D365 BC adapter (Dataverse/OData)` | `- [x] D365 BC adapter (Dataverse/OData) ✅` |
| 1.2.10 | 159 | `- [ ] K3s Edge Gateway store-and-forward sync` | `- [x] K3s Edge Gateway store-and-forward sync ✅` |
| 1.2.11 | 160 | `- [ ] Federated Learning for supplier reliability` | `- [x] Federated Learning for supplier reliability ✅` |
| 1.2.12 | 181 | `Sprint 16: Production Go-Live & Canary — NOT STARTED` | `— COMPLETE` |
| 1.2.13 | 182 | `- [ ] Terraform for Prod EKS, Multi-AZ RDS, MSK` | `- [x] Terraform for Prod EKS, Multi-AZ RDS, MSK ✅` |
| 1.2.14 | 183 | `- [ ] ArgoCD app-of-apps bootstrap` | `- [x] ArgoCD app-of-apps bootstrap ✅` |
| 1.2.15 | 184-186 | 3 remaining items `- [ ]` | `- [x]` with ✅ |

### 1.3 Update spec.md Gap Analysis Tables (4 items)

| # | Line | Current | Change To |
|---|------|---------|-----------|
| 1.3.1 | 269 | `❌ Not implemented` (FDA Part 11) | `✅ Implemented — e-signature with lockout, audit trail` |
| 1.3.2 | 281 | `❌ Not implemented` (K3s Edge) | `✅ Implemented — K3s Edge Gateway with SQLite cache` |
| 1.3.3 | 294 | `❌ Not implemented` (Chaos Engineering) | `✅ Implemented — Chaos Mesh with 5 experiments` |
| 1.3.4 | 310 | `❌ Not implemented` (Drift Detection) | `✅ Implemented — NLP, pATP, feasibility drift detection` |

### 1.4 Update spec.md Success Criteria (2 items)

| # | Line | Current | Change To |
|---|------|---------|-----------|
| 1.4.1 | 719 | `❌ K3s edge deployment not created` | `✅ K3s edge deployment created (TASK-P8-003)` |
| 1.4.2 | 728 | `❌ Drift detection not implemented` | `✅ Drift detection implemented (TASK-P7-004)` |

### 1.5 Update spec.md Sprint 12 Status (1 item)

| # | Line | Current | Change To |
|---|------|---------|-----------|
| 1.5.1 | 1082 | `🔴 NOT STARTED — Odoo adapter only...` | `🟢 COMPLETE — SAP/D365 adapters, K3s Edge, FL all done` |

### 1.6 Update spec.md Phase Task Tables (17 items)

| # | Line | Current | Change To |
|---|------|---------|-----------|
| 1.6.1 | 1191 | `MLflow model registry ❌` | `✅ TASK-P7-005` |
| 1.6.2 | 1193 | `Drift detection ❌` | `✅ TASK-P7-004` |
| 1.6.3 | 1194 | `Drift alerting ❌` | `✅ TASK-P7-004` |
| 1.6.4 | 1196 | `Model versioning ❌` | `✅ TASK-P7-005` |
| 1.6.5 | 1197 | `MLOps dashboard ❌` | `✅ TASK-P7-006` |
| 1.6.6 | 1199 | `Airflow DAG feasibility ❌` | `✅ TASK-P7-003` |
| 1.6.7 | 1201 | `Human Approval Gate ❌` | `✅ TASK-P10-003` |
| 1.6.8 | 1237 | `FDA Part 11 e-sig ❌` | `✅ TASK-P9-010` |
| 1.6.9 | 1239 | `FDA Part 11 lockout ❌` | `✅ TASK-P9-010` |
| 1.6.10 | 1240 | `Compliance evidence ❌` | `✅ TASK-P9-007` |
| 1.6.11 | 1257 | `K3s edge manifests ❌` | `✅ TASK-P8-003` |
| 1.6.12 | 1258 | `K3s lightweight profile ❌` | `✅ TASK-P8-003` |
| 1.6.13 | 1262 | `Terraform prod ❌` | `✅ TASK-P11-001` |
| 1.6.14 | 1263 | `Argo Rollouts canary ❌` | `✅ TASK-P11-004` |
| 1.6.15 | 1272-1284 | 13 MLOps items `❌` | `✅` (MLflow, Airflow, Drift, Model Registry, Dashboard) |
| 1.6.16 | 1285 | `Explainability dashboard ❌` | `✅ TASK-P10-001` (XAI dashboard) |
| 1.6.17 | 1286 | `A/B testing framework ❌` | `✅ TASK-P10-002` (Shadow ROI) |

**Phase 1 Effort:** ~1-2 hours (find-and-replace with verification)
**Phase 1 Verification:** `grep -c "NOT STARTED" specs/000-project-completion/spec.md` should drop from ~43 to ~5

---

## PHASE 2: Critical API Test Coverage (1-2 weeks)

**Goal:** Add tests for 10 critical business endpoints + 4 compliance endpoints.
**Priority:** HIGH — closes the biggest quality gap (37% → ~55% API test coverage).
**Pattern:** Use dpe-svc dependency override approach (most robust for validation testing).

### 2.1 dpe-svc: Core Business Logic (6 tests)

| # | Endpoint | Test File | Test Cases | Priority |
|---|----------|-----------|------------|----------|
| 2.1.1 | `POST /ctp/evaluate` | `services/dpe-svc/tests/test_api_ctp.py` | Valid CTP request → 200 with feasibility_score; Invalid MO ID → 422; Missing fields → 422; Empty BOM → 200 with score=0 | P0 |
| 2.1.2 | `POST /demand/sense` | `services/dpe-svc/tests/test_api_demand_sense.py` | Valid demand sense → 200 with forecast; Empty demand lines → 422; Invalid product_id → 422 | P0 |
| 2.1.3 | `POST /financial/project` | `services/dpe-svc/tests/test_api_financial.py` | Valid projection → 200 with COGM; Invalid MO → 422; Zero quantity → 200 with zero costs | P0 |
| 2.1.4 | `POST /sop/solve` | `services/dpe-svc/tests/test_api_sop.py` | Valid S&OP solve → 200 with gap analysis; Empty forecast → 200 with empty gaps | P1 |
| 2.1.5 | `POST /cost-accounting/full` | `services/dpe-svc/tests/test_api_cost.py` | Valid cost accounting → 200 with P&L; Missing cost elements → 422 | P1 |
| 2.1.6 | `GET /dsar/requests` | `services/dpe-svc/tests/test_api_dsar.py` | List DSARs → 200; Create + List → 200 with 1 item | P1 |

### 2.2 fea-svc: Feasibility Pipeline (4 tests)

| # | Endpoint | Test File | Test Cases | Priority |
|---|----------|-----------|------------|----------|
| 2.2.1 | `POST /feasibility/rescore/{mo_id}` | `services/fea-svc/tests/test_api_rescore.py` | Valid rescore → 200 with updated scores; Invalid UUID → 422; Unknown MO → 200 with fallback scores | P0 |
| 2.2.2 | `GET /feasibility/queue` | `services/fea-svc/tests/test_api_queue.py` | Empty queue → 200 with []; Queue after rescore → 200 with sorted list | P0 |
| 2.2.3 | `GET /feasibility/kpis` | `services/fea-svc/tests/test_api_kpis.py` | KPIs with no data → 200 with null otd_pct; KPIs after scoring → 200 with metrics | P0 |
| 2.2.4 | `GET /feasibility/compliance-kpis` | `services/fea-svc/tests/test_api_compliance.py` | Compliance KPIs → 200 with control status | P1 |

### 2.3 cap-svc: Capacity Scheduling (3 tests)

| # | Endpoint | Test File | Test Cases | Priority |
|---|----------|-----------|------------|----------|
| 2.3.1 | `POST /capacity/solve` | `services/cap-svc/tests/test_api_solve.py` | Valid solve → 200 with assignments; Empty MOs → 422; Invalid WC → 200 with partial results | P0 |
| 2.3.2 | `POST /capacity/network-optimize` | `services/cap-svc/tests/test_api_network.py` | Valid optimization → 200 with make-vs-transfer; Single plant → 200 with no transfers | P0 |
| 2.3.3 | `POST /capacity/green-schedule` | `services/cap-svc/tests/test_api_green.py` | Valid green schedule → 200 with carbon score; beta=0 → same as regular schedule | P1 |

### 2.4 mat-svc: Material CTP (2 tests)

| # | Endpoint | Test File | Test Cases | Priority |
|---|----------|-----------|------------|----------|
| 2.4.1 | `POST /material/ctp` | `services/mat-svc/tests/test_api_ctp.py` | Valid CTP → 200 with feasibility; Missing components → 200 with partial; Unknown MO → 422 | P0 |
| 2.4.2 | `POST /material/ctp/batch` | `services/mat-svc/tests/test_api_ctp_batch.py` | Batch CTP → 200 with results array; Empty batch → 422 | P1 |

### 2.5 Test Infrastructure Setup

| # | Task | Description | Effort |
|---|------|-------------|--------|
| 2.5.1 | Create shared test fixtures | `services/shared/tests/conftest.py` with `_auth_headers()`, `TEST_TENANT_ID`, `TEST_USER_ID` constants | 30 min |
| 2.5.2 | Document test pattern | Add section to AGENTS.md: "How to write API tests" with dependency override pattern | 15 min |
| 2.5.3 | Verify all tests pass | Run `pytest services/<svc>/tests/test_api_*.py -v` for each service | 15 min |

**Phase 2 Effort:** ~1-2 weeks (40-80 hours)
**Phase 2 Verification:** `pytest --co -q services/*/tests/test_api_*.py | wc -l` should show 49+ new tests
**Phase 2 Coverage Target:** API test coverage 37% → 55%+

---

## PHASE 3: Infrastructure & Demo Readiness (2-3 days)

**Goal:** Ensure all services run, Kong routes work, and demo is reproducible.
**Priority:** MEDIUM — needed for live demo but not blocking documentation.

### 3.1 Docker Stack Recovery

| # | Task | Command/Action | Verification |
|---|------|----------------|--------------|
| 3.1.1 | Restart Docker daemon | Manual restart via Docker Desktop | `docker ps` returns container list |
| 3.1.2 | Rebuild all images | `docker compose -f infrastructure/docker/docker-compose.yml up -d --build` | All 26 containers running |
| 3.1.3 | Verify Kong health | `curl localhost:8000` returns OK | HTTP 200 |
| 3.1.4 | Verify all 16 services through Kong | Test each upstream port (8001-8015) | All return 200/422 |

### 3.2 Kong Route Verification

| # | Service | Port | Route Test | Expected |
|---|---------|------|------------|----------|
| 3.2.1 | dpe-svc | 8001 | `GET /api/v1/demand/queue` | 200 |
| 3.2.2 | mat-svc | 8002 | `GET /api/v1/material/health` | 200 |
| 3.2.3 | cap-svc | 8003 | `GET /api/v1/capacity/health` | 200 |
| 3.2.4 | fea-svc | 8004 | `GET /api/v1/feasibility/kpis` | 200 |
| 3.2.5 | del-svc | 8006 | `GET /api/v1/delay/health` | 200 |
| 3.2.6 | nlp-svc | 8007 | `GET /api/v1/copilot/health` | 200 |
| 3.2.7 | sustain-svc | 8012 | `GET /api/v1/sustainability/health` | 200 |
| 3.2.8 | quality-svc | 8013 | `GET /api/v1/quality/health` | 200 |
| 3.2.9 | scn-svc | 8014 | `GET /api/v1/scn/health` | 200 |
| 3.2.10 | network-svc | 8015 | `GET /api/v1/digital-twin/health` | 200 |

### 3.3 Demo Script Creation

| # | Task | Description | Effort |
|---|------|-------------|--------|
| 3.3.1 | Create demo script | `scripts/demo.sh` — sequential curl commands hitting all major endpoints with sample payloads | 1 hour |
| 3.3.2 | Create demo data seed | `scripts/demo-seed.sh` — insert sample MOs, demand lines, suppliers for demo | 30 min |
| 3.3.3 | Document demo flow | `DEMO.md` — step-by-step demo narrative for customer presentation | 30 min |

### 3.4 Final Quality Verification

| # | Task | Command | Pass Criteria |
|---|------|---------|---------------|
| 3.4.1 | Run all unit tests | `pytest services/*/tests/ -v --tb=short` | 592+ tests pass |
| 3.4.2 | Run ruff lint | `ruff check services/` | 0 new errors |
| 3.4.3 | Run ruff format | `ruff format --check services/` | All files formatted |
| 3.4.4 | Verify coverage | `pytest --cov=app services/<critical>/tests/` | ≥80% for dpe/fea/cap/mat |
| 3.4.5 | Update quality-checklists | Fix remaining arithmetic errors in open issues count | Score ≥90% |

**Phase 3 Effort:** ~2-3 days (16-24 hours)
**Phase 3 Verification:** All services healthy, demo script runs end-to-end

---

## Summary

| Phase | Tasks | Effort | Impact |
|-------|-------|--------|--------|
| **Phase 1: Doc Sync** | 33 | 1-2 hours | Fixes 29 inconsistencies, aligns all artifacts |
| **Phase 2: Test Coverage** | 12 | 1-2 weeks | Closes critical test gap, 37% → 55%+ coverage |
| **Phase 3: Demo Ready** | 7 | 2-3 days | Ensures live demo works, reproducible setup |
| **Total** | **52** | **~2-3 weeks** | Full production readiness for demo |

---

## Execution Order

```
Phase 1 (Documentation) → Phase 3.1-3.2 (Docker Recovery) → Phase 2 (Tests) → Phase 3.3-3.4 (Demo Script + Final Verification)
```

**Rationale:** Documentation sync is fastest and unblocks accurate status reporting. Docker recovery is needed before any live testing. Tests can be written against the existing codebase without Docker. Demo script is last since it depends on everything else working.
