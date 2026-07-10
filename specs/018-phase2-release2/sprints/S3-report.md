# Sprint S3 Report — Demand Sensing (SES-first)

**Sprint**: S3  
**Date**: 2026-07-10  
**Authority**: Spec 017 (SES-first) · `docs/PHASE2-SPRINT-PLAN.md`  
**Status**: ✅ Complete

---

## Summary

Delivered SES-first demand forecasting on `cdm_demand_line` with 7/14/30-day horizons, confidence bounds, MAPE accuracy endpoint, Control Tower overlay widget, and Demand tab with Recharts.

---

## Deliverables

| Task | Deliverable | Status |
|------|-------------|--------|
| S3-01 | SES forecaster on `cdm_demand_line` | ✅ |
| S3-02 | `GET /api/v1/demand/forecast`, `GET /api/v1/demand/accuracy` | ✅ |
| S3-03 | Control Tower forecast overlay | ✅ |
| S3-04 | Demand tab (Recharts + MAPE) | ✅ |
| S3-05 | `test_forecaster_r2.py` | ✅ |

---

## APIs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/demand/forecast` | Forecast series; `product_id`, `days` (7/14/30) |
| GET | `/api/v1/demand/accuracy` | MAPE % for `product_id` holdout |
| POST | `/api/v1/demand/sense` | Persist forecasts from demand lines |
| POST | `/api/v1/demand/signal/ingest` | Ingest demand signals |

**Model**: `DEMAND_FORECAST_MODEL=ses` (default per Spec 017)

---

## UI

| File | Purpose |
|------|---------|
| `apps/web/src/features/hubs/planning/DemandForecastPage.tsx` | Demand tab — horizon toggle, Recharts, MAPE |
| `apps/web/src/features/control-tower/components/ForecastOverlayWidget.tsx` | Demand vs capacity gap overlay |
| `apps/web/src/features/control-tower/components/ControlTowerPage.tsx` | Embeds overlay widget |

---

## Tests

```
services/demand-svc/tests/test_forecaster_r2.py — 7 passed
services/demand-svc/tests/ (full suite) — see pytest output
```

---

## Notes

- Live forecast computed from `cdm_demand_line` when no persisted `cdm_demand_forecast` rows exist.
- Prophet/LSTM remain in factory but are not selected unless `DEMAND_FORECAST_MODEL` overrides SES.

---

*S3 report — Phase 2 Release 2*
