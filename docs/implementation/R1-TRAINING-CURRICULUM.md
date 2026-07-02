# Training Curriculum — IPE Release 1

**Audience:** MENA mid-market discrete manufacturing (Odoo 17 customers)  
**Default language:** **Arabic for planners** · English optional for executives  
**Format:** Remote (Zoom/Teams) or on-site Cairo/Alexandria + factory visit day 2 optional  
**Materials:** Live staging environment · PDF quick-reference (Arabic) · WhatsApp group for post-training questions

---

## Curriculum overview

| Session | Role | Duration | Language | When |
|---------|------|----------|----------|------|
| **A — Planner** | Production planners, schedulers | **3 hours** | **Arabic** (primary) | Week 5, before UAT |
| **B — Manager** | Production manager, planning lead | **2 hours** | Arabic or bilingual | Week 5–6 |
| **C — Executive** | CEO, Operations Director | **45 min** | English or Arabic | Week 6, before go-live |

**Prerequisite for all sessions:** Staging sync complete; planner has login credentials; WhatsApp support group created.

---

## Session A — Production planner (Arabic-first)

**Goal:** Planner opens IPE **instead of Excel** every morning before the production meeting and completes the at-risk MO workflow in Arabic.

### A.1 Learning objectives

By end of session, planner can:

1. Log in with Arabic UI and navigate Control Tower  
2. Read feasibility score and interpret at-risk sorting  
3. Understand data quality badges and when to fix Odoo vs call support  
4. Open Resolution Center, compare scenarios, select recommendation  
5. Approve schedule and confirm Odoo dates updated  
6. Use WhatsApp to report sync issues with correct screenshot  

### A.2 Agenda (3 hours)

| Time | Topic | Activity | Materials |
|------|-------|----------|-----------|
| 0:00–0:20 | **Why IPE, not Excel** | Facilitator: daily pain (late MOs, manual copy from Odoo) | 1 slide — Arabic |
| 0:20–0:35 | **Login + Arabic UI** | Each planner logs in; toggle language once then **set Arabic** | `VITE_DEFAULT_LOCALE=ar` |
| 0:35–0:50 | **Sync status bar** | Read “آخر مزامنة Odoo”; green vs red; what to do if stale | Customer support guide §2 |
| 0:50–1:20 | **Control Tower queue** | Walk through: MO list, feasibility %, due date, “معالجة” button | Staging MOs |
| 1:20–1:35 | **Break** | | |
| 1:35–2:05 | **Data quality badges** | Live examples: MISSING_BOM, MISSING_ROUTING; fix in Odoo demo | DQ checklist §3 |
| 2:05–2:40 | **Resolution Center** | Pick at-risk MO → scenarios → trade-offs → select | 1 exercise MO |
| 2:40–3:00 | **Schedule approve + Odoo check** | Approve; switch to Odoo; verify `date_start`; SYNC_CONFLICT intro | 1 exercise MO |
| 3:00–3:15 | **WhatsApp escalation** | Role-play: “sync red at 6:45am” message template | Support guide §2 |
| 3:15–3:30 | **Q&A + daily checklist handout** | Each planner states tomorrow’s routine | Handout §A.4 |

### A.3 Hands-on exercises (staging)

| # | Exercise | Success criteria |
|---|----------|------------------|
| E1 | Find top 3 at-risk MOs | Correct sort by feasibility + due date |
| E2 | Explain unscorable MO | Identifies flag; states Odoo fix |
| E3 | Complete resolution flow | Scenario selected; approve clicked |
| E4 | Verify Odoo write-back | Dates match within 1 minute |
| E5 | Send practice WhatsApp alert | Screenshot + MO number + time |

### A.4 Planner daily checklist (handout — Arabic)

```text
قبل اجتماع الإنتاج (قبل 8:00):
☐ 1. افتح IPE — تأكد شريط المزامنة أخضر ("محدّث")
☐ 2. راجع قائمة مخاطر الأوامر — ركز على أقل نسبة جدوى
☐ 3. لكل أمر "لا يمكن التقييم" — سجّل السبب (Odoo أو WhatsApp)
☐ 4. عالج أهم 3 أوامر في مركز الحلول
☐ 5. اعتمد الجدول — تحقق من Odoo
☐ 6. فقط الأوامر غير القابلة للتقييم تبقى في Excel
```

### A.5 Assessment (trainer signs)

| Planner name | E1 | E2 | E3 | E4 | E5 | Ready for UAT? |
|--------------|----|----|----|----|----|----------------|
| | ☐ | ☐ | ☐ | ☐ | ☐ | ☐ |

---

## Session B — Production manager / planning lead

**Goal:** Manager governs adoption, approves high-impact schedule changes, and owns data quality remediation with IT.

### B.1 Learning objectives

1. Read team queue health: % scorable, open flags, sync reliability  
2. Apply approval guardrail: feasibility ≥85% before executive commit  
3. Prioritize data quality remediation using checklist §7  
4. Interpret executive OTD widget (trend, not single day)  
5. Know when to escalate P0 vs handle in Odoo  

### B.2 Agenda (2 hours)

| Time | Topic | Activity |
|------|-------|----------|
| 0:00–0:25 | **Control Tower — manager view** | Queue + filters; unscorable as KPI leak |
| 0:25–0:50 | **Data quality ownership** | RACI: planner vs IT vs Diligent; remediation plan template |
| 0:50–1:15 | **Resolution governance** | When planner decides vs manager approves; guardrail 85% |
| 1:15–1:35 | **Executive dashboard preview** | OTD baseline; week-over-week; export ROI CSV |
| 1:35–1:50 | **Support model** | WhatsApp group rules; P0 before 8am; no GitHub |
| 1:50–2:00 | **90-day adoption targets** | 4 days/week IPE-before-Excel; 2 saves/month |

### B.3 Manager weekly checklist

| Week | Action |
|------|--------|
| Monday pre-meeting | Confirm sync OK; review flag counts with planner |
| Wednesday | Check scorable % trend; unblock IT if routing gaps |
| Friday | Log “MOs saved from late” count for ROI |
| Monthly | Review OTD trend with executive |

---

## Session C — CEO / Operations Director (executive)

**Goal:** Executive understands ROI story in **5 business outcomes**, not feature list. Agrees to 90-day review and optional reference call.

### C.1 Learning objectives

1. Articulate why IPE complements (not replaces) Odoo  
2. Read OTD trend vs baseline in ≤2 minutes  
3. Know support is WhatsApp/phone — not IT ticket portal  
4. Commit to reference call metric if targets met  

### C.2 Agenda (45 minutes)

| Time | Topic | Key message |
|------|-------|-------------|
| 0:00–0:10 | **Problem** | Excel + Odoo = day-late visibility; crises in daily meeting |
| 0:10–0:20 | **Solution demo** | 3 clicks: at-risk MO → resolution → Odoo updated (live) |
| 0:20–0:30 | **ROI metrics** | OTD trend; planner adoption; MOs saved pre-late |
| 0:30–0:40 | **90-day contract** | Targets from SOW §6.2; review date: ________ |
| 0:40–0:45 | **Reference + renewal** | 1 reference call if satisfied; Year 2 renewal preview |

### C.3 Executive one-pager (leave-behind)

| Question | Answer |
|----------|--------|
| What did we buy? | Feasibility layer on Odoo — not another ERP |
| When is data fresh? | Every 15 min; red bar = call WhatsApp |
| What if it breaks at 7am? | P0 — 2h response; Excel fallback for unscored only |
| How do we measure success? | OTD up; planners use IPE 4+ days/week |
| What is NOT included? | AI chat, demand forecasting, SAP |

---

## Arabic-first UX standards (Release 1)

Trainers must verify these on **Session A**:

| Screen | Arabic requirement | Trainer check |
|--------|-------------------|---------------|
| Login | Labels in Arabic when locale=ar | ☐ |
| Sidebar nav | Planning hubs in Arabic | ☐ |
| Control Tower | Title, columns, sync bar, badges | ☐ |
| Resolution Center | Scenario labels (partial — note gaps) | ☐ |
| Alerts | Data quality toast in Arabic | ☐ |
| RTL layout | No clipped text on 1366×768 | ☐ |
| Language switcher | Planners know how to return to Arabic | ☐ |

**Known partial (R1):** Resolution Center and Login may have some English strings — log on WhatsApp; not a training blocker if core flow is Arabic.

---

## MENA discrete manufacturing context (trainer notes)

Use customer language — example: **electrical transformers**

| Concept | Odoo / IPE mapping | Training tip |
|---------|-------------------|--------------|
| Long lead times | MO horizon 4–12 weeks | Sort by due date + feasibility |
| Test bay bottleneck | Work center capacity | Show bottleneck in queue |
| Engineer-to-order BOM | Late BOM = unscorable | Process fix, not software |
| Daily morning meeting | Sync before 7am | Tie to P0 support SLA |
| Bilingual shop floor | Arabic UI, English SKUs OK | Product codes can stay Latin |
| Ramadan / Friday hours | Shorter WC capacity | Adjust Odoo calendars; mention in B session |

---

## Training completion sign-off

| Session | Date | Trainer (Diligent) | Attendees | Complete |
|---------|------|--------------------|-----------|----------|
| A — Planner | | | | ☐ |
| B — Manager | | | | ☐ |
| C — Executive | | | | ☐ |

**UAT training gate (SOW Exhibit B7):** Sessions A + B + C complete before UAT sign-off.

---

*Related: `R1-CUSTOMER-SOW-TEMPLATE.md` · `R1-DATA-QUALITY-ACCEPTANCE-CHECKLIST.md` · `R1-CUSTOMER-SUPPORT-GUIDE.md`*
