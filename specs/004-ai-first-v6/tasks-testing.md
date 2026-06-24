# Tasks: IPE V6.0 — Testing Pyramid (Unit · Integration · UI · k6)

**Input**: [spec.md](./spec.md), [tasks-release.md](./tasks-release.md), [../005-ipe-program-status/plan.md](../005-ipe-program-status/plan.md)  
**Notion mirror**: IPE Task Tracker v2 — TEST-01–TEST-08  
**Readiness impact**: Testing dimension 92/100 → 96/100 (demo proven) → 100/100 (k6 + Chaos)

---

## Testing Pyramid

| Layer | Tool | Scope | Gate | Task IDs |
|-------|------|-------|------|----------|
| **Unit** | pytest (per service), Vitest (web) | Isolated modules, API handlers, solvers | launch-verify 10/10 | TEST-01, TEST-02 |
| **Integration** | pytest `@ipe/tests/integration` | Multi-service E2E, RLS, Kafka, WS | 31/31 + V6 API smoke | TEST-03, TEST-04 |
| **UI / E2E** | Playwright, Vitest + RTL | Routes, CPM perf, critical path | vitest green + e2e pass | TEST-05, TEST-06 |
| **Live demo** | `run-full-demo.ps1` | Kong + seed + CP0–20 | **20/20** | TEST-07 (= REL-09–11) |
| **Load** | k6 200 VU | p95 < 5s, error < 1% | REL-18 / RV-05 | TEST-08 |
| **Chaos** | Chaos Mesh + `r4-verify.ps1` | Pod kill recovery | REL-19 / RV-05 | TEST-09 |

---

## Phase TEST-UNIT — Backend & Frontend Unit Tests

**Depends on**: repo checkout; `uv` + `pnpm` installed

- [x] TEST-01 [P0] [TEST-UNIT] Run `scripts/launch-verify.ps1` — **10/10** services (shared, cap, dpe, fea, connector, nlp, mat, res, del, alert)
- [ ] TEST-02 [P0] [TEST-UNIT] Run V6-focused pytest subset and save evidence:
  - `services/dpe-svc/tests/test_margin_priority.py`
  - `services/dpe-svc/tests/test_tariff_shock.py`
  - `services/cap-svc/tests/test_api_cpm_cascade.py`
  - `services/cap-svc/tests/test_maintenance_block.py`
  - `services/dpe-svc/tests/test_chaos_cost.py`
  - Output → `specs/004-ai-first-v6/evidence/test-unit-v6.txt`
- [ ] TEST-02b [P1] [TEST-UNIT] Run `apps/web`: `pnpm test -- --run` + `pnpm typecheck` — Vitest green

**Exit gate**: All V6 unit tests pass; launch-verify 10/10.

**Commands**:

```powershell
cd D:\AISOP\ipe
.\scripts\launch-verify.ps1 -ReportPath specs\004-ai-first-v6\evidence\rv-02-launch-verify.txt
cd apps\web
pnpm test -- --run
pnpm typecheck
```

---

## Phase TEST-INT — Integration Tests

**Depends on**: Docker stack up (`REL-STACK`)

- [ ] TEST-03 [P0] [TEST-INT] Run `tests/integration/test_sprint2_e2e.py` — expect **25/25 pass** (1 skip OK)
- [ ] TEST-04 [P0] [TEST-INT] Run `tests/integration/test_phase5_6_e2e.py` — expect **16/16 pass**
- [ ] TEST-04b [P1] [TEST-INT] Run V6 live API smoke (via Kong @ :8000 after `docker compose up`):
  - `GET /api/v1/demand/priority/margin-aware`
  - `POST /api/v1/demand/tariff/shock`
  - `POST /api/v1/capacity/cpm/cascade`
  - `GET /api/v1/analytics/cost-of-chaos?period=7d`
  - `POST /api/v1/iot/telemetry`
  - `GET /api/v1/war-room/recovery-plan`
  - Evidence → `specs/004-ai-first-v6/evidence/test-int-v6-smoke.txt`

**Exit gate**: 41/41 integration tests pass; V6 Kong routes return 200 (not 404).

**Commands**:

```powershell
cd D:\AISOP\ipe
uv run pytest tests/integration/test_sprint2_e2e.py tests/integration/test_phase5_6_e2e.py -v
```

---

## Phase TEST-UI — Frontend UI & E2E

**Depends on**: web @ `:8082`, API @ `:8000`

- [ ] TEST-05 [P1] [TEST-UI] Run Playwright critical path: `pnpm test:e2e` in `apps/web`
- [ ] TEST-06 [P1] [TEST-UI] Run CPM perf test: `pnpm test:perf` — cascade mock p95 < 2s
- [ ] TEST-06b [P2] [TEST-UI] Manual smoke: `/tariff`, `/cost-of-chaos`, `/schedule` CPM drag, `/war-room` recovery cards

**Exit gate**: Playwright suite green; CPM perf threshold met.

---

## Phase TEST-LIVE — Live Demo (Integration at Kong)

**Depends on**: REL-STACK + rebuilt V6 images (dpe-svc, cap-svc, alert-svc) + Kong routes for `/iot`, `/war-room`

- [ ] TEST-07 [P0] [TEST-LIVE] Run `run-full-demo.ps1 -ReportPath docs/demo-run-report-v6.txt` — **20/20**
  - Maps to REL-09, REL-10, REL-11
  - CP17–20 = V6-R1–R5 live proof

**Exit gate**: `docs/demo-run-report-v6.txt` shows 20/20; P-DOC-04 unblocked.

---

## Phase TEST-LOAD — k6 Performance

**Depends on**: TEST-LIVE pass (stable stack)

- [ ] TEST-08 [P2] [TEST-LOAD] Run `scripts/run-k6-200vu.ps1` — save to `specs/003-autonomous-planning-v5/evidence/r4/k6-200vu-summary.txt`
- [ ] TEST-08b [P2] [TEST-LOAD] Run k6 smoke: `tests/performance/k6/load-test-phase56.js` — p95 < 2000ms

**Thresholds**: p95 < 5000ms, error rate < 1%, checks > 95% (200 VU, 5 min sustained)

**Exit gate**: k6 exit 0; evidence file attached. Maps to REL-18.

---

## Phase TEST-CHAOS — Chaos Mesh (optional 100/100)

**Depends on**: K8s cluster with Chaos Mesh (staging)

- [ ] TEST-09 [P2] [TEST-CHAOS] Run `scripts/r4-verify.ps1` — evidence in `specs/003-autonomous-planning-v5/evidence/r4/chaos/`

**Exit gate**: Chaos recovery documented. Maps to REL-19, REL-20.

---

## Summary

| Phase | IDs | Open | Blocks tag |
|-------|-----|------|------------|
| TEST-UNIT | TEST-01–02b | 2 | No (parallel) |
| TEST-INT | TEST-03–04b | 4 | **Yes** (V6 404 fix) |
| TEST-UI | TEST-05–06b | 3 | No |
| TEST-LIVE | TEST-07 | 1 | **Yes** (T055) |
| TEST-LOAD | TEST-08–08b | 2 | No (100/100) |
| TEST-CHAOS | TEST-09 | 1 | No (100/100) |
| **Total** | **13** | **12 open** | |

---

## Dependency Graph

```text
TEST-01 ✅
TEST-02, TEST-02b (parallel)
REL-STACK → TEST-03, TEST-04, TEST-04b
         → TEST-07 (demo 20/20) → T055
TEST-05, TEST-06 (need :8082 + :8000)
TEST-07 → TEST-08 (k6) → TEST-09 (chaos) → READINESS 100/100
```

---

## Link to Release Tasks

| Testing task | Release task |
|--------------|--------------|
| TEST-01 | REL-06–08 |
| TEST-07 | REL-09–11 |
| TEST-08 | REL-18 |
| TEST-09 | REL-19–20 |
