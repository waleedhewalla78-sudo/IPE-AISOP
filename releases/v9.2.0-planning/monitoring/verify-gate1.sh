#!/usr/bin/env bash
# Gate 1: Observability Stack verification (Phase 2)
set -eo pipefail

KONG="${KONG_URL:-http://localhost:8000}"
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY=python

echo "=== Gate 1: Observability Stack Verification ==="

echo ""
echo "--- Step 2: /metrics checks ---"
LOGIN=$(curl -sf -X POST "$KONG/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"Ahmed@nour","password":"admin"}' 2>/dev/null || echo "{}")
TOKEN=$("$PY" -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('access_token',''))" <<<"$LOGIN" 2>/dev/null || echo "")
if [[ -z "$TOKEN" ]]; then
  echo "  WARN: could not obtain JWT — Kong metrics checks may return 401"
fi
AUTH="Authorization: Bearer $TOKEN"

echo "2a) Spec paths via Kong (/api/v1/<svc>/metrics) — not routed in R1 Kong:"
KONG_METRICS_PASS=0
KONG_METRICS_TOTAL=0
for svc in bom-svc res-svc inv-svc feas-svc sched-svc dpe-svc copilot-svc; do
  STATUS=$(curl -so /dev/null -w "%{http_code}" "$KONG/api/v1/$svc/metrics" -H "$AUTH" 2>/dev/null || echo "000")
  echo "  $svc via Kong: $STATUS"
  KONG_METRICS_TOTAL=$((KONG_METRICS_TOTAL + 1))
  [[ "$STATUS" == "200" ]] && KONG_METRICS_PASS=$((KONG_METRICS_PASS + 1))
done

echo ""
echo "2b) R1 deployed services — direct /metrics (Prometheus scrape path):"
declare -A R1_PORTS=( ["dpe-svc"]=8020 ["fea-svc"]=8004 ["res-svc"]=8005 ["cap-svc"]=8003 ["connector"]=8016 )
DIRECT_PASS=0
DIRECT_TOTAL=0
for svc in dpe-svc fea-svc res-svc cap-svc connector; do
  port="${R1_PORTS[$svc]}"
  STATUS=$(curl -so /dev/null -w "%{http_code}" "http://localhost:${port}/metrics" 2>/dev/null || echo "000")
  echo "  $svc :${port}/metrics: $STATUS"
  DIRECT_TOTAL=$((DIRECT_TOTAL + 1))
  [[ "$STATUS" == "200" ]] && DIRECT_PASS=$((DIRECT_PASS + 1))
done

echo ""
echo "--- Step 3: Prometheus targets ---"
curl -sf http://localhost:9090/api/v1/targets | "$PY" -c "
import sys, json
data = json.load(sys.stdin)
targets = data['data']['activeTargets']
up = down = 0
for t in sorted(targets, key=lambda x: x['labels'].get('job','')):
    job = t['labels'].get('job','?')
    health = t['health']
    url = t['scrapeUrl']
    print(f'  {job:22s} {health:10s} {url}')
    up += health == 'up'
    down += health != 'up'
print(f'  --- TOTAL: {up} up, {down} down, {len(targets)} targets ---')
"

echo ""
echo "--- Step 4: Grafana dashboards ---"
curl -sf -u admin:admin http://localhost:3000/api/search | "$PY" -c "
import sys, json
data = json.load(sys.stdin)
print(f'  Dashboard count: {len(data)}')
for d in data:
    print(f\"  Dashboard: {d['title']} (uid: {d['uid']})\")
"

echo ""
echo "--- Step 5: Prometheus alert rules ---"
curl -sf "http://localhost:9090/api/v1/rules" | "$PY" -c "
import sys, json
data = json.load(sys.stdin)
groups = data.get('data', {}).get('groups', [])
rules = 0
for group in groups:
    for rule in group.get('rules', []):
        rules += 1
        print(f\"  {rule['name']:40s} state={rule.get('state','N/A')}\")
print(f'  --- TOTAL: {rules} rules in {len(groups)} groups ---')
"

echo ""
echo "============================================="
IPE_DASHBOARDS=$(curl -sf -u admin:admin http://localhost:3000/api/search | "$PY" -c "import sys,json; print(sum(1 for d in json.load(sys.stdin) if d.get('title','').startswith('IPE ')))" 2>/dev/null || echo "0")
TARGETS_UP=$(curl -sf http://localhost:9090/api/v1/targets | "$PY" -c "import sys,json; t=json.load(sys.stdin)['data']['activeTargets']; print(sum(1 for x in t if x['health']=='up'))" 2>/dev/null || echo "0")
TARGETS_TOTAL=$(curl -sf http://localhost:9090/api/v1/targets | "$PY" -c "import sys,json; print(len(json.load(sys.stdin)['data']['activeTargets']))" 2>/dev/null || echo "0")
RULES=$(curl -sf http://localhost:9090/api/v1/rules | "$PY" -c "import sys,json; print(sum(len(g.get('rules',[])) for g in json.load(sys.stdin).get('data',{}).get('groups',[])))" 2>/dev/null || echo "0")

GATE_PASS=true
[[ "$DIRECT_PASS" -eq "$DIRECT_TOTAL" ]] || GATE_PASS=false
[[ "$TARGETS_UP" -eq "$TARGETS_TOTAL" ]] || GATE_PASS=false
[[ "$IPE_DASHBOARDS" -ge 6 ]] || GATE_PASS=false
[[ "$RULES" -ge 9 ]] || GATE_PASS=false

echo "  GATE 1 SUMMARY"
echo "  Direct /metrics (R1):          $DIRECT_PASS/$DIRECT_TOTAL returned 200"
echo "  Prometheus targets UP:         $TARGETS_UP/$TARGETS_TOTAL"
echo "  IPE Grafana dashboards:        $IPE_DASHBOARDS (need ≥6)"
echo "  Alert rules loaded:            $RULES (need ≥9)"
echo "  Kong /api/v1/*/metrics:        $KONG_METRICS_PASS/$KONG_METRICS_TOTAL (404 expected — use direct /metrics)"
if [[ "$GATE_PASS" == true ]]; then
  echo "  RESULT: PASS"
else
  echo "  RESULT: FAIL (see items above)"
fi
echo "============================================="

[[ "$GATE_PASS" == true ]]
