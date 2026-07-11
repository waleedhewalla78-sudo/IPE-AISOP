# IPE Implementation Playbook v1

**Version:** 1.0  
**Date:** 2026-07-11  
**Scope:** Full customer engagement lifecycle — from SOW signature to 30-day monitoring  
**Audience:** Diligent implementation manager (or Waleed on first deployments)  
**Source documents:** `deploy/star-trans/DEPLOY-RUNBOOK.md`, `docs/implementation/R1-TRAINING-CURRICULUM.md`, `docs/runbooks/R1-CUSTOMER-SUPPORT-GUIDE.md`

> This playbook is self-contained. A consultant who has not deployed IPE before should be able to follow it without asking Waleed for help. Decisions that require judgement are documented inline.

---

## Pre-Engagement Checklist

Complete before scheduling Day 1. Nothing starts until all items are checked.

```
COMMERCIAL
[ ] SOW signed by both parties (authorized signatures, not drafts)
[ ] Implementation fee first 50% invoiced and payment confirmed (or credit approved)
[ ] WhatsApp support group created: "IPE — [Customer Name] Support"
[ ] Customer added to group: planner contact, IT contact, Operations Director
[ ] Diligent added to group: Waleed, implementation manager

ODOO ACCESS (from customer IT)
[ ] Odoo staging URL confirmed: http://[HOST]:8069
[ ] Odoo production URL confirmed
[ ] Database name confirmed
[ ] API service account username and password received
[ ] Permissions verified: read mrp/sale/purchase/stock; write mrp.production
[ ] Odoo version confirmed: 17 or 19

SERVER (from customer IT)
[ ] Server provisioned: 8GB RAM, 4 vCPU, 100GB SSD minimum
[ ] OS: Ubuntu 22.04 LTS or Windows Server 2022
[ ] Docker 24+ and Docker Compose v2 installed on server
[ ] SSH or RDP access to server provided to Diligent implementation manager
[ ] Network path from IPE server to Odoo server on port 8069 confirmed (telnet test)

PEOPLE
[ ] Planner champion identified: name, Arabic speaker (Y/N), availability for Weeks 2-3
[ ] Operations Director identified: name, availability for UAT Session 2 (Day 12, 1 hour)
[ ] Executive sponsor confirmed for go-live sign-off (Day 20)
[ ] Customer IT contact available Week 1 for data quality resolution

DEPLOYMENT PACKAGE
[ ] deploy/star-trans/ directory transferred to customer server (or accessible via network share)
[ ] .env.template reviewed; all variables understood
[ ] star-trans-validate.ps1 on customer server
```

---

## Week 1: Deployment and First Sync (Days 1–5)

### Day 1–2: Environment Setup

**Goal:** All services healthy, no errors, web UI accessible.

**Step 1: Copy deployment files**
```powershell
# On customer server — copy deployment package
# If transferred via file share:
Copy-Item -Recurse deploy\star-trans\ C:\ipe-deploy\
cd C:\ipe-deploy

# Or via SCP from development machine:
# scp -r deploy/star-trans/ user@server:/opt/ipe-deploy/
```

**Step 2: Configure environment**
```powershell
# Copy template and edit
Copy-Item .env.template .env
notepad .env  # or nano .env on Linux

# Required variables — every blank value is a blocker:
# IPE_DATABASE_URL=postgresql+asyncpg://ipe:CHANGEME@db:5432/ipe
# IPE_REDIS_URL=redis://redis:6380/0
# IPE_JWT_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
# ODOO_URL=http://[CUSTOMER_ODOO_HOST]:8069
# ODOO_DB=[DATABASE_NAME]
# ODOO_USERNAME=[SERVICE_ACCOUNT_USERNAME]
# ODOO_PASSWORD=[SERVICE_ACCOUNT_PASSWORD]
# VITE_RELEASE_PROFILE=r1  # activates R1 feature set + Arabic
```

**Step 3: Start services**
```powershell
docker compose up -d
# Wait 30 seconds for services to initialize
Start-Sleep 30
docker compose ps  # all services should show "Up" or "Up (healthy)"
```

**Step 4: Run database migrations**
```powershell
docker compose exec dpe-svc uv run alembic upgrade head
# Expected output: "INFO  [alembic.runtime.migration] Running upgrade ..."
# Last line should be: "INFO  [alembic.runtime.migration] Running upgrade [prev] -> [head]"
```

**Step 5: Verify deployment**
```powershell
.\scripts\star-trans-validate.ps1
# Expected: all PASS. If any FAIL, resolve before proceeding to Day 3.
```

**Common Day 1–2 issues:**

| Symptom | Cause | Resolution |
|---|---|---|
| Service exits immediately | `.env` missing required variable | Run `docker compose logs [service-name]` to identify missing var |
| Migration fails "no table" | Database connection string wrong | Check `IPE_DATABASE_URL` — host, port, password |
| Web UI 502 Bad Gateway | Kong not yet ready | Wait 60 seconds; run `docker compose restart kong` |
| Container OOM killed | Server RAM < 8GB | Cannot proceed; customer must upgrade server |

---

### Day 3–4: First Sync and Data Quality Review

**Goal:** First successful full sync; data quality flags documented; planner can see their MOs.

**Step 1: Trigger first sync**

Via API:
```powershell
$headers = @{"X-Tenant-ID" = "00000000-0000-0000-0000-000000000001"}
Invoke-RestMethod -Uri "http://localhost:8009/api/v1/sync/run" -Method POST -Headers $headers
# Wait 2-5 minutes for sync to complete
```

Or via web UI: Settings → Sync → Run Full Sync Now

**Step 2: Check sync results**
```powershell
# Check sync_run table
docker compose exec -T db psql -U ipe -c "SELECT id, status, entity_counts, error_summary, finished_at FROM cdm_sync_run ORDER BY created_at DESC LIMIT 3;"

# Expected: status='success' or 'partial'. 'failed' means a blocker — check error_summary.
```

**Step 3: Review entity counts**

A healthy first sync typically shows:
- `products`: 50–500 synced
- `work_centers`: 3–20 synced
- `boms`: 20–200 synced
- `manufacturing_orders`: 10–200 synced (only confirmed/in_progress)
- `demands`: 20–500 synced (only confirmed/done sale order lines)

If any critical entity count is 0, this is a data or permission issue — see table below.

| Entity count is 0 | Likely cause |
|---|---|
| `products = 0` | API user lacks product read access; or all products are archived |
| `work_centers = 0` | No active `mrp.workcenter` records; or `mrp` module not active |
| `boms = 0` | No active BOMs; or BOM module (`mrp`) not configured |
| `manufacturing_orders = 0` | All MOs in draft or cancelled; or no `mrp.production` records |
| `demands = 0` | No confirmed sales orders; or `sale` module missing |

**Step 4: Review data quality flags**
```powershell
docker compose exec -T db psql -U ipe -c "SELECT flag_code, COUNT(*) FROM cdm_data_quality_flag WHERE resolved_at IS NULL GROUP BY flag_code ORDER BY COUNT(*) DESC;"
```

Document each flag type in the DQ review table:

| Flag Code | Count | Meaning | Customer Action Required |
|---|---|---|---|
| `MISSING_BOM` | N | MO product has no active BOM | Customer IT: create BOM in Odoo Manufacturing |
| `MISSING_ROUTING` | N | BOM exists but has no routing operations | Customer IT: add routing steps to BOM |
| `MISSING_WC` | N | BOM references a work centre not synced | Customer IT: verify work centre is active and has `mrp` access |
| `SYNC_CONFLICT` | N | Odoo dates changed after IPE approved | Planner: reconcile in Resolution Center |

**Target:** ≥60% of active MOs scorable after Day 3. If below 40%, escalate to data quality resolution before proceeding to Day 5.

---

### Day 5: Initial Planner Review

**Goal:** Planner confirms their data looks correct; field mapping issues documented.

**Script (for implementation manager to follow with planner):**

1. "Open the browser and go to `http://[SERVER]:8082`"
2. "Log in with the planner account we created"
3. "Switch language to Arabic — click the language selector in the top right"
4. "Look at the Control Tower — do you recognise these manufacturing orders?"
5. "Do the product names match what you see in Odoo?"
6. "Do the quantities look right?"
7. "Are there any orders you expected to see that are missing?"

**Document answers:**
- [ ] Planner confirms product names are correct
- [ ] Planner confirms quantities match Odoo
- [ ] Missing MOs noted (check their state in Odoo — must be confirmed or in_progress)
- [ ] Field mapping issues noted for Week 2 resolution
- [ ] Arabic language toggle confirmed working
- [ ] D1 and D2 acceptance reviewed with planner

---

## Week 2: Calibration and Arabic QA (Days 6–10)

### Day 6–7: Data Quality Resolution

**Goal:** Reduce `MISSING_BOM`, `MISSING_ROUTING`, `MISSING_WC` flags to near zero; scorable MO% reaches ≥70%.

**Process:**
1. Share DQ flag report with customer IT contact (export from `cdm_data_quality_flag` table or from Data Quality screen in admin UI)
2. Customer IT corrects data in Odoo (add BOMs, add routing operations, activate work centres)
3. Trigger re-sync after each batch of fixes: `POST /api/v1/sync/run`
4. Re-run flag query to verify improvement

**Escalation decision:** If customer IT cannot fix Odoo data issues within 2 days, Diligent implementation manager assesses whether:
- Issue is a data entry gap (customer can fix with guidance) → continue with support
- Issue is a structural Odoo configuration problem (missing module, missing custom field) → may require Odoo consultant involvement; document in risk log

---

### Day 8–9: Arabic QA

**Goal:** Full planner workflow functions correctly in Arabic with RTL layout.

**Test script (run with planner in Arabic mode):**

| Step | Action | Expected Result | Pass/Fail |
|---|---|---|---|
| 1 | Open Control Tower in Arabic | All column headers, KPI tile labels, and button text in Arabic; RTL layout | |
| 2 | Click on an at-risk MO | Resolution Center opens; scenario cards fully in Arabic | |
| 3 | Compare two scenarios | Cost and delivery impact text in Arabic; numbers in Western numerals | |
| 4 | Open Schedule view | Gantt labels in Arabic; approve button in Arabic | |
| 5 | Check OTD Dashboard | Dashboard title and metric labels in Arabic | |
| 6 | Toggle back to English | Switches correctly; no broken layouts | |

**Log issues:** Note screen name, description of problem, screenshot. Classify as P0 (blocks workflow) or P2 (cosmetic). Fix P0 issues same-day; P2 in post-go-live period.

---

### Day 10: Pre-UAT Verification

**Goal:** System is stable and ready for formal UAT sessions.

**Checklist:**
```
[ ] 5+ consecutive scheduled syncs completed successfully (check cdm_sync_run)
[ ] Sync conflict detection works: change MO date in Odoo; verify SYNC_CONFLICT flag appears in IPE after next sync
[ ] Write-back test (staging data): approve a schedule in IPE; verify mrp.production date_start updated in Odoo; verify chatter note added
[ ] Arabic QA pass: ≥90% of UI text correct in Arabic; no RTL layout breaks
[ ] Scorable MO%: ≥70% of active MOs have a feasibility score
[ ] UAT session schedule confirmed: planner (Day 11), Ops Director (Day 12), planner + IT (Day 13)
[ ] Training materials ready: R1-TRAINING-CURRICULUM.md printed or on screen
[ ] D3, D4, D5 acceptance signed or confirmed
```

---

## Week 3: UAT and Training (Days 11–15)

### Day 11: UAT Session 1 — Planner Workflow (2 hours)

**Attendees:** Planner champion, Diligent implementation manager  
**Language:** Arabic  
**Location:** Customer site or video call with screen share

**Agenda:**

| Time | Activity | Acceptance Criterion |
|---|---|---|
| 0:00–0:15 | Setup and login | Planner logs in independently |
| 0:15–0:45 | Control Tower: identify at-risk MOs | Planner can identify ≥2 at-risk MOs and explain why they are at risk |
| 0:45–1:15 | Resolution Center: compare and select scenario | Planner can compare 2 scenarios and select one based on cost vs. delivery trade-off |
| 1:15–1:45 | Schedule: approve and verify | Planner approves schedule; verifies Odoo dates updated; sees chatter note |
| 1:45–2:00 | Q&A and issue log | All P0 issues logged |

**Pass/fail decision:** Planner completes the full flow without instructor driving the mouse.

---

### Day 12: UAT Session 2 — Executive Dashboard (1 hour)

**Attendees:** Operations Director, Diligent implementation manager  
**Language:** Arabic preferred; English acceptable if Ops Director prefers

| Time | Activity | Acceptance Criterion |
|---|---|---|
| 0:00–0:10 | Login and overview | Ops Director logs in with executive account |
| 0:10–0:35 | OTD Dashboard: trend, root causes, cost-of-chaos | Ops Director can identify top delay cause and total revenue at risk |
| 0:35–0:55 | What-to-ask-the-planner scenarios | Ops Director understands how to use IPE data in weekly management meetings |
| 0:55–1:00 | Sign-off and questions | Ops Director verbally confirms the dashboard is useful |

**Pass/fail:** Ops Director finds the dashboard useful and actionable. "I would look at this every Monday morning" is a pass.

---

### Day 13: UAT Session 3 — Write-Back and Edge Cases (1 hour)

**Attendees:** Planner, IT contact, Diligent implementation manager

| Test | Steps | Expected Result | Pass/Fail |
|---|---|---|---|
| Write-back end-to-end | Approve schedule in IPE → check Odoo MO | `date_start` updated; chatter note present | |
| Odoo unreachable | Stop Odoo temporarily → wait for sync → check IPE | Sync shows "partial"; error logged; previous data still visible; no crash | |
| MO deleted in Odoo | Delete test MO in Odoo → trigger sync | IPE flags MO as SYNC_CONFLICT or marks as archived; does not crash | |
| Conflict detection | Change date in Odoo after IPE approves | Next sync shows `SYNC_CONFLICT` flag on that MO | |

---

### Day 14: Training Session (4 hours)

**Follow:** `docs/implementation/R1-TRAINING-CURRICULUM.md`  
**Attendees:** Planner champion; optionally manager / Operations Director for Block 4

**Trainer checklist before session:**
- [ ] Training environment has fresh Odoo data (triggered sync this morning)
- [ ] At least 3 at-risk MOs visible in Control Tower
- [ ] Resolution scenarios generated for at-risk MOs
- [ ] Planner has their own login credentials
- [ ] Arabic quick-reference card printed (1 copy per planner)

**Post-training verification:**
- [ ] Planner completes TC-06 style flow without assistance
- [ ] Planner knows where to find the DQ flag explanation
- [ ] Planner knows how to read sync status bar
- [ ] Planner knows the WhatsApp escalation procedure
- [ ] Training attendance form signed

---

### Day 15: UAT Sign-Off

**Goal:** All UAT P0 issues resolved; formal sign-off obtained.

**Process:**
1. Review UAT issue log with planner and IT contact
2. Confirm all P0 issues are resolved (not just logged)
3. Walk through D1–D7 acceptance checklist with planner
4. Obtain planner signature on UAT acceptance form (template in Appendix B)
5. Obtain Operations Director signature on UAT acceptance form
6. Confirm go-live date: **Day 16 = tomorrow**
7. Create production deployment checklist for Day 16

**If P0 issues remain:** Do NOT proceed to go-live. Fix P0, then re-run affected UAT session. Notify Waleed if delay exceeds 3 days.

---

## Week 4: Go-Live and Baseline (Days 16–20)

### Day 16: Production Go-Live

**Morning checklist (before 7:30am if planner has early morning meeting):**
```
[ ] Star-trans-validate.ps1 run: all PASS
[ ] Sync triggered manually at 6:30am; sync_run shows success
[ ] Planner logged in and seeing today's MOs
[ ] Diligent implementation manager on WhatsApp standby from 7:00am
[ ] "IPE is live — first production triage" message sent to Ops Director
```

**First production triage (with planner, 30–45 minutes):**
- Planner identifies top 3 at-risk MOs by financial impact
- For each: opens Resolution Center, selects appropriate scenario, approves if suitable
- Diligent observes but does not drive
- Document first day metrics: MOs scored, at-risk count, scenarios viewed

---

### Day 17–19: Intensive Support

**Daily routine:**
1. 8:00am — Send WhatsApp check-in: "Good morning [name] — IPE running well? Any issues from yesterday?"
2. Review `cdm_sync_run` for last 24 hours — flag any failures
3. Check `cdm_data_quality_flag` for new flags
4. Log daily: login count, MOs scored, scenarios approved
5. Resolve any P1 issues immediately

**Escalation trigger:** If planner stops using IPE 2 days in a row during Days 17–19, call Waleed. This is a red flag for adoption risk.

---

### Day 20: OTD Baseline and First Invoice

**OTD baseline capture:**
```powershell
# Run OTD baseline query on Odoo historical data
$headers = @{"X-Tenant-ID" = "00000000-0000-0000-0000-000000000001"}
Invoke-RestMethod -Uri "http://localhost:8001/api/v1/otd/baseline" -Method GET -Headers $headers

# Alternatively, export from Odoo:
# Sales → Orders → Delivered Orders (last 90 days) → export CSV → calculate % delivered on or before promised date
```

**Document:**
- Pre-IPE OTD baseline: _____%  (last 3–6 months from Odoo data)
- Measurement date: Day 20 (go-live + 4 days)
- Signed by Operations Director
- Target for Day 50 measurement: baseline + ≥15%

**Issue first invoice:**
- 50% implementation fee (second tranche — go-live milestone)
- Annual platform licence (first year, invoiced at go-live)
- Net 30 payment terms

---

## Post-Go-Live: 30-Day Monitoring (Days 21–50)

### Weekly Cadence

| Day | Activity |
|---|---|
| 21, 28, 35, 42 | Planner check-in (15 min WhatsApp): adoption metrics, open issues |
| 21, 28, 35, 42 | Sync health review: check `cdm_sync_run` for last 7 days; flag any ≥2 failures |
| 28 | Mid-point satisfaction pulse: "On a scale of 1–10, how useful is IPE this week?" |
| 35 | Review open P2 issues; resolve any that are 2+ weeks old |
| 50 | **Day 30 measurement** |

### Day 50: 30-Day Measurement and ROI

**OTD measurement:**
- Run OTD query for last 30 days (same method as baseline capture)
- Compare to baseline captured on Day 20
- Document: before, after, change, % improvement

**Satisfaction interview (30 minutes, CEO + Ops Director):**
1. "On a scale of 1–10, how satisfied are you with IPE?" (target ≥7)
2. "What's working well?"
3. "What would make it better?"
4. "Would you recommend IPE to another manufacturing company in Egypt?" (target: yes)

**If satisfaction <7:** Escalate to Waleed. Hold a structured problem-solving session before asking for a reference or renewal.

**ROI case study initiation (if satisfaction ≥7):**
- OTD improvement documented
- Time saved per planner per week documented
- Cost-of-chaos reduction estimated
- Begin drafting case study with Ops Director

---

## Appendix A: Common Issues and Resolutions

| Issue | Symptom | Resolution Steps |
|---|---|---|
| **Sync failure** | Sync bar red; last sync >30 min ago | 1. Check `docker compose ps` — all services Up?; 2. Check `docker compose logs connector`; 3. Check Odoo is reachable: `curl http://[ODOO]:8069/web/healthz`; 4. `docker compose restart connector`; 5. Trigger manual sync |
| **All MOs score 0%** | Every MO shows 0 feasibility | Check `cdm_data_quality_flag` — likely `MISSING_BOM` or `MISSING_ROUTING` on all MOs; fix in Odoo |
| **All MOs score 100%** | Every MO shows 100% feasibility | Check work centre definitions in Odoo — if capacity is not set, all capacity gates pass trivially; verify `cdm_work_center` records have non-zero `capacity_hours_per_day` |
| **Arabic broken** | UI reverts to English or shows garbled text | Hard refresh (Ctrl+F5); verify `VITE_RELEASE_PROFILE=r1` in `.env`; check `ar.json` key count ≥250 via validate script |
| **Write-back fails** | IPE shows approval success but Odoo dates unchanged | Check API user has write access to `mrp.production`; check `docker compose logs connector` for 403 errors |
| **Slow Control Tower** | Page takes >10 seconds to load | Check active MO count: `SELECT COUNT(*) FROM cdm_manufacturing_order WHERE status NOT IN ('completed','cancelled');` — if >500, consider pagination setting; check DB indexes |
| **Login broken** | All users get 401 or blank page | Check `IPE_JWT_SECRET_KEY` in `.env` has not changed; `docker compose restart` all services |
| **Container out of memory** | Services restart randomly | Run `docker stats`; if any container >3GB RAM, server RAM is insufficient; escalate |

---

## Appendix B: Customer Sign-Off Template

### UAT Acceptance Form — IPE Release 1

**Customer:** Star Trans  
**Date:** _______________  
**Deployment environment:** Staging / Production (circle one)

| # | Deliverable | Tested? | Accepted? | Issues Noted |
|---|---|---|---|---|
| D1 | Platform deployed, all services healthy | Y / N | Y / N | |
| D2 | Odoo connector syncing, MOs visible | Y / N | Y / N | |
| D3 | Data quality review complete | Y / N | Y / N | |
| D4 | Feasibility scores validated | Y / N | Y / N | |
| D5 | Arabic UI verified | Y / N | Y / N | |
| D6 | UAT sessions completed (3 sessions) | Y / N | Y / N | |
| D7 | Training delivered | Y / N | Y / N | |

**Outstanding P0 issues:** None / (list)  
**Outstanding P1/P2 issues (acceptable for go-live):** (list)

**Planner champion:**  
Name: _______________ Signature: _______________ Date: _______________

**Operations Director:**  
Name: _______________ Signature: _______________ Date: _______________

**Diligent Implementation Manager:**  
Name: Waleed Hewalla Signature: _______________ Date: _______________
