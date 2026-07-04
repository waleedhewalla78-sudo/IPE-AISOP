#!/usr/bin/env bash
set -eo pipefail
URL="${1:-http://localhost:8000/api/v1/health}"
LAST="000"
for i in $(seq 1 510); do
  LAST=$(curl -so /dev/null -w "%{http_code}" "$URL" 2>/dev/null || echo "000")
  if [[ "$LAST" == "429" ]]; then
    echo "429 at request $i"
    exit 0
  fi
done
echo "last: $LAST"
exit 1
