# Tenant Onboarding Runbook (Shadow Mode)

## Overview
This runbook defines the 4-week Shadow Mode onboarding process for new enterprise tenants. Shadow Mode runs IPE recommendations in parallel with the customer's existing planning process without affecting production decisions.

## Onboarding Timeline

### Phase 0: Pre-Onboarding (Week 0)

#### Prerequisites
- [ ] Tenant signs data sharing agreement
- [ ] Tenant provides API access to their ERP system (Odoo, SAP, or D365)
- [ ] Tenant designates a planning team point of contact
- [ ] Network connectivity established (VPN or private link)
- [ ] Tenant user accounts created in IPE (min 3: planner, manager, viewer)

---

### Week 1: Data Integration & Quality Audit

#### Day 1-2: Initial Data Load
```bash
# Provision tenant in IPE
./scripts/provision-tenant.sh \
  --tenant-name "AcmeCorp" \
  --tier "enterprise" \
  --admin-email "planner@acmecorp.com"

# Load initial dataset
python scripts/load-anonymized-staging-data.py \
  --tenant "AcmeCorp" \
  --mos 1000 \
  --supply-orders 500
```

#### Day 3-5: Data Quality Audit
Run the following queries to validate data quality against minimum thresholds:

| Metric | Minimum Threshold | Query |
|--------|------------------|-------|
| BOM Completeness | ≥ 80% | `SELECT COUNT(*) FROM cdm_bom WHERE components IS NULL OR components = '{}'` |
| Lead Time Accuracy | ≥ 60% | `SELECT AVG(1 - ABS(actual_lead_days - planned_lead_days) / NULLIF(planned_lead_days, 0)) FROM cdm_supply_order WHERE planned_lead_days > 0` |
| MO Completeness | ≥ 90% | `SELECT COUNT(*) FROM cdm_manufacturing_order WHERE routing_id IS NULL` |
| Work Center Definition | ≥ 85% | `SELECT COUNT(*) FROM cdm_work_center WHERE capacity_hours <= 0` |
| Supplier Data | ≥ 70% | `SELECT COUNT(*) FROM cdm_supplier WHERE lead_time_days IS NULL` |
| Historical ATP Data | ≥ 500 records | `SELECT COUNT(*) FROM cdm_demand_history` |

**Pass Criteria**: All metrics meet or exceed thresholds. If not, schedule a data remediation meeting with the tenant.

---

### Week 2: ML Model Training & Calibration

#### Day 8-9: Train Tenant-Specific Models
```bash
# Train demand prediction model
curl -X POST https://api.ipe.example.com/api/v1/demand/train \
  -H "X-Tenant-ID: <TENANT_UUID>" \
  -H "Authorization: Bearer <TOKEN>"

# Train supplier reliability model
curl -X POST https://api.ipe.example.com/api/v1/material/train-supplier-model \
  -H "X-Tenant-ID: <TENANT_UUID>" \
  -H "Authorization: Bearer <TOKEN>"
```

#### Day 10-11: Validate Model Performance
```bash
# Run model evaluation
python scripts/validation/shadow_mode_comparison.py \
  --tenant-id <TENANT_UUID> \
  --historical-mos 100 \
  --output /tmp/shadow-report.json

# Verify improvement delta is positive (IPE > historical)
cat /tmp/shadow-report.json | jq .
# Expected: {"ipe_predicted_otd": 92.5, "historical_actual_otd": 84.0, "improvement_delta": 8.5, "pass": true}
```

**Pass Criteria**: Improvement delta > 0 (IPE's predicted on-time delivery exceeds historical actuals).

#### Day 12: Calibration Review
- Review false positive/negative rates for feasibility scoring
- Adjust priority weight thresholds if needed (`tenant_config["priority_weights"]`)
- Verify Copilot responses are accurate and relevant

---

### Week 3: Shadow Mode Parallel Run

#### Day 15-16: Enable Shadow Mode
```bash
# Enable shadow mode for the tenant
curl -X PATCH https://api.ipe.example.com/api/v1/admin/tenants/<TENANT_UUID> \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{"shadow_mode": true, "planner_notification": "daily_digest"}'
```

#### Day 17-21: Monitor and Compare
- IPE generates recommendations in the background
- Planners receive daily digest emails comparing IPE recommendations vs actual decisions
- Review dashboard for:
  - **On-Time Delivery Comparison** (IPE vs planner)
  - **Constraint Resolution Rate** (automated vs manual)
  - **Copilot Adoption** (queries per planner per day)
  - **Alert Accuracy** (true positive rate)

#### Weekly Checkpoint Meeting Agenda
1. Review last week's comparison metrics
2. Discuss specific cases where IPE disagreed with planners
3. Identify false positives/negatives in alerting
4. Collect planner feedback on Copilot responses
5. Adjust configuration parameters as needed

---

### Week 4: Go/No-Go Decision

#### Day 22-24: Final Validation
```bash
# Run final shadow mode comparison
python scripts/validation/shadow_mode_comparison.py \
  --tenant-id <TENANT_UUID> \
  --historical-mos 500 \
  --output /tmp/final-shadow-report.json

# Validate all alert rules fired correctly
# Check no critical alerts were missed
# Verify system performance under load
```

#### Day 25: Go/No-Go Checklist

**Required (all must pass):**
- [ ] Data quality audit passed (all thresholds met)
- [ ] ML model improvement delta > 5%
- [ ] Shadow mode ran for minimum 5 business days
- [ ] No SEV1/SEV2 incidents during shadow mode
- [ ] Planner satisfaction survey score ≥ 4/5
- [ ] All 10 services deployed and healthy
- [ ] P95 API response time < 2000ms under expected load
- [ ] Kafka consumer lag consistently < 1 minute
- [ ] Disaster recovery plan reviewed with tenant IT team
- [ ] Tenant admin user accounts provisioned and tested

**Recommended:**
- [ ] At least 3 planners trained on IPE Copilot
- [ ] Tenant-specific runbook documented
- [ ] SLA targets defined and documented

#### Day 26-28: Production Enablement
```bash
# Disable shadow mode - production recommendations begin
curl -X PATCH https://api.ipe.example.com/api/v1/admin/tenants/<TENANT_UUID> \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{"shadow_mode": false, "auto_resolve": false}'

# Enable automated resolution (gradually)
# Phase 1: Auto-resolve low-risk MOs (feasibility >= 90)
# Phase 2: Auto-resolve medium-risk MOs (feasibility >= 75)
# Phase 3: Full autonomy with planner override
```

## Post-Onboarding
- [ ] Schedule weekly performance review for first month
- [ ] Enable tenant-specific Grafana dashboards
- [ ] Configure alert notification channels (email, Slack)
- [ ] Hand off to account management team
- [ ] Schedule quarterly business review

## Troubleshooting

### Data Quality Failures
- **BOM Completeness < 80%**: Request tenant to complete BOM definitions in ERP
- **Lead Time Accuracy < 60%**: Request historical lead time data correction
- **Insufficient Historical Data**: Extend data collection period by 2 weeks

### Model Performance Issues
- **Improvement Delta < 0**: Check for data drift; retrain with larger dataset
- **High False Positive Rate in Alerts**: Adjust rule thresholds per tenant
- **Copilot Irrelevant Responses**: Add tenant-specific context to NLP prompts

### Infrastructure Issues
- **Slow API Response**: Scale service replicas or increase resource limits
- **Kafka Connection Errors**: Verify network policies and TLS certificates
- **Database Connection Pool Exhaustion**: Increase pool size or optimize queries
