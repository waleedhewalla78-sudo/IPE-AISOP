# Sprint 1 — Defect Log

**Defect ID format:** `S1-###`

---

### S1-001: App connects as superuser (RLS bypassed)

**Date:** 2026-06-17
**Severity:** Medium
**Status:** Known — deferred

**Description:**
All application services connect to PostgreSQL as `ipe` user (`postgresql+asyncpg://ipe:ipe_dev_pass@localhost:5432/ipe_dev`). Since `ipe` is the table owner (created the schema via migrations), PostgreSQL RLS policies do NOT apply to this connection. RLS is correctly installed (verified by testing as `ipe_app` role) but transparent to the running application.

**Root cause:**
Migration's `GRANT SELECT, INSERT, UPDATE ON cdm_* TO ipe_app` was intended for the app user, but `settings.DATABASE_URL` uses `ipe` instead of `ipe_app`.

**Impact:**
- No tenant-level row isolation at the database layer for application queries
- RLS provides defense-in-depth value only for direct DB access

**Remediation:**
- Create `ipe_app` database user with password
- Change `settings.DATABASE_URL` to `postgresql+asyncpg://ipe_app:<password>@...`
- Ensure `ipe_app` has `USAGE` on schemas and sequences
- Test that all API endpoints still function (may need `SET app.current_tenant_id` being honored)

---

### S1-002: cdm_model_registry extends spec (20th table)

**Date:** 2026-06-17
**Severity:** Low
**Status:** Accepted

**Description:**
Migration 002 adds `cdm_model_registry` table, bringing total to 20 CDM tables. The Sprint 1 spec defines exactly 19 tables. This is a pre-existing extension (not part of the Sprint 1 change set).

**Impact:**
None — the table is a useful extension for model management.

---

### S1-003: Shared integration test failures (3 tests)

**Date:** 2026-06-17
**Severity:** Low
**Status:** Pre-existing — needs separate fix

**Description:**
Three tests in `services/shared/tests/integration/test_rls_isolation.py` fail:

1. `test_tenant_a_cannot_read_tenant_b_data` — `sqlalchemy.ext.asyncio.exc.AsyncMethodRequired`: uses `session.execute()` with server-side cursor; should use `session.stream()`
2. `test_set_local_scopes_session` — `AttributeError: 'session' has no attribute 'async_session_factory'`
3. `test_unscoped_query_returns_no_rows` — same missing attribute

**Root cause:**
Integration tests were written against an older version of `session.py` that exposed `async_session_factory`. The current `session.py` encapsulates the factory inside `get_session()`.

**Fix:**
Rewrite integration tests to use `get_session()` context manager and `stream()` for async result sets.

---

### S1-004: Coverage below pyproject.toml threshold

**Date:** 2026-06-17
**Severity:** Low
**Status:** Known — temporary threshold

**Description:**
dpe-svc test coverage is 56% (branch). The pyproject.toml `[tool.coverage.run]` specifies `fail_under = 80`. Per AGENTS.md Phase 0, the threshold was temporarily lowered to 40%.

**Impact:**
`pytest --cov` fails due to coverage threshold.

---

### S1-005: MDR engine SQL queries missing explicit tenant_id filter

**Date:** 2026-06-17
**Severity:** High
**Status:** Fixed

**Description:**
The MDR engine (`mdr_engine.py`) SQL queries for BOM completeness and lead time accuracy relied on RLS for tenant isolation. Since the app connects as the `ipe` superuser (table owner), PostgreSQL RLS is bypassed and the queries counted data across ALL tenants. This caused the MDR gate to incorrectly pass for tenants with failing data quality.

**Root cause:**
1. App connects as `ipe` superuser (table owner) — RLS policies do not apply (same root cause as S1-001)
2. MDR engine queries lacked `WHERE tenant_id = :tid` clauses

**Fix applied:**
Added explicit `WHERE p.tenant_id = :tid` and `WHERE tenant_id = :tid` to both SQL queries in `services/dpe-svc/app/core/mdr_engine.py`.

**Verification:**
- Tenant with 0% BOM completeness now correctly returns HTTP 403 `MDR_GATE_FAILED`
- Tenant with 100% BOM completeness correctly passes through to classification

---

### S1-006: Docker image source code drift (demand.py, mdr_engine.py)

**Date:** 2026-06-17
**Severity:** Medium
**Status:** Fixed (workaround)

**Description:**
The running Docker container for `dpe-svc` contained an older version of `demand.py` that was missing the MDR gate check. The source code on disk (`services/dpe-svc/app/api/v1/demand.py`) had the MDR gate, but the Docker image was built from an earlier revision.

**Root cause:**
Docker image not rebuilt after MDR gate was added to `demand.py`. Additionally, the Docker build is broken due to path dependency resolution: `pyproject.toml` references `ipe-shared = { path = "../shared" }` which resolves to `/shared` inside the container, but the Dockerfile copies shared to `/app/shared`.

**Workaround:**
Files manually copied into running container via `docker cp`. Proper fix requires fixing the Docker build context or path resolution.

---

### S1-007: 80 missing ORM columns across 16 tables (schema-model drift)

**Date:** 2026-06-17
**Severity:** Medium
**Status:** Fixed (migration 003)

**Description:**
The Sprint 1 base migration (001) defined the initial 19-table CDM schema. Subsequent sprints added ~80 new columns to the SQLAlchemy ORM models (and two entirely new tables: `cdm_resource_calendar`, `cdm_maintenance_window`) without creating corresponding Alembic migrations. The database schema drifted from the ORM models.

**Impact:**
`POST /api/v1/demand/classify` failed with `UndefinedColumnError: column cdm_demand_line.erp_source_type does not exist`.

**Fix applied:**
Migration 003 (`migrations/versions/003_sync_orm_columns.py`) adds all 80 missing columns across 16 tables and creates 2 new tables (`cdm_customer`, `cdm_resource_calendar`, `cdm_maintenance_window`).

**Verification:**
All dpe-svc HTTP endpoints work correctly after migration. 44/44 unit tests pass.
