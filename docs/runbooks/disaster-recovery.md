# Disaster Recovery Runbook

## Overview
This runbook defines the procedures for recovering the IPE platform in the event of a catastrophic failure. The target RTO is **4 hours** and the target RPO is **15 minutes**.

## Architecture Assumptions
- **PostgreSQL**: AWS RDS with automated backups and continuous WAL archiving to S3
- **Model Artifacts**: Stored in S3 bucket `ipe-models-{env}` with versioning enabled
- **Docker Images**: Pulled from GitHub Container Registry (`ghcr.io/anomalyco`)
- **Kubernetes**: EKS cluster with managed node groups
- **Kafka**: Confluent Cloud with automatic data retention (7 days)

---

## Recovery Scenarios

### 1. Total Regional Outage (RDS + EKS Failure)

**RTO**: 4 hours | **RPO**: 15 minutes

#### Step 1: Activate Disaster Recovery
```bash
# Notify incident response team via PagerDuty
# Designate DR lead and confirm secondary region readiness
```

#### Step 2: Restore PostgreSQL from WAL Archives
```bash
# Identify the latest available backup
aws rds describe-db-snapshots \
  --db-instance-identifier ipe-production \
  --query 'DBSnapshots[?Status==`available`]' \
  --region us-west-2

# Restore to a new RDS instance in the DR region
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier ipe-dr \
  --db-snapshot-identifier arn:aws:rds:us-west-2:123456789012:snapshot:ipe-production-20240615 \
  --region eu-west-1

# Perform point-in-time recovery (target: 15 min before failure)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier ipe-production \
  --target-db-instance-identifier ipe-dr \
  --restore-time "2024-06-15T14:45:00Z" \
  --region eu-west-1
```

#### Step 3: Restore Model Artifacts from S3
```bash
# Sync the latest models to the DR region S3 bucket
aws s3 sync s3://ipe-models-prod/ s3://ipe-models-dr/ \
  --source-region us-west-2 --region eu-west-1
```

#### Step 4: Deploy Infrastructure to DR Cluster
```bash
# Switch kubectl context to DR cluster
kubectl config use-context ipe-dr-cluster

# Deploy infrastructure first
argocd app sync ipe-infrastructure

# Wait for PostgreSQL, Kafka, and Redis health checks
kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=postgres -n ipe-platform --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=kafka -n ipe-platform --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=redis -n ipe-platform --timeout=120s
```

#### Step 5: Run Database Migrations
```bash
# Apply any pending migrations
kubectl exec -n ipe-platform deploy/postgres -- \
  alembic upgrade head
```

#### Step 6: Deploy Application Services
```bash
argocd app sync ipe-services

# Verify all services are healthy
kubectl get pods -n ipe-platform
kubectl exec -n ipe-platform deploy/dpe-svc -- curl -s http://localhost:8002/health
```

#### Step 7: Validate Data Integrity
```bash
# Run data integrity checks
kubectl exec -n ipe-platform deploy/dpe-svc -- \
  python -c "from ipe_shared.database.session import get_session; ..."
```

#### Step 8: Update DNS
```bash
# Switch Route53 record to point to DR cluster's Kong proxy
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456 \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.ipe.example.com",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [{"Value": "<DR_CLUSTER_ELB_DNS>"}]
      }
    }]
  }'
```

---

### 2. Database Corruption (Logical Failure)

**RTO**: 2 hours | **RPO**: 15 minutes

#### Step 1: Quarantine the Corrupted Database
```bash
# Immediately stop application traffic
kubectl scale deploy -n ipe-platform --all --replicas=0

# Snapshot the corrupted database for forensic analysis
aws rds create-db-snapshot \
  --db-instance-identifier ipe-production \
  --db-snapshot-identifier ipe-corrupted-$(date +%Y%m%d%H%M)
```

#### Step 2: Point-in-Time Recovery
```bash
# Restore to the most recent clean state (before corruption)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier ipe-production \
  --target-db-instance-identifier ipe-recovered \
  --restore-time "2024-06-15T13:30:00Z" \
  --region us-west-2
```

#### Step 3: Rename and Redirect
```bash
# Rename the corrupted instance
aws rds modify-db-instance \
  --db-instance-identifier ipe-production \
  --new-db-instance-identifier ipe-corrupted-$(date +%Y%m%d)

# Rename the recovered instance to production name
aws rds modify-db-instance \
  --db-instance-identifier ipe-recovered \
  --new-db-instance-identifier ipe-production
```

#### Step 4: Verify and Restore Traffic
```bash
# Verify the recovered database
kubectl exec -n ipe-platform deploy/dpe-svc -- \
  python -c "from ipe_shared.database.session import ..."

# Scale services back up
kubectl scale deploy -n ipe-platform --all --replicas=2
```

---

### 3. Kafka Cluster Failure

**RTO**: 1 hour | **RPO**: 0 (Confluent Cloud managed)

#### Step 1: Fall Back to Confluent Cloud
```bash
# Update Kafka bootstrap servers in the global ConfigMap
kubectl patch configmap ipe-platform-config -n ipe-platform \
  --type merge -p '{"data":{"KAFKA_BOOTSTRAP_SERVERS":"pkc-xxxxx.confluent.cloud:9092"}}'

# Restart all services to pick up the new config
kubectl rollout restart deploy -n ipe-platform
```

#### Step 2: Verify Messages Are Not Lost
```bash
# Check consumer lag using Confluent Cloud CLI
confluent kafka consumer group list
confluent kafka consumer group describe ipe-alert-svc

# If lag exists, verify DLQ for unprocessed messages
```

---

### 4. Model Artifact Corruption

**RTO**: 30 minutes | **RPO**: 1 day (daily model snapshots in S3)

#### Step 1: Revert to Previous Model Version
```bash
# List available model versions in S3
aws s3api list-object-versions \
  --bucket ipe-models-prod \
  --prefix models/supplier_reliability/

# Download the last known good version
aws s3api get-object \
  --bucket ipe-models-prod \
  --key models/supplier_reliability/20240614.pkl \
  --version-id <VERSION_ID> \
  models/supplier_reliability.pkl

# Re-upload as the current version
aws s3 cp models/supplier_reliability.pkl \
  s3://ipe-models-prod/models/supplier_reliability/current.pkl
```

#### Step 2: Trigger Model Reload
```bash
# Restart services that cache models in memory
kubectl rollout restart deploy/mat-svc deploy/cap-svc -n ipe-platform
```

---

## Testing the DR Plan

The DR plan must be tested quarterly per SOC 2 requirements.

```bash
# Quarterly DR test script
./scripts/dr-test.sh \
  --region-dr eu-west-1 \
  --snapshot-id ipe-production-$(date +%Y%m%d) \
  --target-rto-minutes 240
```

## Post-Mortem Checklist
- [ ] Root cause identified and documented
- [ ] All monitoring alerts reviewed
- [ ] Data integrity verified (WAL gap analysis)
- [ ] RTO/RPO targets met
- [ ] Runbook updated with lessons learned
- [ ] Incident report filed in compliance repository
