# T090 R2 Stack Health — 2026-08-24 (continuation refresh)

**Branch:** `033-phase9-wave9a`  
**Compose:** `infrastructure/docker/docker-compose.release2.yml`  
**Prior:** `T090-R2-STACK-HEALTH-2026-08-14.md` (2026-08-15 run)

## 1. .env

Present. Keys present (values not committed): `IPE_DATABASE_URL`, `IPE_REDIS_URL`, `IPE_KAFKA_BOOTSTRAP_SERVERS`, `IPE_JWT_SECRET_KEY`.

## 2. Port availability pre-flight

Host **5433** was held by non-IPE `al-azhar-girls-faculty-portal-db-1`. User authorized stop. After stop: 5433, 6380, 8000, 8082, 8020, 8120, 8016, 8002–8005, 8007, 8443 free.

## 3. Stack up

- `docker compose … down` then `up -d`.
- First `up -d` failed: **connector** healthcheck timeout (cold start) — same flake as 2026-08-15.
- After connector became healthy (~2–3 min), second `up -d` started **cap-svc**, **kong**, **web-ui**. Exit 0.
- Transient `ipe-network` label mismatch after a failed subset start; empty leftover network removed; retry succeeded.

## 4. Migration head

`alembic_version` = **082** ✓ (`cdm_platform_advanced`)

No `migrate` service in this compose file. Volume `r2_db_data` retained prior schema + seed.

## 5. Per-service health

| Service | Status | Notes |
|---------|--------|-------|
| db | healthy | :5433 |
| redis | healthy | :6380 |
| dpe-svc | up | health 200 via :8020 and Kong |
| fea-svc | up | health 200 |
| upload-svc | healthy | health 200 |
| mat-svc | healthy | health 200 |
| res-svc | healthy | health 200 |
| cap-svc | up | health 200 |
| connector | healthy | after warm (initial unhealthy) |
| kong | healthy | :8000; admin 8001 **not published** to host |
| web-ui | healthy | :8082 HTTP 200 |
| nlp / sop / demand / scenario | healthy | non-demo-critical |

## 6. Endpoint smoke

| URL | Result |
|-----|--------|
| http://localhost:8082/ | **200** |
| http://localhost:8000/ | 404 (Kong no root — expected) |
| http://localhost:8000/api/v1/health | **200** JSON `dpe-svc` |
| http://localhost:8020/api/v1/health | **200** |
| http://localhost:8120/api/v1/health | **200** |
| http://localhost:8004/api/v1/health | **200** |

## 7. Seed persistence (not re-run)

`cdm_manufacturing_order` count = **28** (T092 volume survived; not a fresh seed this session).

## 8. VERDICT

**YELLOW** — demo-critical services reachable after connector warm; stack left **UP**. Do not treat connector cold-start flake as a compose edit in this prompt.

## 9. Remediation (optional, not done)

Raise connector healthcheck `start_period` / timeout so `up -d` does not fail on cold start.
