# 04 — Frontend-Backend Integration Map (V2 Audit)

**Generated**: 2026-06-20 | **Methodology**: Traced every frontend API call to backend route handler.

## Integration Status Summary

| Status | Count | Description |
|--------|-------|-------------|
| VERIFIED_COMPLETE | 15 | Frontend call → Backend handler verified |
| IMPLEMENTED_NOT_INTEGRATED | 4 | Backend exists but path/port/method mismatch |
| CANNOT_VERIFY | 5 | No backend endpoint found |
| IMPORT_BUG | 3 | Frontend import will fail at runtime |

## Complete Integration Map

### Control Tower Dashboard

| # | Frontend Call | Backend | Match? |
|---|---------------|---------|--------|
| 1 | `GET /api/v1/dashboard/demands` | **NOT FOUND** | ❌ No backend route |
| 2 | `GET /api/v1/dashboard/capacity` | **NOT FOUND** | ❌ No backend route |
| 3 | `GET /api/v1/dashboard/alerts` | **NOT FOUND** | ❌ No backend route |
| 4 | `GET /api/v1/resolution/scenarios` | `res-svc: GET /api/v1/resolution/scenarios` | ✅ |
| 5 | `GET /feasibility/queue` | `fea-svc: GET /api/v1/feasibility/queue` | ❌ Missing `/api/v1` prefix |
| 6 | `GET /feasibility/kpis` | `fea-svc: GET /api/v1/feasibility/kpis` | ❌ Missing `/api/v1` prefix |

### Schedule Page

| # | Frontend Call | Backend | Match? |
|---|---------------|---------|--------|
| 7 | `POST /api/v1/capacity/schedule` | `cap-svc: POST /api/v1/capacity/schedule` | ✅ |
| 8 | `POST /api/v1/sync/odoo/activate` | `connector: POST /api/v1/sync/odoo/activate` | ✅ |

**BUG**: `schedule/api.ts:1` — `import { api }` fails (`export default` in lib/api.ts)

### Executive Dashboard

| # | Frontend Call | Backend | Match? |
|---|---------------|---------|--------|
| 9 | `GET /api/v1/analytics/executive-summary` | `dpe-svc: GET /api/v1/analytics/executive-summary` | ✅ |
| 10 | `GET /api/v1/analytics/otd-by-work-center` | `dpe-svc: GET /api/v1/analytics/otd-by-work-center` | ✅ |
| 11 | `GET /api/v1/analytics/delay-breakdown` | `dpe-svc: GET /api/v1/analytics/delay-breakdown` | ✅ |
| 12 | `GET /api/v1/analytics/planning-accuracy` | `dpe-svc: GET /api/v1/analytics/planning-accuracy` | ✅ |

### Admin Page

| # | Frontend Call | Backend | Match? |
|---|---------------|---------|--------|
| 13 | `GET /api/v1/admin/config` | `dpe-svc: GET /api/v1/admin/config` | ✅ (response shape warning) |
| 14 | `PUT /api/v1/admin/config` | `dpe-svc: PUT /api/v1/admin/config` | ✅ (response shape warning) |
| 15 | `GET /api/v1/admin/data-quality` | `dpe-svc: GET /api/v1/admin/data-quality` | ✅ |

### Compliance Page

| # | Frontend Call | Backend | Match? |
|---|---------------|---------|--------|
| 16 | `GET /api/v1/feasibility/compliance-kpis` | `fea-svc: GET /api/v1/feasibility/compliance-kpis` | ✅ |

**BUG**: `compliance/api.ts:1` — `import { api }` fails (`export default` in lib/api.ts)

### Shop Floor Page

| # | Frontend Call | Backend | Match? |
|---|---------------|---------|--------|
| 17 | `GET /api/v1/capacity/analyze` | `cap-svc: POST /api/v1/capacity/analyze` | ❌ GET vs POST method mismatch |
| 18 | `POST /api/v1/capacity/schedule` | `cap-svc: POST /api/v1/capacity/schedule` | ✅ (schema mismatch: `operations` vs `mo_ids`) |
| 19 | `GET /api/v1/alerts` | `alert-svc: GET /api/v1/alerts` | ✅ |

**BUG**: `shop-floor/api.ts:1` — `import { api }` fails (`export default` in lib/api.ts)

### Auth Service

| # | Frontend Call | Backend | Match? |
|---|---------------|---------|--------|
| 20 | `POST /api/v1/auth/login` | **NOT FOUND** | ❌ No auth service in any backend |
| 21 | `GET /api/v1/auth/me` | **NOT FOUND** | ❌ No auth service in any backend |

### Resolution Center (Inline)

| # | Frontend Call | Backend | Match? |
|---|---------------|---------|--------|
| 22 | `GET /api/v1/resolution/scenarios?mo_id=X` | `res-svc: GET /api/v1/resolution/scenarios` | ✅ |
| 23 | MO list data | **HARDCODED** | ❌ `MOCK_MO_LIST` (3 items) never from API |

### Copilot Panel (Inline)

| # | Frontend Call | Backend | Match? |
|---|---------------|---------|--------|
| 24 | `POST /api/v1/copilot/query` (SSE) | `nlp-svc: POST /api/v1/copilot/query` | ⚠️ SSE parsing but endpoint returns JSON |
| 25 | `WS ws://localhost:8004/...` | `fea-svc: WS /api/v1/feasibility/ws/{tenant}` | ✅ |

### Generic Hooks

| # | Frontend Call | Backend | Match? |
|---|---------------|---------|--------|
| 26 | `useApi(url)` | N/A — generic hook, not used by any component | N/A |

## Response Shape Mismatches

| Call | Frontend Expects | Backend Returns | Impact |
|------|-----------------|-----------------|--------|
| GET /admin/config | `res.data?.data` as raw config | `{config: {...}, autonomy_mode: ...}` | Config fields won't resolve |
| PUT /admin/config | Returns same mismatch | Same | Save feedback may be wrong |
| GET /capacity/analyze | `work_centers[].utilization_pct` etc. | `work_centers[].capacity_hours_per_day` etc. | Field mapping completely wrong |

## Hardcoded/Mock Data

| Feature | Data Source | Notes |
|---------|------------|-------|
| Control Tower - Bottlenecks | `getMockBottlenecks()` | Always mock, no API call |
| Control Tower - Demands | Falls back to `MOCK_RISK_QUEUE` | Used when 3 dashboard endpoints fail |
| Resolution Center - MO list | `MOCK_MO_LIST` | Entirely hardcoded; never fetched |
| Resolution Center - Scenarios | `MOCK_SCENARIOS` | Used when API returns empty |
| Executive - All analytics | Mock data blocks | Used on API error fallback only |
| Admin - Config | `MOCK_CONFIG`, `MOCK_DATA_QUALITY` | Used on API error fallback only |

## Critical Blockers

| # | Issue | Impact |
|---|-------|--------|
| 1 | 3 files with `import { api }` will fail at runtime | Schedule, Compliance, Shop Floor pages entirely broken |
| 2 | No `/auth/login` or `/auth/me` backend | Users cannot authenticate through frontend |
| 3 | 3 `/dashboard/*` endpoints don't exist | Control Tower shows only mock data |
| 4 | 2 `/feasibility/*` calls missing `/api/v1` prefix | Feasibility data never reaches frontend |
| 5 | `/capacity/analyze` uses GET but backend expects POST | Always 405 Method Not Allowed |
