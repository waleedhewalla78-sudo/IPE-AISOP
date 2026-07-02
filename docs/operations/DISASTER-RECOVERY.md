# IPE Disaster Recovery Runbook

**Release:** v9.1.0-r2 / Phase 1  
**RTO target:** 4 hours  
**RPO target:** 24 hours (daily backups)

## Backup locations

| Asset | Script | Default path |
|-------|--------|--------------|
| PostgreSQL | `scripts/backup/pg-backup.sh` | `/backups/postgres/ipe_YYYYMMDD_HHMMSS.sql.gz` |
| Docker volumes | `scripts/backup/volume-backup.sh` | `/backups/volumes/` |
| Scheduled | `scripts/backup/backup-cron.sh` | `/var/log/ipe-backup.log` |

Environment overrides: `POSTGRES_CONTAINER`, `POSTGRES_USER`, `POSTGRES_DB`, `BACKUP_DIR`, `RETENTION_DAYS`.

---

## Scenario 1: Database corruption

1. Stop application services (keep `db` if you need in-place restore):
   ```bash
   docker compose -f infrastructure/docker/docker-compose.release1.yml stop \
     dpe-svc fea-svc cap-svc res-svc connector kong web-ui
   ```
2. Identify last good backup:
   ```bash
   ls -lt /backups/postgres/
   ```
3. Restore:
   ```bash
   bash scripts/backup/pg-restore.sh /backups/postgres/ipe_YYYYMMDD_HHMMSS.sql.gz
   ```
4. Verify row counts:
   ```bash
   docker exec ipe-db-1 psql -U ipe -d ipe_test -c \
     "SELECT COUNT(*) FROM cdm_manufacturing_order;"
   ```
5. Restart stack:
   ```bash
   docker compose -f infrastructure/docker/docker-compose.release1.yml up -d
   ```
6. Health check:
   ```bash
   curl -s http://localhost:8000/api/v1/health | jq .
   ```
7. Integration demo:
   ```powershell
   .\scripts\run-release1-integration-demo.ps1
   ```

---

## Scenario 2: Full server loss

1. Provision new server (Docker, compose, git).
2. Clone repo and checkout tagged release: `git checkout v9.1.0-r2`.
3. Restore off-site backups (S3/GCS) to `/backups/`.
4. Generate JWT keys: `bash scripts/generate-jwt-keys.sh`
5. Setup Keycloak: `bash scripts/setup-keycloak.sh`
6. Seed Vault: `bash scripts/vault-init.sh`
7. TLS certs: `bash scripts/generate-dev-certs.sh` (or restore from backup).
8. Start infrastructure:
   ```bash
   docker compose -f infrastructure/docker/docker-compose.release1.yml up -d
   ```
9. Restore database: `bash scripts/backup/pg-restore.sh <backup>`
10. Restore volumes from tarballs if needed.
11. Verify: run demo scripts and k6 baseline.

---

## Scenario 3: Kafka consumer crash mid-batch

IPE consumers use **manual commit** (`enable_auto_commit=False`) with **at-least-once** semantics:

- Offsets commit only after successful handler execution.
- Idempotency keys in Redis (`ipe:processed:{service}:{event_id}`) prevent duplicate side effects.
- `auto_offset_reset='earliest'` on new consumer groups replays from topic start.

**On restart after crash:**

| Phase | Behavior |
|-------|----------|
| Before handler completes | Message redelivered; idempotency skip if already marked |
| After handler, before commit | Message redelivered; handler must be idempotent |
| After commit | Next message consumed |

Failed messages go to DLQ topic `ipe.dlq.{service_name}` and offset is committed to avoid poison-pill loops.

---

## Recovery verification checklist

- [ ] `GET /api/v1/health` returns `healthy` with database up
- [ ] MDR composite ≥ 70% for Star Trans tenant
- [ ] Release 1 demo 14/14 PASS
- [ ] Release 2 demo 5/5 PASS (if enabled)
- [ ] k6 P95 < 500ms at 50 VUs

---

## Contacts & escalation

Document on-call rotation and backup storage credentials in your internal ops wiki (not in git).
