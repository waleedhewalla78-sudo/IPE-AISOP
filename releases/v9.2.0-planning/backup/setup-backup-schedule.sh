#!/bin/bash
# Add daily IPE backup to crontab (02:00)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="/var/backups/ipe"
mkdir -p "$BACKUP_DIR"
chmod +x "${SCRIPT_DIR}/ipe-backup.sh"
(crontab -l 2>/dev/null; echo "0 2 * * * ${SCRIPT_DIR}/ipe-backup.sh ${BACKUP_DIR}") | sort -u | crontab -
echo "Daily backup scheduled at 02:00 → ${BACKUP_DIR}"
