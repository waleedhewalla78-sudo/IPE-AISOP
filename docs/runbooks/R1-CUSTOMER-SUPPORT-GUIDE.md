# Customer Support Guide — IPE Release 1

**Audience:** Customer planners, production managers, IT contacts — **not** Diligent engineers  
**Language:** Arabic primary · English below each section  
**Product:** IPE Control Tower on Odoo 17  
**Support:** WhatsApp group + phone · Sun–Thu 08:00–18:00 Cairo (adjust per contract)

---

## 1. How to get help

### 1.1 WhatsApp first (recommended)

Join the group: **`IPE — [Your company] Support`**

| Do send | Do not send |
|---------|-------------|
| Screenshot of the problem | Long voice notes without text summary |
| Odoo MO number (e.g. MO/00456) | Passwords or Odoo admin credentials |
| Time you noticed the issue | Multiple messages for same issue — use one thread |
| Whether sync bar is green or red | GitHub links or “open a ticket” |

**Response times (contract):**

| Urgency | When to use | Target response |
|---------|-------------|-----------------|
| **Urgent (P0)** | Sync failed **before production meeting** (~7–8am); no fresh data | **2 hours** |
| **High (P1)** | Cannot approve schedule; login broken for all users | Same business day |
| **Normal (P2)** | One order looks wrong; Arabic text cut off | Next business day |
| **Question (P3)** | “How do I…?” training | Same or next day |

### 1.2 Phone

Use phone **only for P0** when WhatsApp unanswered after **30 minutes** during business hours.

**Diligent L1:** [Name] · [+20 XXX XXX XXXX]

### 1.3 Email

Formal requests, contracts, invoices: [support@diligent.example]

---

## 2. Scenario: Sync failed before the 7am production meeting

**Arabic summary:** المزامنة فشلت قبل اجتماع الإنتاج — هذا عاجل (P0)

This is the **most common urgent scenario** for MENA factories with early daily production meetings.

### 2.1 What you see

- Sync bar shows **red** or **“تأخر المزامنة”** (sync delayed)  
- “Last synced” time is **more than 30 minutes ago**  
- New orders entered in Odoo yesterday **do not appear** in Control Tower  
- Meeting starts in less than 2 hours  

### 2.2 What to do (planner) — step by step

| Step | Action |
|------|--------|
| 1 | **Do not panic** — last successful sync data is still visible; note the timestamp on sync bar |
| 2 | Open WhatsApp group immediately |
| 3 | Send **P0 message** (copy template below) + screenshot of sync bar |
| 4 | For meeting: use **scored MOs from IPE**; use **Excel only for MOs not in IPE or unscorable** |
| 5 | Wait for Diligent reply — do **not** re-approve schedules until sync is green again |

### 2.3 WhatsApp message template — P0 sync failure

**Arabic (copy-paste):**

```text
🚨 عاجل P0 — تأخر المزامنة قبل الاجتماع
الوقت الآن: [مثال 6:45 ص]
آخر مزامنة ظاهرة: [من الشريط — مثال 4:30 ص]
الاجتماع: [8:00 ص]
لا تظهر أوامر جديدة من Odoo أمس
[أرفق لقطة شاشة لشريط المزامنة]
```

**English:**

```text
🚨 P0 URGENT — Sync delayed before production meeting
Current time: [e.g. 6:45am]
Last sync shown: [from bar — e.g. 4:30am]
Meeting: [8:00am]
New Odoo orders from yesterday not visible
[Attach sync bar screenshot]
```

### 2.4 What Diligent will do

1. Acknowledge within **30 minutes** (target)  
2. Check connector and Odoo connection (you may be asked: “Is Odoo website loading?”)  
3. Fix or communicate **Excel fallback plan** before your meeting  
4. Send “sync restored” message with new timestamp  

### 2.5 What is NOT a sync bug

| Situation | Who fixes |
|-----------|-----------|
| Single MO missing BOM | Your team in Odoo — see §4 |
| Odoo website down entirely | Your IT restarts Odoo server |
| Internet down at factory | Your IT — IPE cannot reach Odoo |
| MO shows “Cannot score” | Usually missing BOM/routing in Odoo |

---

## 3. Scenario: Sync bar green but order missing

1. Confirm MO exists in Odoo and state is not **Draft** or **Cancelled**  
2. Wait **one full sync cycle** (15 minutes)  
3. If still missing, WhatsApp **P2** with Odoo MO number and screenshot from Odoo  

---

## 4. Scenario: “Cannot score” / “لا يمكن التقييم” on an MO

**This is usually Odoo data, not an IPE bug.**

| Badge / flag | Meaning | Your fix in Odoo |
|--------------|---------|------------------|
| Missing BOM | No bill of materials | Manufacturing → Products → add BOM |
| Missing routing | BOM has no operations | Add routing steps to BOM |
| Missing work center | Work center not set up | Manufacturing → Work Centers |
| Sync conflict | Odoo changed after IPE approval | Open **Resolution Center** → reconcile |

After fixing in Odoo, wait **15 minutes** or ask Diligent to trigger manual sync (P2).

**Full checklist:** `R1-DATA-QUALITY-ACCEPTANCE-CHECKLIST.md`

---

## 5. Scenario: Schedule approved but Odoo dates unchanged

| Step | Action |
|------|--------|
| 1 | Wait 2 minutes — write-back is not instant |
| 2 | Refresh MO in Odoo |
| 3 | If still wrong: WhatsApp P1 with MO number + screenshot IPE approve screen + Odoo dates |
| 4 | Do not duplicate approve clicks — one approve per MO |

**Common cause:** Odoo user permissions — IT must ensure service account can edit manufacturing order dates.

---

## 6. Scenario: Login problems

| Symptom | Try first | Then |
|---------|-----------|------|
| Wrong password | Caps lock; Arabic keyboard | Manager requests reset from Diligent |
| Blank page | Different browser (Chrome/Edge) | WhatsApp P1 with screenshot |
| “Network error” | Check internet / VPN | WhatsApp P1 |

**Do not share password in WhatsApp.**

---

## 7. Scenario: Arabic layout looks wrong

1. Click language switcher → select **العربية**  
2. Refresh page (F5)  
3. If one screen still English-only: WhatsApp P2 with screenshot — note screen name  
4. **Workaround:** use English temporarily for that screen only; return to Arabic for Control Tower  

---

## 8. Escalation path (who you talk to)

```text
You (planner/manager)
        │
        ▼ WhatsApp / phone (always start here)
   Diligent L1 engineer
        │
        ├── Fixed same day → done
        │
        └── Sync down >2h / data wrong for many MOs
                │
                ▼
           Engineering lead (L2)
                │
                └── Contract / commercial issue
                        │
                        ▼
                   Account lead (L3)
```

**You never need to:** restart servers, run Docker, open database, or install software updates — that is Diligent or your IT (Odoo only).

---

## 9. Your IT contact — Odoo-side checklist

Share with Customer IT (not daily planner workflow):

| Task | Frequency |
|------|-----------|
| Keep Odoo server running and backed up | Daily |
| Maintain service account password | When changed — notify Diligent **before** sync fails |
| Install `ipe_connector` updates when Diligent sends | As released |
| Allow network Odoo ↔ IPE | One-time firewall |
| Fix BOM/routing master data when planner reports flags | Weekly until ≥85% scorable |

**Install guide:** `docs/integration/ODOO-CONNECTOR-INSTALL.md`

---

## 10. Quick reference card (print for planner desk)

```text
┌─────────────────────────────────────────────────────────────┐
│  IPE — بطاقة الدعم السريع                                    │
├─────────────────────────────────────────────────────────────┤
│  افتح IPE قبل 8:00 → الشريط الأخضر = OK                      │
│  أحمر = WhatsApp فوراً (قالب P0 في الدليل §2)                 │
│  "لا يمكن التقييم" = أصلح BOM/مسار في Odoo                   │
│  بعد الاعتماد → تحقق من تاريخ Odoo                           │
│  WhatsApp: [group name]  ·  هاتف P0 فقط: [phone]             │
│  ساعات الدعم: الأحد–الخميس 8–6 القاهرة                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 11. FAQ

**Q: Can we use Excel and IPE together?**  
A: During first 30 days, yes for **unscorable** MOs only. Goal: all active MOs in IPE by day 30.

**Q: How often does data update?**  
A: Every **15 minutes** automatically.

**Q: Who pays if Odoo is down?**  
A: Odoo uptime is Customer IT. IPE sync resumes automatically when Odoo returns.

**Q: Is WhatsApp secure for production data?**  
A: Send MO **numbers** and **screenshots** — not passwords. Group is invite-only.

**Q: What if we need help on Friday / Saturday?**  
A: Contract covers Sun–Thu. P0 on off-days: best-effort reply; plan critical approves before Thursday.

---

*Engineer runbook (Diligent internal): `R1-SUPPORT-RUNBOOK.md`*  
*SOW support terms: `R1-CUSTOMER-SOW-TEMPLATE.md` §8*
