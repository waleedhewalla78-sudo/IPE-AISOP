# IPE v6.0.0+ Product Completion — Master Execution Plan (Reconciled)

**Workspace:** `E:\AISOP\ipe`  
**Updated:** 2026-06-26  
**Supersedes:** Draft Master Execution Plan (15/20 snapshot)  
**Authority:** [`specs/005-ipe-program-status/analyze.md`](../specs/005-ipe-program-status/analyze.md), [`READINESS.md`](../READINESS.md)

---

## Executive Summary (Current)

| Metric | Stale plan (Jun 26 draft) | **Actual (Jun 26 reconciled)** |
|--------|---------------------------|--------------------------------|
| Live demo | 15/20 | **20/20** stable |
| Git | Zero commits | **5+ commits**; tags **v1.0.0**, **v6.0.0**, **v6.0.1** |
| Unit tests | 878 passing | **870+** passing (cap/mat/dpe suites expanded) |
| REL-PROD | Not started | **2A–2D complete** (k6, chaos, coverage, ops MVP) |
| Speckit readiness | 96/100 | **97/100** |
| Audit (est.) | 74/100 | **~91/100** |
| Next tag | v6.0.0 pending | **v6.1.0** (Wave 3) |

The platform is **past** the v6.0.0 demo gate. Remaining work is **Wave 3 hardening** (C-03, C-04, SEC-05) and long-term POST-* backlog.

---

## Phase Status Matrix

| Phase | Scope | Status | Evidence |
|-------|-------|--------|----------|
| **0** | Git + C-01/C-02/BUG-02/BUG-03 | ✅ **Done** | `fea0705`, `0e2055e`; tags exist |
| **1** | Demo 20/20 + v6.0.0 tag | ✅ **Done** | `docs/demo-run-report-v6.txt`, T055 |
| **2** | Audit code fixes live | ✅ **Done** | MDR auth forward; rebuild verified |
| **3** | REL-PROD 2A k6 | ✅ **Done** | `docs/k6-summary.md` |
| **3** | REL-PROD 2B Chaos C1–C6 | ✅ **Done** | `docs/chaos/chaos-summary.md` |
| **3** | REL-PROD 2C Coverage 60% | ✅ **Done** | cap 68%, mat 65%, dpe 66% |
| **3** | REL-PROD 2D Loki/Grafana | ✅ **Done** | `docs/ops-monitoring.md` |
| **W3** | C-03 TLS runbook | ⬜ Open | — |
| **W3** | C-04 JWT rotation | ⬜ Open | — |
| **W3** | SEC-05 password_hash | ⬜ Open | — |
| **4** | Keycloak / SAML / SCIM | 🔴 BLOCKED | C-007 |
| **5–7** | Commercial / hardening / BRD | ⬜ Future | POST-* backlog |

---

## Closed P0 / P1 Items (vs stale risk register)

| ID | Stale status | **Current** |
|----|--------------|-------------|
| GIT-01 | Open | ✅ Closed — git initialized, tagged |
| T016 Copilot 503 | Open | ✅ Closed — nlp fallback |
| T017 CP15 persist | Open | ✅ Closed |
| T018 Tariff 500 | Open | ✅ Closed |
| T019 Chaos 500 | Open | ✅ Closed |
| BUG-01 ERP sync | Fixed not committed | ✅ Closed — committed + tested |
| BUG-02 MDR fail-open | Open | ✅ Closed — 503 fail-closed |
| BUG-03 Version approve | Open | ✅ Closed — 409 on conflict |
| C-01 check-availability | Open | ✅ Closed — `rule_based_atp()` |
| C-02 Double prefix | Open | ✅ Verified — no change needed |
| R-01 Coverage 40% | Open | ✅ Closed — 60% gate + tests |
| R-08 Log aggregation | Open | ✅ MVP — Loki + Promtail + Grafana |

---

## Phase 3 Detail (REL-PROD) — Delivered

### 8.1 k6 Load Testing ✅

| Test | Result |
|------|--------|
| smoke.js | PASS — p95 646ms |
| load-10vu.js | PASS — p95 3.0s |
| load-200vu.js | PASS — 0% 5xx; Kong 429 at high VU (restart Kong) |

Scripts: `tests/performance/k6/`

### 8.2 Chaos Engineering ✅

6/6 scenarios via `scripts/run-chaos-scenarios.ps1`. C3 validated CDM persist + `ERP_EVENT_PUBLISH_FAILED` when Kafka paused.

### 8.3 Coverage ≥60% ✅

| Service | Coverage | `fail_under` |
|---------|----------|--------------|
| cap-svc | 68.26% | 60 |
| mat-svc | 65.35% | 60 |
| dpe-svc | 66.01% | 60 |

Audit-path tests: check-availability, approve 409, tariff exposure.

### 8.4 Operational Infrastructure ✅

| Component | URL |
|-----------|-----|
| Grafana | http://localhost:3002 (`admin` / `ipe_admin`) |
| Prometheus | http://localhost:9091 |
| Loki | http://localhost:3100 |

Start: `.\scripts\run-monitoring-stack.ps1` (after `rel-demo-stack.ps1`)

---

## Wave 3 — Immediate Next Steps (v6.1.0)

Execute in order from `E:\AISOP\ipe`:

```powershell
# 1. Confirm stack + monitoring (optional re-verify)
.\scripts\rel-demo-stack.ps1 -SkipBuild
.\scripts\run-monitoring-stack.ps1 -VerifyOnly

# 2. Wave 3 deliverables (engineering)
#    - docs/runbooks/tls-internal.md
#    - docs/runbooks/jwt-rotation.md
#    - migrations/028_* password_hash + seed update

# 3. Regression
.\scripts\run-full-demo.ps1 -ReportPath docs\demo-run-report-post-v6.1.txt
.\scripts\run-chaos-scenarios.ps1   # C6 only if time-boxed

# 4. Tag (after user approval)
# git tag -a v6.1.0 -m "IPE v6.1.0 — REL-PROD hardening"
```

**Estimated effort:** 2–3 days focused engineering.

---

## Binding Decisions (unchanged)

| Decision | Answer |
|----------|--------|
| Workspace | `E:\AISOP\ipe` canonical |
| REL-STACK | `docker-compose.demo.yml` + `rel-demo-stack.ps1` |
| Blocks v6.0.0 | ~~20/20 + T055~~ — **satisfied** |
| Keycloak | BLOCKED C-007 until IdP sandbox |
| Demo users | `Ahmed@nour` / `admin` |

---

## Score Trajectory

```text
Audit 74 (Jun 20) → 82 (audit fixes) → 85 (k6) → 87 (chaos) → 89 (coverage) → 91 (ops) → 95 (W3) → 100 (enterprise)
Speckit 97 ────────────────────────────────────────────────────────────────────────────────► 100
```

---

## Artifact Index

| Artifact | Path |
|----------|------|
| Program analyze | `specs/005-ipe-program-status/analyze.md` |
| Program plan | `specs/005-ipe-program-status/plan.md` |
| Program tasks | `specs/005-ipe-program-status/tasks.md` |
| Release tasks | `specs/004-ai-first-v6/tasks-release.md` |
| READINESS | `READINESS.md` |
| Demo evidence | `docs/demo-run-report-v6.txt` |
| k6 | `docs/k6-summary.md` |
| Chaos | `docs/chaos/chaos-summary.md` |
| Coverage | `docs/coverage-summary.md` |
| Ops | `docs/ops-monitoring.md` |

---

*This document reconciles the June 26 Master Execution Plan draft against live Speckit artifacts. Use it for stakeholder updates; use `tasks.md` for execution tracking.*
