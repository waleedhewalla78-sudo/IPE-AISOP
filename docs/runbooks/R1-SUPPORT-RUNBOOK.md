# Release 1 Support Runbook — Star Trans / MENA Customers

**Audience:** Diligent support engineers (internal)  
**Customer-facing guide:** `docs/runbooks/R1-CUSTOMER-SUPPORT-GUIDE.md` (WhatsApp, 7am sync, non-engineers)

**Channel:** WhatsApp group + phone, business hours (Sun–Thu 8am–6pm Cairo)  
**SLA:** Same-day response; critical sync failure before production meeting = 2-hour target

---

## 1. Contact model

| Tier | Contact | When |
|------|---------|------|
| L1 | Named Diligent engineer (WhatsApp) | First contact — always |
| L2 | Engineering lead | Sync down >2 hours, data corruption suspected |
| L3 | Waleed / founder | Customer escalation, contract dispute |

**Do not** ask customers to open GitHub issues.

---

## 2. Symptom: Sync failed / "Last synced" stale

### Planner sees

- Control Tower sync bar red or timestamp >30 min old
- No new MOs from yesterday's Odoo orders

### Diagnosis

```powershell
# On IPE VM
docker compose -f infrastructure/docker/docker-compose.release1.yml ps
docker compose -f infrastructure/docker/docker-compose.release1.yml logs connector --tail 100
```

Check `cdm_sync_run` latest row:

```sql
SELECT started_at, finished_at, status, entity_counts, error_summary
FROM cdm_sync_run
WHERE tenant_id = '<tenant-uuid>'
ORDER BY started_at DESC LIMIT 5;
```

### Common causes

| Cause | Fix |
|-------|-----|
| Odoo credentials expired | Update tenant config; test `POST /api/v1/sync/run` |
| Odoo server down | Customer restarts Odoo; confirm URL reachable |
| Network/firewall | Allow Odoo server → IPE :8000 or IPE → Odoo :8069 |
| Mapper error on custom field | Log issue; patch mapper; manual sync |
| IPE connector container down | `docker compose up -d connector` |

### Customer message template (Arabic/English)

> We're aware the sync didn't complete at [time]. We're investigating and will update you before [time+2h]. Your last successful sync was at [timestamp] — data shown is from that point.

---

## 3. Symptom: MO shows "Cannot score — MISSING_BOM"

### Not a platform bug

Odoo MO lacks BOM or routing. Customer fixes in Odoo:

1. Open MO in Odoo → check BOM linked
2. Verify routing operations exist
3. Wait next sync (15 min) or trigger manual sync

---

## 4. Symptom: Schedule approved but Odoo dates unchanged

### Diagnosis

1. Check cap-svc logs for `ERP_ACTIVATE` 
2. Verify `erp_mo_id` on MO in IPE
3. Test activate: `POST /api/v1/sync/odoo/activate` with MO ids

### Common causes

| Cause | Fix |
|-------|-----|
| Missing `erp_mo_id` | Re-sync MOs from Odoo |
| Odoo user lacks MRP write permission | Fix service account ACLs |
| Material reservation conflict | Odoo UserError — planner adjusts in Odoo |

---

## 5. Symptom: Login failure

1. Confirm Kong + dpe-svc healthy
2. Reset password via admin SQL (staging only) or re-seed user
3. Check JWT secret unchanged across restart

---

## 6. Symptom: Arabic layout broken

1. Clear browser cache
2. Toggle language EN → AR
3. Report specific screen to engineering (screenshot via WhatsApp)

---

## 7. Escalation matrix

| Severity | Definition | Response |
|----------|------------|----------|
| P0 | Production meeting in <2h, no data | 2h fix or rollback + Excel fallback communicated |
| P1 | Sync down >4h business hours | Same day |
| P2 | Single MO wrong score | Next business day |
| P3 | UI cosmetic | Next release |

---

## 8. Rollback procedure

1. Stop connector scheduler (prevent bad writes to Odoo)
2. Restore DB snapshot if corruption (pre-go-live snapshot required)
3. Customer continues on Odoo native until fix deployed
4. Post-incident: update this runbook

---

## 9. Weekly health check (proactive)

Every Monday before customer production meeting:

- [ ] Last sync success within 24h
- [ ] `release1-smoke.ps1` PASS on staging mirror
- [ ] Disk >20% free on IPE VM
- [ ] Export ROI CSV sent to executive sponsor
