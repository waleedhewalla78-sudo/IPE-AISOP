# T090 R2 Stack Health — 2026-08-15

**Branch:** `033-phase9-wave9a`  
**Compose:** `infrastructure/docker/docker-compose.release2.yml`

## 1. .env
Present; keys assumed from template (not committed).

## 2. Ports pre-flight
8000, 8082, 5433, 6380, 8020, 8120 — free before up.

## 3. Stack up
- Initial `up -d` failed once: `connector` healthcheck timeout (5s) during cold start → blocked Kong/web depends_on.
- After connector became healthy, `up -d kong web-ui cap-svc` succeeded.
- Services now Up; demo-critical healthy or responding.

## 4. Migration head
`alembic_version` = **082** ✓

## 5. Per-service (snapshot)

| Service | Status | Notes |
|---------|--------|-------|
| db | healthy | :5433 |
| redis | healthy | :6380 |
| dpe-svc | up | health 200 |
| fea-svc | up | health 200 |
| upload-svc | healthy | health 200 |
| mat-svc | healthy | |
| res-svc | healthy | |
| connector | healthy | after warm |
| cap-svc | up | |
| kong | health starting → routes work | `/api/v1/health` 200 via :8000 |
| web-ui | starting → **200** on :8082 | |
| nlp/sop/scenario/demand | up/healthy | non-blocking warnings OK |

## 6. Endpoint smoke
| URL | Result |
|-----|--------|
| http://localhost:8082/ | **200** |
| http://localhost:8000/api/v1/health | **200** (dpe) |
| http://localhost:8020/api/v1/health | **200** |
| http://localhost:8120/api/v1/health | **200** |
| http://localhost:8004/api/v1/health | **200** |
| http://localhost:8000/ | 404 (expected Kong no root) |

## 7. VERDICT

**YELLOW** — all demo-critical services reachable; initial connector healthcheck flake noted (timeout 5s cold). Stack left **UP**.

Remediation optional: raise connector healthcheck timeout in compose (deferred — do not change compose mid-Batch0 unless blocking).
