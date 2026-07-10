# W1 Odoo Config v2 — Sprint Report

**Date**: 2026-07-10  
**Spec**: 017-first-release-plan §3.1–3.4  
**Migration**: **043** (`cdm_odoo_config_version`)  
**Service**: `connector` (`/api/v1/admin/odoo-config`)

---

## Deliverables

| Task | Status | Evidence |
|------|--------|----------|
| W1-03 Schema + API | ✅ | `connector/app/api/v1/odoo_config.py`, Pydantic v2 + JSON Schema |
| W1-04 Test connection <5s | ✅ | `POST .../test-connection`, `CONNECTION_TIMEOUT_SECONDS=5` |
| W1-05 Multi-entity + versioning | ✅ | `entity_key`, version history, rollback, v1 bootstrap |
| W1-06 React UI | ✅ | `apps/web/.../OdooConfigPage.tsx`, Platform hub tab, en+ar i18n |

---

## API contract

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/v1/admin/odoo-config` | List current configs per entity |
| GET | `/api/v1/admin/odoo-config/{entity_key}` | Current version for entity |
| GET | `/api/v1/admin/odoo-config/{entity_key}/versions` | Version history |
| POST | `/api/v1/admin/odoo-config` | Create new version (422 on invalid mappings) |
| POST | `/api/v1/admin/odoo-config/test-connection` | XML-RPC auth, 5s SLA |
| POST | `/api/v1/admin/odoo-config/{entity_key}/rollback/{version}` | Rollback → new version |

**RLS**: `cdm_odoo_config_version` uses `tenant_isolation` policy (NULLIF pattern from migration 001 loop).

**Backward compat**: First GET bootstraps `primary` entity from legacy `cdm_tenant.config` (v1).

---

## Kong routes

- `infrastructure/kong/kong.release1.yml` — `/api/v1/admin/odoo-config` → connector
- `infrastructure/kong/kong.yml` — same path on connector service

Legacy v1 endpoints remain on dpe-svc: `/api/v1/admin/erp/odoo`.

---

## Tests

```powershell
cd ipe
uv run --directory services/connector pytest services/connector/tests/test_odoo_config_v2.py -q
```

Coverage: JSON Schema validation, 422 on invalid body, mock Odoo connection, 5s timeout, version conflict 409, v1 default mappings.

---

## UI

- Route: `/platform/odoo-config` (Release 1 profile)
- Platform hub tab: `odooConfig.nav`
- Features: multi-entity selector, test-and-save, version history, rollback

---

## Files changed (summary)

- `migrations/versions/043_odoo_config_versioning.py`
- `services/shared/ipe_shared/models/odoo_config_version.py`
- `services/connector/app/schemas/odoo_config_v2.py`
- `services/connector/app/core/odoo_config_service.py`
- `services/connector/app/api/v1/odoo_config.py`
- `services/connector/tests/test_odoo_config_v2.py`
- `apps/web/src/features/odoo-config/**`
- `infrastructure/kong/kong.yml`, `kong.release1.yml`
- `specs/017-first-release-plan/tasks.md`, `specs/018-phase2-release2/tasks.md`

---

*W1-03–06 complete — ready for W1-07 OTD dashboard.*
