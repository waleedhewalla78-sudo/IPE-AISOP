# Wave 1 Readiness — Phase 0 → Phase 1 Handoff

**Date**: 2026-07-09  
**From**: Phase 0 (Spec 017 Week 1)  
**To**: Wave 1 Foundation (Weeks 2–5)

---

## Tagged version

| Item | Value |
|------|-------|
| **Git tag** | `v9.4.0-p3` |
| **Message** | Phase 0 complete. Gate 11: 12/14 PASS (waiver OQ-9 for OR-Tools timeout under kind). Sprint 7 Tier 1: T717–T719 + T730 complete. 20/20 emitter tests pass. |
| **Gate 11 evidence** | `ipe/docs/demo-data/gate11-k8s-demo.txt` + OQ-9 waiver `ipe/docs/demo-data/gate11-oq9-waiver.md` |
| **Alembic head** | **038** (`038_sprint7_activity_events`) — compose DB (`localhost:5433/ipe_test`) and kind PostgreSQL pod |

---

## R1 deploy set health (kind `ipe-dev`)

| Service | Status (2026-07-09) |
|---------|---------------------|
| cap-svc | 1/1 Running |
| connector | 1/1 Running |
| dpe-svc | 1/1 Running |
| fea-svc | 1/1 Running |
| mat-svc | 1/1 Running |
| res-svc | 1/1 Running |
| postgresql | 1/1 Running |
| redis | 1/1 Running |
| Ingress (`ipe-api`) | `GET /api/v1/health` → **HTTP 200** |

**Note**: Kong is disabled in `values-dev.yaml`; nginx ingress fronts R1 APIs on `http://localhost`.

HPA resources removed; all R1 deployments scaled to **1** replica.

---

## Sprint 7 Phase 0 completion

| Task | Status |
|------|--------|
| T717 connector activity emitter | ✅ |
| T718 cap-svc activity emitter | ✅ |
| T719 res-svc activity emitter | ✅ |
| T730 migration 038 (`cdm_activity_event`) | ✅ compose + K8s |
| Emitter tests | **20/20 PASS** |

---

## Known issues carried forward

| ID | Issue | Mitigation / owner |
|----|-------|-------------------|
| **OQ-9** | Gate 11 kind steps 10–11 OR-Tools timeout (12/14) | Waiver doc; compose 14/14 proves logic; [#27](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/27) kind CPU / port-forward follow-up |
| **Stakeholder sign-off** | OQ-9 Section 6 blank until PO/Platform/QA sign | [#28](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/28) |
| **Ingress root** | `GET /` → 404 (expected); health at `/api/v1/health` | Document in K8S-DEPLOYMENT-GUIDE if needed |

---

## First Wave 1 task

**W1-01 Copilot R1 nav unhide** — ✅ **Already implemented** (`apps/web/src/components/layout/Sidebar.tsx`, `releaseProfile.ts`).

**Start here (Prompt 3 / next session):**

| Priority | Task | GitHub | Cursor prompt |
|----------|------|--------|---------------|
| **1** | Copilot smoke test (R1 profile) | [#30](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/30) | Prompt 3 suite — Copilot validation |
| **2** | Admin Odoo Config v2 schema | [#31](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/31) | Prompt 4 |

Spec: `ipe/specs/017-first-release-plan/tasks.md`  
Plan: `ipe/specs/017-first-release-plan/plan.md` (Wave 1, Weeks 2–5)

---

## Quick verification commands

```powershell
cd E:\AISOP\ipe

# Emitter regression
cd services\shared;  uv run pytest tests/test_activity_eib.py -q
cd ..\connector;     uv run pytest tests/test_activity_emit.py -q
cd ..\cap-svc;       uv run pytest tests/unit/test_activity_emit.py -q
cd ..\res-svc;       uv run pytest tests/unit/test_activity_emit.py -q

# Schema parity
cd ..\..\migrations
$env:IPE_DATABASE_URL_SYNC = "postgresql://ipe:ipe_test_pass@127.0.0.1:5433/ipe_test"
uv run alembic current
kubectl exec -n ipe deploy/postgresql -- psql -U ipe -d ipe_test -t -c "SELECT version_num FROM alembic_version;"

# Cluster
kubectl get pods -n ipe
```

---

*Handoff artifact for Wave 1 kickoff — Spec 017.*
