#!/bin/sh
set -eu

TEMPLATE="/etc/alertmanager/alertmanager.yml"
OUT="/alertmanager/alertmanager.rendered.yml"
mkdir -p /alertmanager

if [ -n "${ALERTMANAGER_SLACK_URL:-}" ]; then
  sed "s|\${ALERTMANAGER_SLACK_URL}|${ALERTMANAGER_SLACK_URL}|g" "$TEMPLATE" > "$OUT"
else
  awk '
    /^inhibit_rules:/ { skip=0 }
    skip { next }
    /^  - name: '\''slack-critical'\''/ { skip=1; next }
    /^  - name: '\''slack-warning'\''/ { skip=1; next }
    /slack_api_url:/ { next }
    { gsub(/receiver: '\''slack-critical'\''/, "receiver: '\''default'\''");
      gsub(/receiver: '\''slack-warning'\''/, "receiver: '\''default'\''");
      print }
  ' "$TEMPLATE" > "$OUT"
fi

exec /bin/alertmanager \
  --config.file="$OUT" \
  --storage.path=/alertmanager
