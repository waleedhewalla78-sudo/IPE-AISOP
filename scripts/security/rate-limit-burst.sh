#!/usr/bin/env bash
# Burst enough requests to exceed Kong global 500/min IP limit.
set -eo pipefail
URL="${1:-http://localhost:8000/api/v1/health}"
COUNT="${2:-520}"
WORKERS="${3:-80}"

PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY=python
if command -v uv >/dev/null 2>&1; then
  PY_RUN=(uv run python)
else
  PY_RUN=("$PY")
fi

export BURST_URL="$URL" BURST_COUNT="$COUNT" BURST_WORKERS="$WORKERS"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IPE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Burst $COUNT requests ($WORKERS workers) to $URL"
if OUTPUT=$(cd "$IPE_ROOT/services/res-svc" && "${PY_RUN[@]}" <<'PY'
import os
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import requests

url = os.environ["BURST_URL"]
count = int(os.environ["BURST_COUNT"])
workers = int(os.environ["BURST_WORKERS"])

def hit(_):
    try:
        return requests.get(url, timeout=10).status_code
    except Exception:
        return 0

with ThreadPoolExecutor(max_workers=workers) as ex:
    codes = Counter(ex.map(hit, range(count)))

for code, n in sorted(codes.items(), key=lambda x: str(x[0])):
    print(f"  HTTP {code}: {n}")
sys.exit(0 if codes.get(429, 0) > 0 else 1)
PY
); then
  echo "$OUTPUT"
  echo "429 observed"
  exit 0
else
  echo "$OUTPUT"
  echo "no 429 in burst"
  exit 1
fi
