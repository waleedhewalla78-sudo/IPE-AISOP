# R1 Training Curriculum — Star Trans / Release 1

**Version:** 2.0 (Sprint 2 update — 2026-07-11)  
**Duration:** 4 hours (including break)  
**Audience:** Planner champion (primary); optional manager / executive observers  
**Prerequisites:** IPE deployed; Odoo staging synced; trainee accounts created; Arabic UI verified  
**Last updated:** 2026-07-11  
**Route verification:** All screen names below match current R1 UI routes (`/control-tower`, `/resolution`, `/schedule`, `/otd`, `/settings`)

---

## Agenda

| Block | Duration | Topic | Route |
|-------|----------|--------|-------|
| 1 | **30 min** | Login, navigation, and product overview | `/` → `/control-tower` |
| 2 | **45 min** | Control Tower: reading and triaging the risk queue | `/control-tower` |
| 3 | **45 min** | Resolution Center: comparing scenarios | `/resolution/[mo-id]` |
| — | **15 min** | Break | — |
| 4 | **30 min** | Schedule: approving and verifying write-back | `/schedule` |
| 5 | **30 min** | OTD Dashboard: reading on-time delivery metrics | `/otd` |
| 6 | **15 min** | Arabic language toggle and RTL navigation | All screens |
| 7 | **15 min** | Common questions, troubleshooting, and escalation | — |
| — | **15 min** | Buffer / recap / quick-reference card handout | — |

**Total:** ~4 hours (3h 45min structured + 15min buffer)

---

## Block 1 — Login, Navigation, and Product Overview (30 min)

**Objectives:** Planner understands what IPE Release 1 does, what it does not do, and can navigate the UI independently.

### 1.1 What IPE Does (10 min)

| Topic | Key Points |
|-------|------------|
| The problem | MOs are planned in Odoo; infeasibility is discovered on the floor; planner uses Excel as backup |
| IPE role | Scores every active MO for feasibility BEFORE the shift; surfaces risk with resolution options; approves schedule back to Odoo |
| Architecture (simple) | Browser → IPE → Odoo (reads every 15 min; writes on approval) |
| Roles | Planner (daily user), Operations Director (weekly OTD review), Admin (Diligent only) |
| **Out of scope (R1)** | AI Copilot, demand sensing, scenario workbench, S&OP (future upgrade) |

### 1.2 Login (5 min)

**URL:** `http://[CUSTOMER-SERVER]:8082`  
**Auth:** Local JWT — username and password set during deployment  
**Arabic toggle:** Click language selector (globe icon, top right) → select العربية  
**Note:** Password reset requests go to Diligent via WhatsApp (customer does not have direct DB access)

**Trainer action:** Log in as the planner trainee account. Switch to Arabic. Confirm RTL layout activates.

### 1.3 Navigation (10 min)

| Menu Item (Arabic) | Menu Item (English) | Route | What It Shows |
|---|---|---|---|
| برج التحكم | Control Tower | `/control-tower` | All active MOs with feasibility scores; risk queue |
| مركز الحلول | Resolution Center | `/resolution/[mo-id]` | Scenario cards for a specific at-risk MO |
| الجدولة | Schedule | `/schedule` | Gantt chart; approve button |
| لوحة OTD | OTD Dashboard | `/otd` | On-time delivery trend and root cause breakdown |
| الإعدادات | Settings | `/settings` | Sync status; admin only |

**Demo:** Open Control Tower. Point out: (1) KPI tiles at top, (2) risk queue, (3) sync status bar at bottom.

### 1.4 Mini-exercise (5 min)

Planner closes the browser and re-opens it. Logs in independently. Switches to Arabic. Navigates to Control Tower. **Pass criterion:** Planner does this without assistance.

---

## Block 2 — Control Tower: Reading and Triaging the Risk Queue (45 min)

**Objectives:** Planner can identify at-risk MOs, understand the feasibility score, and prioritise using financial impact.

### 2.1 Understanding the Score (15 min)

| Concept | Explanation |
|---|---|
| Feasibility score | 0–100%. Score = percentage of constraint gates passing. 5 gates × 20% each. |
| Risk tiers | ≥80% = Green (low risk); 50–79% = Yellow (monitor); <50% = Red (at-risk, action needed) |
| Sort order | Default: financial impact descending (revenue at risk + delay cost) |
| Gate badges | Each at-risk MO shows which gates failed (material, capacity, BOM, demand, delivery) |
| "Cannot score" | DQ flag present — data issue in Odoo; Diligent or customer IT must resolve |

**Arabic terms:**
- درجة الجدوى = Feasibility score
- قيد المواد = Material constraint
- قيد الطاقة = Capacity constraint
- قائمة المواد مفقودة = Missing BOM
- لا يمكن التقييم = Cannot score

### 2.2 Reading an MO Row (10 min)

**Walk through one at-risk MO row:**
1. MO name (links to Odoo if clicked)
2. Product name (Arabic if product names are in Arabic in Odoo)
3. Quantity and unit
4. Planned start / planned end dates
5. Feasibility score + failed gates
6. Revenue at risk (from linked sale order)
7. "Open in Resolution Center" button

### 2.3 Filtering and Sorting (10 min)

| Filter | How to Use | When to Use |
|---|---|---|
| At-risk only | Toggle "At Risk" filter button | Daily triage — focus on reds and yellows |
| By gate | Click gate badge at top | "Show me all MOs failing capacity" |
| By product | Search box | "All transformer core orders" |
| By date | Date range picker | "This week's production" |

### 2.4 Sync Status Bar (10 min)

| Status | Colour | Meaning | Action |
|---|---|---|---|
| Last synced 5 min ago | Green | Normal | None |
| Last synced 20–30 min ago | Yellow | Sync may be running | Wait 5 minutes |
| Last synced >30 min ago | Red | Sync failed or stalled | P0: WhatsApp Diligent immediately |
| تأخر المزامنة | Red Arabic text | Sync delayed | Same as above |

**Trainer action:** Show the sync status bar. Point out the last sync time. Explain that this is how the planner knows data is fresh.

---

## Block 3 — Resolution Center: Comparing Scenarios (45 min)

**Objectives:** Planner can open a resolution, compare scenarios, select the best option, and understand the cost/delivery trade-off.

### 3.1 Opening Resolution Center (5 min)

**From Control Tower:** Click "Open Resolution" on an at-risk MO, or click the MO name → Resolution Center opens at `/resolution/[mo-id]`.

**Screen layout:**
- Left panel: MO details (product, quantity, current dates, failing gates)
- Center: Scenario cards (2–3 cards side by side)
- Right panel: Cost impact summary (optional — may be collapsed on smaller screens)

### 3.2 Understanding a Scenario Card (15 min)

Each scenario card shows:

| Field | Arabic Label | Meaning |
|---|---|---|
| Scenario title | عنوان السيناريو | Brief description (e.g., "إعادة جدولة لنافذة الطاقة التالية") |
| New delivery date | تاريخ التسليم المقترح | Estimated completion date under this scenario |
| Delivery impact | أثر التسليم | Days early (green) or days late (red) vs. original commitment |
| Cost impact | الأثر المالي | Extra cost in USD/EGP (overtime, expedite fee, etc.) |
| Action required | الإجراء المطلوب | What the planner must do to execute this scenario |
| Action button | اختر هذا السيناريو | Select this scenario and move to approval |

**Key insight to convey to planner:** "IPE does not decide for you. It shows you the options and costs. You decide which is best for your customer and factory."

### 3.3 Comparing Scenarios (15 min)

**Example (use real data from the training environment):**

| | Scenario 1 | Scenario 2 | Scenario 3 |
|---|---|---|---|
| Description | Reschedule to next capacity window | Split MO into 2 batches | Expedite component purchase |
| Delivery date | +3 days late | +1 day late | On time |
| Extra cost | $0 (no overtime) | $200 (setup twice) | $850 (expedite fee) |
| Action needed | Approve in IPE only | Approve + notify customer | Approve + call supplier |

**Question to ask planner:** "If this were a real order — which scenario would you choose?" (Let them reason through it. There is no single correct answer.)

### 3.4 Selecting and Approving a Scenario (10 min)

1. Click "اختر هذا السيناريو" on the preferred scenario
2. Review confirmation dialog: "Are you sure? This will update Odoo."
3. Click "اعتماد" (Approve)
4. IPE updates the schedule and triggers Odoo write-back
5. Status changes to "Approved"
6. Odoo MO shows updated `date_start` and `date_finished` + chatter note

**Trainer action:** Have planner do this on a test MO. Verify Odoo dates updated. Show chatter note in Odoo.

---

## Block 4 — Schedule: Approving and Verifying Write-Back (30 min)

**Objectives:** Planner understands the schedule screen, can approve schedules, and can verify Odoo write-back.

### 4.1 The Schedule Screen (10 min)

**Route:** `/schedule`

- Shows Gantt chart of all scheduled manufacturing orders across work centres
- X-axis: time (days); Y-axis: work centres (Winding, Assembly, Testing, etc.)
- Color coding: green = on track; yellow = at risk; red = overloaded / late
- Click a bar: opens MO details panel on the right

**Arabic labels to point out:**
- الجدول = Schedule
- مركز العمل = Work centre
- الموافقة على الجدول = Approve schedule
- جدول مقترح = Proposed schedule
- الجدول المعتمد = Approved schedule

### 4.2 Schedule Approval Workflow (10 min)

IPE generates a proposed schedule; planner reviews and approves:

1. Click "اقتراح جدول" (Generate / Refresh schedule) — OR-Tools runs
2. Review Gantt: does the proposed schedule look reasonable?
3. Click "اعتماد الجدول" (Approve schedule)
4. Confirmation: "This will update Odoo MO dates for all scheduled orders"
5. After approval: Odoo write-back runs for all approved MOs
6. Odoo MOs show updated dates + chatter notes

**Guardrail:** MOs with feasibility score <50% cannot be approved directly. They must be resolved via the Resolution Center first.

### 4.3 Verifying Write-Back in Odoo (10 min)

**Trainer action:** After planner approves in IPE, open Odoo in a second browser tab:
1. Go to Manufacturing → Manufacturing Orders
2. Open the MO that was just approved
3. Verify `Scheduled Start` and `Scheduled End` match what IPE showed
4. Click "Log Notes" (chatter icon) — verify IPE chatter note is present

If dates are not updated within 2 minutes: check `docker compose logs connector` for write-back errors. Most common cause: API user missing write access to `mrp.production`.

---

## Block 5 — OTD Dashboard: Reading On-Time Delivery Metrics (30 min)

**Objectives:** Operations Director (and planner) can read the OTD dashboard; understand trends and root causes.

### 5.1 Dashboard Overview (10 min)

**Route:** `/otd`

| KPI Tile | Arabic Label | Meaning |
|---|---|---|
| OTD % (current month) | نسبة التسليم في الموعد (الشهر الحالي) | % of MOs completed on or before promised date this month |
| OTD % (trailing 90 days) | آخر 90 يوماً | Rolling 90-day on-time delivery rate |
| Revenue at risk | الإيرادات في خطر | Total revenue from currently at-risk MOs |
| Avg. delay (late orders) | متوسط التأخير | Average days late for orders that missed the deadline |

### 5.2 OTD Trend Chart (10 min)

- Line chart: OTD % by week over last 90 days
- Reference line: baseline OTD% captured at go-live (Day 20)
- Target line: baseline + 15% (IPE improvement target)
- Hover over a week: shows count of on-time vs. late that week

**Question to ask Operations Director:** "Looking at this chart — is there a week where OTD dropped suddenly? What happened that week?" (This links the metric to real events.)

### 5.3 Root Cause Breakdown (10 min)

- Bar chart: delays by root cause (material shortage, capacity overload, BOM missing, demand mismatch)
- Linked to IPE gate failures — a delay categorised as "capacity" means the MO's capacity gate was failing
- Click a bar: drill down to specific MOs delayed for that reason

**Arabic root cause labels:**
- نقص المواد = Material shortage
- زيادة التحميل على الطاقة = Capacity overload
- قائمة مواد مفقودة = Missing BOM
- تعارض الطلب = Demand mismatch

---

## Block 6 — Arabic Language Toggle and RTL Navigation (15 min)

**Objectives:** Planner can confidently use all screens in Arabic; knows how to switch back to English if needed.

### 6.1 Language Toggle (5 min)

- Location: Globe icon, top-right navigation bar
- Click → select العربية (Arabic) or English
- RTL layout activates immediately; no page reload needed
- Setting persists for the session; returns to default on re-login

### 6.2 RTL Navigation Tips (10 min)

| Situation | What to Expect |
|---|---|
| Menu | Opens from the right side (not left) |
| Tables | First column is on the right |
| Buttons | "Next" / "اذهب" is on the left side (RTL direction) |
| Date picker | Calendar reads right-to-left; month navigation arrows are reversed |
| Search box | Cursor starts from the right; Arabic text input works normally |
| Numbers | Always displayed in Western Arabic numerals (1, 2, 3) — not Eastern Arabic (١, ٢, ٣) |

**Note for planner:** "If a screen looks broken in Arabic — before calling us — try: 1) hard refresh (Ctrl+F5), 2) switch to English and back to Arabic, 3) different browser. If still broken, WhatsApp us with a screenshot."

---

## Block 7 — Common Questions and Troubleshooting (15 min)

### 7.1 Common Questions

**Q: An order is in Odoo but not showing in IPE.**  
A: Check the order state in Odoo — only `confirmed` and `in_progress` states sync. Draft and cancelled orders do not appear.

**Q: An order shows "لا يمكن التقييم" (Cannot score).**  
A: There is a data quality flag (check the badge). Most common: missing BOM or missing routing in Odoo. Fix the data in Odoo and wait 15 minutes for the next sync.

**Q: I approved a schedule but Odoo didn't update.**  
A: Wait 2 minutes — write-back is near-real-time, not instant. If still not updated after 5 minutes, send P1 WhatsApp message with the MO number and a screenshot.

**Q: The feasibility score seems wrong for a specific order.**  
A: Check the gate breakdown (click the MO). If it shows a gate failing that shouldn't be — e.g., "Material shortage" but you know the material is in stock — there may be a stock.quant sync lag. Wait one sync cycle and recheck.

**Q: Can we edit the schedule manually?**  
A: Not in R1. The schedule is generated by OR-Tools and requires planner approval. Direct editing of Gantt bars is not available — date changes must be made in Odoo, then IPE re-syncs.

### 7.2 Escalation Procedure (5 min)

Review `docs/runbooks/R1-CUSTOMER-SUPPORT-GUIDE.md` quick reference card with planner:

1. **Green sync bar** → everything is working
2. **Red sync bar before 8am meeting** → P0 WhatsApp immediately (use template in support guide)
3. **"Cannot score" on specific MOs** → fix data in Odoo; not Diligent's issue
4. **Feature broken (approve doesn't work, etc.)** → P1 WhatsApp with screenshot
5. **Question** → WhatsApp; not urgent

---

## Block 8 — Quick Reference Card (Arabic)

*Print and give to planner at end of training. One page. Laminate if possible.*

```
┌─────────────────────────────────────────────────────────────────────┐
│               IPE — بطاقة المرجع السريع                              │
│               الإصدار الأول — نجمة العمليات                          │
├─────────────────────────────────────────────────────────────────────┤
│  📌 الروتين اليومي                                                    │
│  ١. افتح IPE قبل اجتماع الصباح (8:00)                               │
│  ٢. تحقق من شريط المزامنة — يجب أن يكون أخضر                        │
│  ٣. افتح برج التحكم — راجع الأوامر الحمراء أولاً                    │
│  ٤. لكل أمر أحمر: مركز الحلول → اختر السيناريو → اعتمد              │
│  ٥. تحقق من تحديث Odoo بعد 2 دقيقة من الاعتماد                     │
├─────────────────────────────────────────────────────────────────────┤
│  🔴 شريط أحمر قبل الاجتماع = P0                                     │
│  أرسل رسالة WhatsApp فوراً:                                          │
│  "🚨 عاجل P0 — تأخر المزامنة                                        │
│   الوقت: [  ]  آخر مزامنة: [  ]  الاجتماع: [  ]                    │
│   [أرفق لقطة شاشة]"                                                 │
├─────────────────────────────────────────────────────────────────────┤
│  ⚠️ "لا يمكن التقييم"                                                │
│  → أصلح بيانات Odoo (BOM أو مسار العمل)                            │
│  → انتظر 15 دقيقة                                                   │
│  → إذا استمرت المشكلة: WhatsApp P2                                   │
├─────────────────────────────────────────────────────────────────────┤
│  📊 أهداف الأداء (30 يوم)                                           │
│  التسليم في الموعد: ≥ الأساس + 15%                                   │
│  أوامر قابلة للتقييم: ≥ 80%                                         │
│  نجاح المزامنة: ≥ 95%                                               │
├─────────────────────────────────────────────────────────────────────┤
│  📞 الدعم — الأحد–الخميس 9:00–18:00 (القاهرة)                      │
│  WhatsApp: [group name]                                              │
│  هاتف P0 فقط: [Waleed phone]                                        │
│  بريد: support@diligent-ai.com                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Materials Checklist

| Material | Path | Status |
|----------|------|--------|
| Deployment guide | `docs/customer/star-trans/DEPLOYMENT-GUIDE-v1.md` | Ready |
| UAT test plan | `docs/customer/star-trans/UAT-TEST-PLAN.md` | Ready |
| Odoo field mapping | `docs/integration/ODOO-19-FIELD-MAPPING.md` | Ready |
| Quick reference card | Block 8 above (print from this file) | Print before session |
| Support guide | `docs/runbooks/R1-CUSTOMER-SUPPORT-GUIDE.md` | Ready |
| Implementation playbook | `docs/implementation/IMPLEMENTATION-PLAYBOOK-v1.md` | Ready |

## Training Attendance Sign-Off

| Name | Role | Attended | Date |
|------|------|----------|------|
| | Planner champion | ☐ Yes ☐ No | |
| | Manager (optional) | ☐ Yes ☐ No | |
| | Operations Director (optional — Block 5) | ☐ Yes ☐ No | |
| | IPE trainer (Diligent) | ☐ Yes ☐ No | |

**Planner competency assessment** (complete at end of Block 3):  
☐ Planner completed full workflow (login → triage → resolution → approve) without assistance  
☐ Planner can explain the feasibility score in their own words  
☐ Planner knows when to escalate vs. self-resolve  

Trainer signature: _______________ Date: _______________
