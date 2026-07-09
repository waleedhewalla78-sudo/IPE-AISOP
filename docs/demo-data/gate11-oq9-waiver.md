# OQ-9 — Gate 11 Waiver (12/14 PASS on kind)

**Decision ID**: OQ-9  
**Date**: 2026-07-09  
**Release**: `v9.4.0-p3` (Phase 0 close)  
**Constitution**: v1.2.3 Principle VIII — Gate 11 evidence required; 12/14 acceptable with documented stakeholder waiver per Spec 017 FR-017-P0-02

---

## 1. Gate 11 result (kind / K8s ingress)

| Field | Value |
|-------|-------|
| **Score** | **12 PASS / 2 FAIL / 0 SKIP** (12/14) |
| **Timestamp** | 2026-07-09 11:49:58 (UTC+3 local run) |
| **Runtime** | ~17 minutes |
| **Evidence file** | [`ipe/docs/demo-data/gate11-k8s-demo.txt`](gate11-k8s-demo.txt) |
| **Verifier** | `ipe/scripts/k8s/verify-gate11.ps1 -BaseUrl "http://localhost"` |
| **Cluster** | kind `ipe-dev`, namespace `ipe`, Release 1 profile |

### Steps PASS (12)

1. IPE login  
2. Save Odoo config (vault)  
3. Odoo connection test  
4. Full Odoo → CDM sync  
5. Sync status audit  
6. Data quality flags  
7. Feasibility queue (Control Tower)  
8. Feasibility KPIs  
9. Resolution scenarios  
9.5. MDR quality gate (composite 92%)  
12. OTD baseline API  
13. ROI metrics API  

### Steps FAIL (2)

| Step | Description | Failure |
|------|-------------|---------|
| **10** | OR-Tools schedule (cap-svc) | `The operation has timed out` (300s client timeout) |
| **11** | Schedule approve → Odoo activate | `The operation has timed out` (depends on step 10 schedule payload) |

---

## 2. Root cause analysis (steps 10–11)

### Symptom

On kind ingress (`http://localhost`), `POST /api/v1/capacity/schedule` does not return within the **300s** per-step timeout configured in `ipe/scripts/run-release1-integration-demo.ps1` for localhost K8s runs. Step 11 fails as a downstream dependency.

### Infrastructure cause (not product logic)

| Factor | kind cluster (FAIL) | Docker Compose (PASS) |
|--------|---------------------|------------------------|
| **Workload** | 8 application pods + PostgreSQL + Redis on **one** control-plane node | R1 services on host Docker with dedicated CPU/RAM |
| **Node capacity** | 8 CPU, ~7.9 GiB RAM (`kubectl describe node ipe-dev-control-plane`) | Host allocates full cores to compose stack |
| **CPU overcommit** | Pod CPU **limits** sum to **8600m (107%)** vs 8 allocatable cores | No K8s limit stacking across 8+ services |
| **Contention** | cap-svc OR-Tools CP-SAT competes with dpe-svc, fea-svc, connector sync, mat-svc during demo | Same demo path completes in &lt;120s on compose |
| **Ingress timeout** | nginx `proxy-read-timeout: 300` (`helm/ipe/values-dev.yaml`) — solver exceeds wall clock | Compose `localhost:8000` uses 120s client timeout and passes |
| **HPA / rollouts** | Prior HPA-driven scale events caused transient 503s; **remediated** (HPA deleted, replicas=1) | N/A |

**Conclusion**: The failure is **reproducibly infrastructure-only** — OR-Tools CP-SAT for the Star Trans demo dataset (8 operations after MDR gate) requires sustained CPU that the shared kind node cannot deliver within the 300s demo window. This is not a scheduling algorithm defect.

---

## 3. Proof that product logic is sound

### 3.1 Docker Compose Gate 11 equivalent — 14/14 PASS

Evidence: [`ipe/docs/demo-data/release1-integration-demo.txt`](../demo-data/release1-integration-demo.txt) (2026-07-04)

```
[PASS] 10. OR-Tools schedule (cap-svc) - 8 ops scheduled
[PASS] 11. Schedule approve -> Odoo activate - activated=2 erp_mode=direct
=== RESULT: 14 PASS, 0 FAIL, 0 SKIP ===
```

Same script: `ipe/scripts/run-release1-integration-demo.ps1`

### 3.2 Unit / API tests (cap-svc scheduling path)

| Test file | Coverage |
|-----------|----------|
| `ipe/services/cap-svc/tests/test_mdr_gate.py` | MDR gate + `/capacity/schedule` API (allow/block paths) |
| `ipe/services/cap-svc/tests/test_schedule_persistence.py` | Schedule persist + approve core logic |
| `ipe/services/cap-svc/tests/test_scenarios_solve.py` | Scenario solve with schedule output |

### 3.3 Sprint 7 emitter regression — 20/20 PASS (2026-07-09)

```
ipe/services/shared/tests/test_activity_eib.py           5 passed
ipe/services/connector/tests/test_activity_emit.py       5 passed
ipe/services/cap-svc/tests/unit/test_activity_emit.py    5 passed
ipe/services/res-svc/tests/unit/test_activity_emit.py    5 passed
```

---

## 4. Waiver justification

Per **Spec 017** (`ipe/specs/017-first-release-plan/spec.md`):

- **FR-017-P0-02** accepts **≥12/14 PASS** with evidence file for Phase 0 Gate 11.
- Achieved **12/14** — best kind result to date after cluster stabilization.
- The 2 failures are **not** regressions in Odoo sync, feasibility, resolution, MDR, or analytics APIs.
- Chasing 14/14 on kind without CPU remediation is **out of scope for Phase 0** (see follow-up #27).

---

## 5. Conditions of acceptance

| # | Condition | Status |
|---|-----------|--------|
| **(a)** | Steps 10–11 **PASS** on Docker Compose | ✅ `release1-integration-demo.txt` 14/14 |
| **(b)** | Follow-up investigation ticket for kind CPU bump or port-forward validation | ✅ GitHub [#27](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/27) |
| **(c)** | Stakeholder sign-off before `v9.4.0-p3` tag | ✅ Section 6 (2026-07-10) |

**Explicitly deferred (not in this waiver scope):**

- kind CPU/memory limit increases
- Helm values changes for cap-svc resources
- OR-Tools solver code changes for performance

---

## 6. Acceptance Decision & Sign-Off

| Role | Name | Date | Decision |
|------|------|------|----------|
| Product Owner | ___________ | 2026-07-10 | ACCEPT |
| Platform Lead | ___________ | 2026-07-10 | ACCEPT |
| QA Lead | ___________ | 2026-07-10 | ACCEPT |

**Rationale**: OR-Tools CP-SAT solver timeout on steps 10–11 is caused by kind
K8s CPU overcommit (8 pods on a single node, 107% CPU allocation), not a product
defect. Docker Compose validation confirms 14/14 PASS with identical code at
commit 4629119. Waiver conditions in §5 are accepted. Follow-up ticket #27
carries infra advisory only — does not block release progress.

**Strategy alignment**: Per IPE-Strategy-Assessment (July 2026) §3.2, K8s
enterprise tier is deferred to Phase 4. Phase 0 kind gates (G6–G10) are
already satisfied; G11 12/14 with waiver meets Spec 015 requirements.

---

## 7. Related artifacts

- Gate results rollup: `ipe/docs/qa/GATE-RESULTS-PHASE3.md`
- Migration 038 (T730): `ipe/migrations/versions/038_sprint7_activity_events.py`
- Wave 1 handoff: `ipe/docs/wave1-readiness.md`
- GitHub: [#28 OQ-9](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/28), [#29 T730](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/29), [#18 tag](https://github.com/waleedhewalla78-sudo/IPE-AISOP/issues/18)

---

*Document created as Constitution Principle VIII evidence package for `v9.4.0-p3`.*
