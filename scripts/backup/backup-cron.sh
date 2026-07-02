#!/usr/bin/env bash
# Daily backup entrypoint — schedule via cron at 02:00 or Kubernetes CronJob.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${LOG_FILE:-/var/log/ipe-backup.log}"

{
  echo "=== IPE backup started $(date -Is) ==="
  bash "${SCRIPT_DIR}/pg-backup.sh"
  bash "${SCRIPT_DIR}/volume-backup.sh"
  echo "=== IPE backup finished $(date -Is) ==="
} >>"$LOG_FILE" 2>&1
