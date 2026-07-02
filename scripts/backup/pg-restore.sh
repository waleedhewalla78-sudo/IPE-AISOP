#!/usr/bin/env bash
# Restore PostgreSQL backup into IPE db container.
set -euo pipefail

BACKUP_FILE="${1:-}"
if [[ -z "$BACKUP_FILE" ]]; then
  echo "Usage: pg-restore.sh <backup-file.sql.gz>"
  exit 1
fi
if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-ipe-db-1}"
POSTGRES_USER="${POSTGRES_USER:-ipe}"
POSTGRES_DB="${POSTGRES_DB:-ipe_test}"

echo "Restoring $BACKUP_FILE into $POSTGRES_CONTAINER ($POSTGRES_DB)..."
gunzip -c "$BACKUP_FILE" | docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
echo "Restore complete."
