# Sprint S6 — OTD Analytics Extended (Report)

**Date**: 2026-07-10  
**Spec**: 017 W1-07/W1-08 + 018 Sprint S6  
**Migration**: `039_cdm_otd_snapshot`  
**Service**: `dpe-svc`  
**Frontend**: `apps/web/src/features/otd-analytics/`

---

## Deliverables

| ID | Deliverable | Status |
|----|-------------|--------|
| W1-07 | OTD aggregation API (5 KPIs) + tenant RLS | ✅ |
| W1-08 | OTD dashboard UI (Recharts, filters, en/ar) | ✅ |
| S6-01 | `GET /api/v1/analytics/otd/trend` | ✅ |
| S6-02 | `GET /api/v1/analytics/otd/root-cause` | ✅ |
| S6-03 | `GET /api/v1/analytics/otd/cost-of-chaos` | ✅ |
| S6-04 | `GET /api/v1/analytics/otd/baseline` | ✅ |
| S6-05 | `OTDDashboardPage.tsx` + PDF export | ✅ |
| S6-06 | Migration `039_cdm_otd_snapshot` | ✅ |

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/analytics/otd/kpis` | Five KPI cards (OTD %, completed, at-risk, avg delay, chaos $) |
| GET | `/api/v1/analytics/otd/trend` | Daily/weekly/monthly OTD trend |
| GET | `/api/v1/analytics/otd/root-cause` | Delay breakdown by cause category |
| GET | `/api/v1/analytics/otd/cost-of-chaos` | Financial impact rollup |
| GET | `/api/v1/analytics/otd/baseline` | Pre/post IPE baseline comparison |

**Legacy (retained)**: `GET/POST /api/v1/analytics/otd-baseline` for Outcomes page.

### Query parameters

- `range`: `7d`, `30d`, `90d` (default `30d`)
- `period`: `daily` | `weekly` | `monthly` (trend only)
- Filters: `supplier_id`, `line_id` (work center), `region_id` (plant)

### Five KPIs (W1-07)

1. **otd_pct** — On-time delivery %
2. **completed_mos** — Completed MOs in lookback window
3. **orders_at_risk** — MOs with feasibility &lt; 70 or past due
4. **avg_delay_days** — Average overrun for late MOs
5. **chaos_cost_usd** — Cost of chaos in period

---

## Database

### `cdm_otd_snapshot` (migration 039)

- Daily/weekly/monthly snapshot rows per tenant
- Dimensional keys: `supplier_id`, `work_center_id`, `plant_id`
- RLS policy: `tenant_isolation` (USING + WITH CHECK)
- Unique index on `(tenant_id, snapshot_date, period, supplier, line, region)`

`upsert_daily_snapshot()` in `app/core/otd_aggregation.py` supports aggregation consumer hook.

---

## Frontend

- Route: `/command-center/otd-analytics`
- Nav: Command Center hub (visible in `release1`)
- Charts: Recharts LineChart (trend), BarChart (root cause)
- Filters: supplier, production line, region
- i18n: `otd.*` keys in `en.json` + `ar.json`
- PDF: `window.print()` export button

---

## Tests

| File | Coverage |
|------|----------|
| `services/dpe-svc/tests/test_analytics_otd.py` | KPI/trend/root-cause/chaos/baseline endpoints; tenant context; RLS query scoping |

Run:

```powershell
cd ipe
uv run --directory services/dpe-svc pytest services/dpe-svc/tests/test_analytics_otd.py -v
```

---

## Gate criteria

| Gate | Criteria | Met |
|------|----------|-----|
| G-W1-OTD | 5 KPI API + tenant RLS test | ✅ |
| G-S6-API | Four nested `/otd/*` endpoints | ✅ |
| G-S6-UI | Dashboard with Recharts + filters + ar i18n | ✅ |
| G-S6-MIG | Migration 039 with RLS | ✅ |
| G-R2-05 | `run-release2-demo.ps1` OTD steps | ✅ extended |

---

## Demo script steps

`scripts/run-release2-demo.ps1` validates:

1. Legacy `GET /analytics/otd-baseline`
2. `GET /analytics/otd/kpis`
3. `GET /analytics/otd/trend`
4. `GET /analytics/otd/baseline`

---

*S6 OTD report — 2026-07-10*
