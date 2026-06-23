# 13 — Dependency & Supply Chain Assessment (V2 Audit)

**Generated**: 2026-06-20

## Package Management

| Layer | Manager | Lock File | Size |
|-------|---------|-----------|------|
| Python (root) | uv | `uv.lock` | 657KB |
| Python (11 services) | uv (workspace) | per-service `uv.lock` | — |
| Frontend | pnpm | `pnpm-lock.yaml` | 163KB |
| Frontend (web) | pnpm | `pnpm-lock.yaml` (pnpm workspace) | — |

## Python Dependency Audit

### Runtime Dependencies (ipe_shared, representative)

| Package | Version | Status | Notes |
|---------|---------|--------|-------|
| fastapi | >=0.115.0 | Current | LTS release |
| uvicorn | >=0.30.0 | Current | |
| sqlalchemy | >=2.0.35 | Current | Async support |
| asyncpg | >=0.29.0 | Current | |
| pydantic | >=2.9.0 | Current | |
| pydantic-settings | >=2.5.0 | Current | |
| pyjwt | >=2.9.0 | Current | |
| aiokafka | >=0.11.0 | Current | |
| prometheus-client | >=0.20.0 | Current | Metrics setup |
| opentelemetry-api/sdk | >=1.27.0 | Current | **NOT USED** (never initialized) |
| sentry-sdk | >=2.15.0 | Current | Assumes Sentry is configured |
| cryptography | >=43.0.0 | Current | |
| redis | >=5.0.0 | Current | Was unpinned; now pinned per Phase 6 |
| fastavro | >=1.12.2 | Current | Avro serialization |
| httpx | >=0.27.0 | Current | HTTP client |

### Key Missing Dependencies

| Package | Needed For | Status |
|---------|-----------|--------|
| ruff | Linting | Not in pyproject.toml (workspace-managed?) |
| pytest | Testing | Not in shared's pyproject.toml |
| mypy | Type checking | Config exists but package not installed |
| numpy | Monte Carlo | Intentionally omitted (stdlib random used) |
| scipy | Statistical distributions | Intentionally omitted |
| anthropic | LLM API | In del-svc + nlp-svc pyproject.toml |
| or-tools | CP-SAT solver | In cap-svc pyproject.toml |

### Workspace Config Verification

**Root `pyproject.toml`**:
```toml
[tool.uv.workspace]
members = [
    "services/dpe-svc", "services/mat-svc", "services/cap-svc",
    "services/fea-svc", "services/res-svc", "services/del-svc",
    "services/nlp-svc", "services/rec-svc", "services/alert-svc",
    "services/connector", "services/ml-svc", "services/shared",
]
```

**Issue**: `services/ml-svc` is listed as a workspace member but its pyproject.toml references `ipe-shared` via `{ workspace = true }` — needs verification that ml-svc's `dependencies` or `tool.uv.sources` are configured correctly.

## Node.js Dependency Audit

### Direct Dependencies (apps/web/package.json)

| Package | Version | Type | Notes |
|---------|---------|------|-------|
| react | ^18.3.1 | Runtime | Current LTS |
| react-dom | ^18.3.1 | Runtime | Current |
| react-router-dom | ^6.26.0 | Runtime | Current |
| @reduxjs/toolkit | ^2.2.7 | Runtime | Current |
| react-redux | ^9.1.2 | Runtime | Current |
| axios | ^1.7.4 | Runtime | Current |
| recharts | ^3.8.1 | Runtime | Current |
| tailwindcss | ^3.4.9 | Dev | Current |
| typescript | ^5.5.4 | Dev | Current |
| vite | ^5.4.0 | Dev | Current (CVE warning) |
| vitest | ^2.0.5 | Dev | Current (CVE warning) |
| @playwright/test | ^1.61.0 | Dev | Current |
| eslint | ^8.57.0 | Dev | Current |
| @testing-library/react | ^16.0.0 | Dev | Current |

## Known Vulnerabilities (Dev Only)

| Package | Version | CVE | Risk | Mitigation |
|---------|---------|-----|------|-----------|
| vitest | ^2.0.5 | Critical | Dev tool only — not in production image | Update to 3.2.6+ |
| vite | ^5.4.0 | High | Dev server — production uses nginx/Kong | Acceptable risk |
| esbuild | 0.21.5 (transitive) | High | Bundle tool — compile-time only | Acceptable risk |

## Container Image Audit

### Base Images

| Dockerfile | Base Image | Notes |
|-----------|-----------|-------|
| All Python services | `python:3.12-slim` | Current, supported |
| mock-odoo-api | `python:3.12-slim` | Uses pip (not uv) |
| airflow | `apache/airflow:2.9.0` | Version pinned |

### Image Build Verification

All 9 service Dockerfiles use the same pattern:
```dockerfile
FROM python:3.12-slim
COPY pyproject.toml /app/
COPY services/shared /app/services/shared
RUN uv sync --no-dev --directory /app/services/<svc>
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80XX"]
```

**Issue**: CMD uses `--port 80XX` but Dockerfile EXPOSE uses different port numbers. CMD port should match EXPOSE.

**Issue**: `uv sync --no-dev` excludes ruff, pytest, mypy — this is intentional for production images but means no linting in CI images.

## SBOM / Vulnerability Scanning

| Check | Status |
|-------|--------|
| Gitleaks config | ✅ Present (`.gitleaks.toml`) |
| SBOM generation | ❌ Not configured |
| Container image scanning | ❌ Not configured |
| License compliance | ❌ Not checked |
| Dependabot/Renovate | ❌ Not configured |

## CI Pipeline Dependency Validation

`ci.yml` `service-dependencies` job:
- Matrix across 10 services + `ipe_shared`
- Checks `uv run python -c "import ipe_shared; print('OK')"` for each service
- Validates shared library is importable

**Missing**: No vulnerability scanning, SBOM generation, or license checking in CI pipeline.

## Summary

| Metric | Status |
|--------|--------|
| Package pinning | ✅ Pinned (>= not ^) |
| Lock files present | ✅ Both uv.lock and pnpm-lock.yaml exist |
| Known CVEs | ⚠️ 3 dev-only CVEs |
| SBOM | ❌ Missing |
| Container scanning | ❌ Missing |
| License compliance | ❌ Not checked |
| Auto-update bot | ❌ Not configured |
| Workspace config | ⚠️ ml-svc in members list (needs verification) |
