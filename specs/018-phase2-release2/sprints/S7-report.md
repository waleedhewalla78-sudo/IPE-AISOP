# Sprint S7 Report — Odoo Admin Polish

**Sprint**: S7 (Phase 2 Release 2)  
**Date**: 2026-07-10  
**Spec**: `018-phase2-release2`  
**Depends on**: W1 Odoo Config v2 (connector `odoo_config` API)

---

## Scope delivered

| ID | Task | Status | Evidence |
|----|------|--------|----------|
| S7-01 | DQ flags dashboard on Odoo Config page | ✅ | `OdooConfigPanel.tsx` — table from `GET /api/v1/sync/data-quality` with per-flag resolution guidance |
| S7-02 | Sync history table (last 10 runs) | ✅ | `GET /api/v1/sync/history?limit=10` + history table in UI |
| S7-03 | Partner wizard polish | ✅ | 3-step Odoo wizard (connection → schedule → monitor); onboarding ERP step highlights Odoo |

---

## Backend

### New endpoint

- **`GET /api/v1/sync/history`** (`services/connector/app/api/v1/sync.py`)
  - Query param `limit` (default 10, max 50)
  - Returns `runs[]` with `id`, `source`, `trigger`, `started_at`, `finished_at`, `duration_seconds`, `status`, `entity_counts`, `error_summary`
  - Tenant-scoped via `cdm_sync_run` + RLS

### Existing endpoints reused

- `GET /api/v1/sync/data-quality` — unresolved DQ flags
- `POST /api/v1/sync/run` — manual sync from monitor step
- `GET/PUT /api/v1/admin/erp/odoo` — legacy tenant Odoo credentials (Admin UI)

---

## Frontend

| File | Change |
|------|--------|
| `apps/web/src/features/admin/components/OdooConfigPanel.tsx` | **New** — partner wizard + DQ dashboard + sync history |
| `apps/web/src/features/admin/components/AdminPage.tsx` | Odoo tab delegates to `OdooConfigPanel` |
| `apps/web/src/features/admin/api.ts` | `fetchSyncDqFlags`, `fetchSyncHistory`, `runSyncNow` |
| `apps/web/src/features/admin/types.ts` | `DataQualityFlag`, `SyncRun` types |
| `apps/web/src/features/onboarding/components/OnboardingWizard.tsx` | ERP selection, Odoo recommended, route to Admin |
| `apps/web/src/locales/en.json`, `ar.json` | S7 i18n keys (`admin.odoo.*`) |

---

## Tests

| Suite | File | Tests |
|-------|------|-------|
| connector | `tests/test_sync_history_api.py` | 3 — history payload, limit cap, data-quality flags |
| web (vitest) | `tests/features/admin/OdooConfigPanel.test.tsx` | 1 — wizard + DQ + history render |

### Run commands

```powershell
cd E:\AISOP\ipe\services\connector
uv run pytest tests/test_sync_history_api.py -v

cd E:\AISOP\ipe\apps\web
npm run test -- tests/features/admin/OdooConfigPanel.test.tsx
```

---

## Acceptance criteria (guide § Sprint 7)

| Criterion | Result |
|-----------|--------|
| Test connection from Admin Odoo tab | ✅ Wizard step 1 |
| Save Odoo config | ✅ Wizard step 3 save |
| Sync schedule interval input | ✅ Wizard step 2 (default 900 min) |
| Sync now with feedback | ✅ Monitor step |
| DQ flags table with guidance | ✅ Side panel |
| Sync history last 10 runs | ✅ API + table |
| Arabic labels | ✅ `ar.json` keys |

---

## Notes

- W1 Odoo Config v2 (`/api/v1/admin/odoo-config`) remains available for versioned entity mappings; S7 polish uses the existing Admin ERP endpoints plus sync APIs for partner UX.
- DQ resolution guidance maps all six `cdm_data_quality_flag` codes from migration 036.

---

*S7 complete — 2026-07-10*
