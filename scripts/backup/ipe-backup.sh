#!/bin/bash
# IPE Daily Backup Script
# Usage: ./ipe-backup.sh [backup_dir]
# Schedule: crontab -e → 0 2 * * * /path/to/ipe-backup.sh /path/to/backups

BACKUP_DIR="${1:-/var/backups/ipe}"
DATE=$(date +%Y-%m-%d)
FILENAME="ipe-backup-${DATE}.dump"
LOG_FILE="${BACKUP_DIR}/backup.log"
RETENTION_DAYS=7

# Resolve compose directory: scripts/backup -> repo root, or deploy/star-trans if present
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_DIR="${COMPOSE_DIR:-}"
if [ -z "$COMPOSE_DIR" ]; then
  if [ -f "${SCRIPT_DIR}/../../deploy/star-trans/docker-compose.yml" ]; then
    COMPOSE_DIR="${SCRIPT_DIR}/../../deploy/star-trans"
  elif [ -f "${SCRIPT_DIR}/../../docker-compose.yml" ]; then
    COMPOSE_DIR="${SCRIPT_DIR}/../.."
  else
    COMPOSE_DIR="$(pwd)"
  fi
fi

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..." >> "$LOG_FILE"

docker compose -f "${COMPOSE_DIR}/docker-compose.yml" exec -T db pg_dump -U ipe -Fc ipe > "${BACKUP_DIR}/${FILENAME}" 2>> "$LOG_FILE"

if [ $? -eq 0 ]; then
    SIZE=$(du -h "${BACKUP_DIR}/${FILENAME}" | cut -f1)
    echo "[$(date)] SUCCESS: ${FILENAME} (${SIZE})" >> "$LOG_FILE"
else
    echo "[$(date)] ERROR: Backup failed!" >> "$LOG_FILE"
    exit 1
fi

# Cleanup old backups
find "$BACKUP_DIR" -name "ipe-backup-*.dump" -mtime +${RETENTION_DAYS} -delete
echo "[$(date)] Cleaned backups older than ${RETENTION_DAYS} days" >> "$LOG_FILE"
