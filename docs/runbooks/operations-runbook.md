# IPE Operations Runbook — Day 2 Procedures

## Overview
This runbook provides step-by-step instructions for common Day-2 operations tasks required by the IPE SRE team.

---

## 1. Restarting a Stuck Kafka Consumer

### Symptoms
- Grafana alert `IPEKafkaLag` firing (consumer lag > 1000 for 10 min)
- Events not being processed (e.g., demand classifications stalled)

### Procedure

**Step 1: Identify the stuck consumer**
```bash
kubectl exec -n ipe-platform deploy/kafka -- \
  kafka-consumer-groups --bootstrap-server kafka-headless:9092 --all-groups --describe

# Look for groups with LAG > 0 for more than 10 minutes
# Example output:
# GROUP              TOPIC                     CURRENT-OFFSET  LOG-END-OFFSET  LAG
# ipe-dpe-svc        ipe.demand.created        1500            2500            1000
```

**Step 2: Check consumer logs for errors**
```bash
kubectl logs -n ipe-platform deploy/dpe-svc --tail=100 | grep -i "error\|exception\|timeout"
```

**Step 3: Restart the consumer**
```bash
# Graceful restart — ArgoCD will restore the desired replica count
kubectl rollout restart deploy/dpe-svc -n ipe-platform

# Monitor lag decrease
kubectl exec -n ipe-platform deploy/kafka -- \
  kafka-consumer-groups --bootstrap-server kafka-headless:9092 \
  --group ipe-dpe-svc --describe
```

**Step 4: Investigate root cause**
- Check for Poison Pill messages (malformed payloads) in the DLQ topic: `ipe.dlq.dpe-svc`
- Check service resource utilization: `kubectl top pod -n ipe-platform | grep dpe-svc`

---

## 2. Manually Triggering Airflow ML Retraining DAG

### When to use
- After new tenant data is loaded
- When ML drift alert `IPEMLDrift` fires
- Weekly scheduled retrain missed due to infrastructure issue

### Procedure

**Step 1: Verify Airflow is healthy**
```bash
kubectl get pods -n ipe-platform | grep airflow
# Expected: airflow-scheduler Running, airflow-webserver Running
```

**Step 2: Trigger the retrain DAG**
```bash
# Via Airflow CLI (requires Airflow pod access)
AIRFLOW_POD=$(kubectl get pod -n ipe-platform -l component=scheduler -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n ipe-platform $AIRFLOW_POD -- \
  airflow dags trigger retrain_models

# Verify the DAG run
kubectl exec -n ipe-platform $AIRFLOW_POD -- \
  airflow dags list-runs -d retrain_models
```

**Step 3: Monitor model evaluation**
```bash
# Check the evaluation step in the Airflow UI
# Or via CLI:
kubectl exec -n ipe-platform $AIRFLOW_POD -- \
  airflow tasks states-for-dag-run retrain_models --state success

# Verify new model is promoted
kubectl exec -n ipe-platform deploy/mat-svc -- \
  curl -s http://localhost:8003/health | jq .model_version
```

**Step 4: Validate model performance**
```bash
python scripts/validation/shadow_mode_comparison.py \
  --tenant-id <TENANT_UUID> \
  --historical-mos 100 \
  --output /tmp/retrain-validation.json

cat /tmp/retrain-validation.json
# Expected: "pass": true
```

---

## 3. Rotating the Odoo Connector HMAC Secret

### When to use
- Scheduled quarterly secret rotation (SOC 2 compliance)
- Suspected key compromise
- Employee offboarding with access to the Odoo instance

### Procedure

**Step 1: Generate a new HMAC key**
```bash
NEW_HMAC_KEY=$(openssl rand -hex 32)
echo "New HMAC key: $NEW_HMAC_KEY"
```

**Step 2: Update the Kubernetes secret**
```bash
# Patch the existing secret
kubectl patch secret ipe-service-keys -n ipe-platform \
  --type merge -p "{\"stringData\":{\"connector-hmac-key\":\"$NEW_HMAC_KEY\"}}"

# Restart the connector to pick up the new key
kubectl rollout restart deploy/connector -n ipe-platform
```

**Step 3: Verify connector health**
```bash
sleep 10
kubectl exec -n ipe-platform deploy/connector -- \
  curl -s http://localhost:8001/health | jq .
# Expected: {"status": "healthy"}
```

**Step 4: Update the Odoo side**
1. Log into Odoo admin interface
2. Navigate to **IPE Connector > Configuration**
3. Update the **HMAC Shared Secret** field with the new key
4. Test the connection by triggering a test export

**Step 5: Verify end-to-end flow**
```bash
# Trigger a test demand sync via Odoo
# Check that the connector processes the message
kubectl logs -n ipe-platform deploy/connector --tail=20 | grep "HMAC\|signature"
# Expected: "HMAC signature verified"
```

---

## Escalation Matrix

| Level | Team | Contact | Response Time | Scope |
|-------|------|---------|---------------|-------|
| L1 | SRE (On-Call) | PagerDuty: `ipe-sre` | 15 min | Platform infrastructure, restart, incident triage |
| L2 | Platform Engineering | Slack: `#ipe-platform-eng` | 30 min | Code-level debugging, architectural issues, deployment fixes |
| L3 | Core AI Team | Slack: `#ipe-core-ai` | 1 hour | ML model issues, algorithm bugs, solver misconfigurations |

### Escalation Flow

```
Incident Detected (Grafana Alert / PagerDuty)
       |
       v
[L1] SRE On-Call triages (15 min)
       |
       +-- Resolved? --> Post-mortem
       |
       v   No
[L2] Platform Engineering (30 min)
       |
       +-- Resolved? --> Post-mortem
       |
       v   No
[L3] Core AI Team (1 hour)
       |
       +-- Resolved? --> Post-mortem
       |
       v   No
Executive Escalation -- VP Engineering notified
```

### Communication Channels

| Channel | Purpose |
|---------|---------|
| `#ipe-alerts` | Grafana/PagerDuty alert notifications (read-only) |
| `#ipe-incidents` | Active incident coordination |
| `#ipe-postmortem` | Post-incident review discussion |
| `ipe-sre@example.com` | SRE team email for scheduled maintenance |
