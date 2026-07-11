# عملية قياس خط الأساس للتسليم في الموعد
# OTD Baseline Capture Process

**Document:** IPE-IMPL-OTD-BASELINE-v1  
**Date:** 2026-07-11  
**Purpose:** Capture the customer's on-time delivery percentage **before** IPE deployment. This baseline is compared at Day 30 to demonstrate ROI.

---

## Purpose

OTD % = (Manufacturing Orders finished on or before deadline) ÷ (Total completed MOs) × 100

Capture 6 months of history where possible. Record method, date, and who captured it.

---

## Method 1: SQL Query Against Odoo Database (Fastest)

Run against the customer's Odoo PostgreSQL database (read-only recommended):

```sql
SELECT
    DATE_TRUNC('month', date_finished) AS month,
    COUNT(*) AS total_completed,
    COUNT(*) FILTER (WHERE date_finished <= date_deadline) AS on_time,
    ROUND(
        COUNT(*) FILTER (WHERE date_finished <= date_deadline)::numeric
        / NULLIF(COUNT(*), 0)::numeric * 100, 1
    ) AS otd_pct
FROM mrp_production
WHERE state = 'done'
  AND date_finished >= NOW() - INTERVAL '6 months'
GROUP BY 1
ORDER BY 1;
```

**Odoo 17 note:** If `date_finished` / `date_deadline` are missing, try:

```sql
-- Odoo 17 alternate column names
SELECT
    DATE_TRUNC('month', date_finished) AS month,
    COUNT(*) AS total_completed,
    COUNT(*) FILTER (WHERE date_finished <= date_planned_finished) AS on_time,
    ROUND(
        COUNT(*) FILTER (WHERE date_finished <= date_planned_finished)::numeric
        / NULLIF(COUNT(*), 0)::numeric * 100, 1
    ) AS otd_pct
FROM mrp_production
WHERE state = 'done'
  AND date_finished IS NOT NULL
  AND date_finished >= NOW() - INTERVAL '6 months'
GROUP BY 1
ORDER BY 1;
```

---

## Method 2: IPE OTD Baseline API (After Deployment)

After IPE is deployed and historical MOs have been synced (or OTD snapshots exist via FR-R1-16 / `cdm_otd_snapshot`):

```bash
# Obtain JWT first (local auth)
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ipe.local","password":"admin"}' | jq -r .access_token)

curl -X POST http://localhost:8001/api/v1/analytics/otd/baseline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: <tenant-uuid>" \
  -d '{"months_back": 6}'
```

**Script alternative:** `scripts/otd-baseline-capture.py` — queries Odoo via XML-RPC and writes JSON + markdown table.

```powershell
python scripts/otd-baseline-capture.py `
  --odoo-url http://odoo-host:8069 `
  --db star_trans `
  --user api_user `
  --password <secret> `
  --months 6 `
  --out docs/customer/star-trans/otd-baseline-YYYY-MM-DD.md
```

---

## Method 3: Manual from Odoo Export

For customers who do not allow direct SQL or API access:

1. Odoo → Manufacturing → Manufacturing Orders  
2. Filter: State = Done; Finished Date = last 6 months  
3. Export to CSV: MO number, product, planned date / deadline, actual finish date  
4. In Excel: `On Time = IF(Actual <= Planned, 1, 0)`  
5. `OTD % = SUM(On Time) / COUNT(*) × 100`  
6. Optionally pivot by month for the recording template below

---

## Recording Template

| Month | Total MOs Completed | On-Time | Late | OTD % |
|-------|---------------------|---------|------|-------|
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| | | | | |
| **Overall** | | | | **%** |

**Captured by:** _______________  
**Date:** _______________  
**Method used:** SQL / API / Manual  
**Data source:** _______________ (Odoo DB name / export file)  
**Customer:** Star Trans  
**Notes:** _______________

---

## Day-30 Comparison

| Metric | Pre-IPE Baseline | Day 30 | Delta |
|--------|------------------|--------|-------|
| Overall OTD % | | | |
| Late MO count (rolling 30d) | | | |

Store the signed baseline with the customer implementation record before go-live.
