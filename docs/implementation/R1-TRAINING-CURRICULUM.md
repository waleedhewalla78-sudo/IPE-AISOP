# R1 Training Curriculum — Star Trans / Release 1

**Duration:** 4 hours (including breaks)  
**Audience:** Planner champion, optional manager / executive observers  
**Prerequisites:** IPE deployed; Odoo staging synced; trainee accounts created  
**Last updated:** 2026-07-04

---

## Agenda

| Block | Duration | Topic |
|-------|----------|--------|
| 1 | **30 min** | Product overview |
| 2 | **60 min** | Hands-on: Control Tower → Resolution → Schedule |
| — | 15 min | Break |
| 3 | **30 min** | Odoo sync monitoring and troubleshooting |
| 4 | **30 min** | Executive dashboard walkthrough |
| 5 | **15 min** | Q&A |
| — | 20 min | Buffer / recap / homework |

---

## Block 1 — Product Overview (30 min)

**Objectives:** Understand what IPE Release 1 does and does not do.

| Topic | Points |
|-------|--------|
| Problem | Late MOs, Excel planning, Odoo MRP alone |
| IPE role | Feasibility scores, resolution scenarios, OR-Tools schedule, Odoo write-back |
| Architecture (simple) | Browser → Kong → services → PostgreSQL ↔ Odoo |
| Roles | Planner, manager, admin, executive |
| Out of scope (R1) | Full Arabic, demand sensing, multi-ERP, self-service SaaS |

**Demo:** Login page + Control Tower at-a-glance (no deep dive yet).

---

## Block 2 — Hands-on Workflow (60 min)

**Objectives:** Complete one end-to-end planner cycle.

| Step | Duration | Activity |
|------|----------|----------|
| Login | 5 min | Planner account; tenant context |
| Control Tower | 15 min | Queue, scores, at-risk filter, KPIs |
| Resolution | 15 min | Open scenarios; compare cost vs delivery; apply one |
| Schedule | 15 min | Generate schedule; read Gantt; approve |
| Activate | 10 min | Write-back to Odoo; verify dates in Odoo UI |

**Success criteria:** Trainee completes TC-06 style flow without instructor driving the mouse.

---

## Block 3 — Odoo Sync Monitoring (30 min)

**Objectives:** Know when data is stale and how to recover.

| Topic | Content |
|-------|---------|
| When to sync | Morning, after large Odoo changes |
| Sync status | Last run, success/fail, entity counts |
| Data quality flags | What they mean; who fixes (Odoo master data) |
| Common failures | Wrong URL, credentials, Odoo down, network |
| Escalation | Customer IT vs IPE support |

**Exercise:** Trigger a partial sync; interpret status bar.

---

## Block 4 — Executive Dashboard (30 min)

**Objectives:** Read OTD / command views for decision support.

| Topic | Content |
|-------|---------|
| Command Center | High-level risk and OTD |
| What executives should not do | Direct schedule edits (planner-owned) |
| Cadence | Weekly review with planner champion |

**Exercise:** Login as executive (or shared view); identify one at-risk signal.

---

## Block 5 — Q&A (15 min)

Capture open questions in `SOW-INPUT.md` §6 if they affect scope.

---

## Materials

| Material | Path |
|----------|------|
| Deployment guide | `docs/customer/star-trans/DEPLOYMENT-GUIDE-v1.md` |
| UAT plan | `docs/customer/star-trans/UAT-TEST-PLAN.md` |
| Field mapping | `docs/customer/star-trans/ODOO-FIELD-MAPPING-WORKSHEET.md` |

## Attendance / Sign-off

| Name | Role | Attended | Date |
|------|------|----------|------|
| | Planner champion | | |
| | Manager (optional) | | |
| | Executive (optional) | | |
| | IPE trainer | | |
