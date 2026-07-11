#!/bin/bash
# Schedule IPE health check every 5 minutes
DIR="$(cd "$(dirname "$0")" && pwd)"
chmod +x "${DIR}/ipe-health-check.sh"
(crontab -l 2>/dev/null; echo "*/5 * * * * ${DIR}/ipe-health-check.sh /var/log/ipe-health.log") | sort -u | crontab -
echo "Health monitoring: every 5 minutes → /var/log/ipe-health.log"
