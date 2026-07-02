#!/usr/bin/env bash
# PostgreSQL backup for IPE (docker-compose db service).
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups/postgres}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/ipe_${TIMESTAMP}.sql.gz"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-ipe-db-1}"
POSTGRES_USER="${POSTGRES_USER:-ipe}"
POSTGRES_DB="${POSTGRES_DB:-ipe_test}"

mkdir -p "$BACKUP_DIR"

docker exec "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip > "$BACKUP_FILE"

echo "Backup: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

find "$BACKUP_DIR" -name "ipe_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete
