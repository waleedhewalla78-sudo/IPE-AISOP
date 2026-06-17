# Incident Response Runbook

## Overview
This runbook defines the triage and escalation procedures for the IPE platform's critical alerts. It covers severity levels SEV1 (critical) through SEV3 (minor).

## Severity Definitions

| Severity | Definition | Response Time | Escalation |
|----------|-----------|---------------|-----------|
| SEV1 | Platform outage or data loss | 15 min | VP Engineering |
| SEV2 | Degraded performance or partial outage | 30 min | Engineering Lead |
| SEV3 | Minor issue, no customer impact | 4 hours | On-call engineer |

---

## Alert Playbooks

### Alert 1: Kafka Consumer Lag > 5 Minutes

**Severity**: SEV2 (SEV1 if lag continues > 15 min)

#### Triage Steps
```bash
# 1. Check consumer group lag across all services
kubectl exec -n ipe-platform deploy/kafka -- \
  kafka-consumer-groups --bootstrap-server kafka-headless:9092 --all-groups --describe

# 2. Identify the specific consumer with the highest lag
# Expected output format:
# GROUP                    TOPIC                          LAG
# ipe-dpe-svc              ipe.demand.created             3420
# ipe-alert-svc            ipe.mo.feasibility_scored      8900  <-- HIGH LAG

# 3. Check the slow consumer's logs for errors
kubectl logs -n ipe-platform deploy/alert-svc --tail=100 | grep -i error

# 4. Check resource utilization
kubectl top pod -n ipe-platform | grep alert-svc
```

#### Resolution Steps
```bash
# Option A: Increase consumer replicas (if CPU-bound)
kubectl scale deploy/alert-svc -n ipe-platform --replicas=4

# Option B: Restart the consumer (if stuck)
kubectl rollout restart deploy/alert-svc -n ipe-platform

# Option C: Increase Kafka partition count (structural fix)
kubectl exec -n ipe-platform deploy/kafka -- \
  kafka-topics --bootstrap-server kafka-headless:9092 \
  --alter --topic ipe.mo.feasibility_scored --partitions 6
```

#### Escalation
If lag is not decreasing after 15 minutes of intervention, escalate to Engineering Lead.

---

### Alert 2: OR-Tools Solver Timeout

**Severity**: SEV2

#### Triage Steps
```bash
# 1. Check solver logs in cap-svc
kubectl logs -n ipe-platform deploy/cap-svc --tail=50 | grep -i "solver\|timeout\|CP-SAT"

# 2. Check current queue depth
kubectl exec -n ipe-platform deploy/cap-svc -- \
  curl -s http://localhost:8004/health | jq .queue_depth

# 3. Check for unusually large scheduling requests
kubectl logs -n ipe-platform deploy/cap-svc --tail=200 | \
  grep -oP '"mo_ids":\[\K[^\]]+' | wc -w
```

#### Resolution Steps
```bash
# Option A: Increase solver timeout
kubectl set env deploy/cap-svc -n ipe-platform \
  SOLVER_TIMEOUT_SECONDS=60

# Option B: Scale up cap-svc
kubectl scale deploy/cap-svc -n ipe-platform --replicas=4

# Option C: Reduce scheduling horizon (emergency)
kubectl set env deploy/cap-svc -n ipe-platform \
  MAX_HORIZON_HOURS=72
```

#### Root Cause Analysis
Common causes:
- Large MO batch (> 500 MOs in single request)
- Complex routing with many shared work centers
- Insufficient CPU resources for CP-SAT solver

---

### Alert 3: Anthropic API Rate Limits (429 Errors)

**Severity**: SEV3 (SEV2 if sustained > 5 min)

#### Triage Steps
```bash
# 1. Verify rate limit errors in nlp-svc and del-svc
kubectl logs -n ipe-platform deploy/nlp-svc --tail=100 | grep "429\|rate_limit"

# 2. Check Anthropic dashboard for current usage
# https://console.anthropic.com/settings/usage
```

#### Resolution Steps
```bash
# Option A: Enable request queuing
kubectl set env deploy/nlp-svc -n ipe-platform \
  LLM_RATE_LIMIT_RPM=50 \
  LLM_BURST_SIZE=10

# Option B: Reduce model complexity (temporary bypass)
kubectl set env deploy/nlp-svc -n ipe-platform \
  LLM_MODEL=claude-instant-1.2

# Option C: Fall back to rule-based classification
kubectl set env deploy/del-svc -n ipe-platform \
  NLP_FALLBACK_ONLY=true
```

#### Escalation
Contact Anthropic support to request quota increase if sustained usage exceeds 80% of plan limit.

---

### Alert 4: PostgreSQL Connection Pool Exhaustion

**Severity**: SEV1

#### Triage Steps
```bash
# 1. Check active connections
kubectl exec -n ipe-platform deploy/postgres -- \
  psql -U ipe_app -d ipe -c "SELECT count(*) FROM pg_stat_activity;"

# 2. Check which services have the most connections
kubectl exec -n ipe-platform deploy/postgres -- \
  psql -U ipe_app -d ipe -c "SELECT application_name, count(*) FROM pg_stat_activity GROUP BY 1 ORDER BY 2 DESC;"

# 3. Check service pods for connection leaks
kubectl logs -n ipe-platform deploy/dpe-svc --tail=50 | grep -i "connection\|pool\|timeout"
```

#### Resolution Steps
```bash
# Option A: Increase max connections
kubectl set env deploy/postgres -n ipe-platform \
  POSTGRES_MAX_CONNECTIONS=200

# Option B: Reduce connection pool per service
kubectl set env deploy/dpe-svc deploy/mat-svc deploy/cap-svc -n ipe-platform \
  DB_POOL_SIZE=5 \
  DB_MAX_OVERFLOW=10

# Option C: Restart leaking service
kubectl rollout restart deploy -n ipe-platform -l !app.kubernetes.io/component=postgres
```

---

### Alert 5: High Memory Usage (OOMKilled Pods)

**Severity**: SEV2

#### Triage Steps
```bash
# 1. Check for OOMKilled pods
kubectl get pods -n ipe-platform | grep OOMKilled

# 2. Check memory trends
kubectl top pod -n ipe-platform --sort-by=memory

# 3. Check for memory leaks in logs
kubectl logs -n ipe-platform <oom-pod> --previous | tail -50
```

#### Resolution Steps
```bash
# Option A: Increase memory limits
kubectl set resources deploy/cap-svc -n ipe-platform \
  --limits memory=8Gi --requests memory=2Gi

# Option B: Reduce batch sizes via env vars
kubectl set env deploy/dpe-svc -n ipe-platform \
  BATCH_SIZE=25
```

---

### Alert 6: Odoo Connector Down

**Severity**: SEV2

#### Triage Steps
```bash
# 1. Check connector health
kubectl exec -n ipe-platform deploy/connector -- \
  curl -s http://localhost:8001/health | jq .

# 2. Check Odoo connectivity
kubectl logs -n ipe-platform deploy/connector --tail=50 | grep "odoo\|connection"

# 3. Check HMAC signature validation errors
kubectl logs -n ipe-platform deploy/connector --tail=50 | grep "HMAC\|signature"
```

#### Resolution Steps
```bash
# Option A: Restart connector
kubectl rollout restart deploy/connector -n ipe-platform

# Option B: Rotate HMAC key and update Odoo side
kubectl delete secret ipe-service-keys -n ipe-platform
# Then re-deploy to generate new keys

# Option C: Check export queue for stuck messages
kubectl exec -n ipe-platform deploy/postgres -- \
  psql -U ipe_app -d ipe -c "SELECT count(*) FROM ipe_export_queue WHERE status = 'pending' AND retry_count > 3;"
```

---

## On-Call Rotation

| Week | Primary | Secondary |
|------|---------|-----------|
| Week 1 | Engineer A | Engineer B |
| Week 2 | Engineer B | Engineer C |
| Week 3 | Engineer C | Engineer A |
| Week 4 | Engineer D | Engineer E |

## Escalation Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| Engineering Lead | Jane Doe | +1-555-0100 | jane@example.com |
| VP Engineering | John Smith | +1-555-0101 | john@example.com |
| SRE | DevOps Team | +1-555-0102 | sre@example.com |

## Post-Incident Review

After every SEV1/SEV2 incident, the on-call engineer must:
1. Complete the incident timeline in PagerDuty
2. File a post-mortem in `docs/post-mortems/YYYY-MM-DD-incident.md`
3. Update this runbook if new playbook steps are identified
4. Present findings at the weekly engineering review
