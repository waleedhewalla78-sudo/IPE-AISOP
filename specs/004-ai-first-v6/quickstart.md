# Quickstart: IPE V6.0 Verification

**Baseline**: v1.0.0 (`003-autonomous-planning-v5`) must be running before V6 work.

## Prerequisites

```powershell
cd d:\AISOP\ipe
.\scripts\start-product.ps1
docker compose -f infrastructure\docker run --rm migrate
docker compose -f infrastructure\docker up -d --build cap-svc dpe-svc mat-svc
```

Login: http://localhost:8082 — `Ahmed@nour` / `admin`

> **Demo numbering note**: `run-full-demo.ps1` labels persist-after-approve as checkpoint **15**; this corresponds to **003 checkpoint 16** (T017). V6 checkpoints are **17–20**.

## V6-R1 — Activity-Based Planning

1. Seed activity cost drivers (post-migration 024)
2. `GET /api/v1/demand/priority/margin-aware` — verify margin-adjusted scores
3. Schedule with `strategy=activity_optimized`, compare `activity_cost_breakdown` vs `balanced`
4. Attempt approve on MO with feasibility 84% — expect 422 guardrail

```powershell
cd services\dpe-svc
uv run pytest tests/test_margin_priority.py -q
cd ..\cap-svc
uv run pytest tests/test_activity_objective.py tests/test_guardrail_85.py -q
```

---

## V6-R2 — Tariff Shock

1. Open **Tariff Shock** panel (Control Tower or `/tariff`)
2. Run **+25% Region X** scenario
3. Verify MOs below margin threshold + substitute draft in connector queue
4. pATP response includes `landed_cost_per_unit`

---

## V6-R3 — Visual CPM

1. Open **Schedule** Gantt
2. Drag an MO bar +2 days
3. Critical path redraws (red) within 2s
4. Confirm → existing **Approve** flow

```powershell
cd apps\web
npm run test -- tests/features/schedule/cpm-cascade.perf.test.ts
```

---

## V6-R4 — Predictive Maintenance

```powershell
curl -X POST http://localhost:8003/api/v1/iot/telemetry `
  -H "Authorization: Bearer $TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"machine_id":"CNC-04","rul_hours":36}'
```

Verify maintenance block + affected MO reschedule within 60s.

---

## V6-R5 — Cost of Chaos & War Room

1. Navigate to `/cost-of-chaos` — Pareto categories with $
2. Trigger supplier delay disruption → **War Room** shows top 3 recovery options with business score

```powershell
.\scripts\run-full-demo.ps1   # checkpoints 17–20 (post-V6)
```

---

## Full Demo

After V6-R5 complete:

```powershell
.\scripts\run-full-demo.ps1
# Expect 20/20 checkpoints including tariff + chaos
```

Target readiness: **≥96/100** — see `READINESS.md`
