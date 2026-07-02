# Clarification Record: 013-release1-odoo-mena

**Version**: 2.0 (post-implementation)  
**Date**: 2026-06-29  
**Spec**: `spec.md` v2.0

---

## Resolved (locked — do not reopen without customer change)

| ID | Question | Decision | Date |
|----|----------|----------|------|
| OQ-1 | Customer #1 | **Star Trans** — Electrical Transformer Technology, Egypt | 2026-06-29 |
| OQ-3 | Odoo version | **17.0** with `mrp` module | 2026-06-29 |
| OQ-6 | Demo vs production data | SQL overlay (012) = sales only; production = Odoo sync | 2026-06-29 |
| OQ-7 | Release profile | `IPE_RELEASE_PROFILE=release1` → 8-service stack, 15-min sync | 2026-06-29 |
| OQ-8 | Primary competition | Excel + Odoo MRP (not Kinaxis) | 2026-06-29 |
| OQ-9 | Arabic scope R1 | Control Tower + nav + sync bar MVP; Resolution/Login partial OK for UAT if flagged | 2026-06-29 |
| OQ-10 | Write-back path | `ERP_SYNC_MODE=direct` → cap-svc → connector → Odoo XML-RPC | 2026-06-29 |

---

## Open — must resolve before UAT sign-off

### OQ-2: Star Trans hosting model

| Option | Pros | Cons |
|--------|------|------|
| **A. Diligent cloud (recommended default)** | Faster deploy, we control updates | Customer may require data residency |
| **B. On-prem Windows VM** | Matches factory IT policy | T037 validation required; slower support |

**Recommendation:** Propose **A** in SOW; offer **B** as +$5K setup if IT mandates.  
**Needed from customer:** IT contact, firewall rules for outbound HTTPS to our cloud, or VM specs (8GB RAM, Windows Server 2019+).

**Default if no answer by kickoff:** Cloud staging on Diligent infra; document VPN option in playbook §3.

---

### OQ-4: SOW scope and pricing

**Underspecified:**

- Exact user count (planners vs read-only executives)
- WhatsApp support hours (business hours Cairo vs 24/7)
- PoC duration (30 vs 60 days) before production cutover
- Who owns Odoo custom field mapping workshops

**Recommendation:**

| Line item | Suggested |
|-----------|-----------|
| License | $24K/yr (mid-market transformer mfg) |
| Implementation | $18K fixed (Odoo sync + 2 workshops + UAT) |
| PoC | 45 days, success = SC-R1-04 + SC-R1-05 |
| Support | Email + WhatsApp business hours (Cairo TZ) |

**Action:** T002 — legal to draft from playbook sign-off checklist.

---

### OQ-5: Second prospect timeline

**Question:** Start prospect #2 before or after Star Trans UAT?

**Recommendation:** **Parallel discovery only** — no engineering until Star Trans UAT passes (Principle VII).  
**Action:** T004 — identify name + ERP by day 60 of Star Trans engagement.

---

### OQ-11: Odoo custom fields on `mrp.production`

**Underspecified:** Star Trans may use custom fields (transformer specs, test bay, etc.) not in default mapper.

**Clarification needed:**

1. Export Odoo `mrp.production` field list from staging (worksheet §2)
2. Map only fields needed for feasibility (qty, dates, product, state, BOM)
3. Custom fields → `cdm_manufacturing_order.metadata` JSONB (optional R1.1)

**Default:** Sync standard Odoo 17 fields only; custom fields ignored unless listed in signed field mapping worksheet.

---

### OQ-12: Routing source in Odoo 17

**Underspecified:** Odoo 17 uses `mrp.routing.workcenter` / operation templates; our CDM expects `cdm_routing_operation`.

**Options:**

| Option | Effort | Recommendation |
|--------|--------|------------------|
| Sync from BOM `operation_ids` | Medium | **P0 for UAT** — T080 |
| Manual routing seed for PoC | Low | Acceptable only if Star Trans has <5 routings |
| Skip routing → all MOs `MISSING_ROUTING` | Zero | **Unacceptable for production** |

**Default:** Implement T080 before UAT if Star Trans has routings in Odoo; else workshop to seed minimal routing in CDM for PoC only.

---

### OQ-13: Credential storage

**Current:** Odoo password in tenant `config` JSONB (plaintext in DB).

**Question:** Acceptable for PoC?

**Recommendation:** Yes for staging UAT with signed security addendum; **vault (T081)** before production invoice.

---

### OQ-14: Post-sync feasibility trigger

**Underspecified:** After sync, when does scoring run?

| Option | Status |
|--------|--------|
| Manual "Rescore" in UI | Not built |
| fea-svc webhook from connector post-sync | **Recommended — T082** |
| Scheduled batch rescore every 15 min | Acceptable fallback |

**Default:** T082 — connector calls `POST /feasibility/rescore` for touched MO IDs after successful sync run.

---

### OQ-15: web-ui deployment for customer

**Current:** `apps/web` runs on host (`npm run dev`); not in `docker-compose.release1.yml`.

**Options:**

| Option | Recommendation |
|--------|----------------|
| Add `web-ui` service to compose with nginx | **R1.1 — T083** |
| Customer accesses via our hosted URL | OK for cloud PoC |
| Static build served by Kong | Preferred for on-prem |

**Default for UAT:** Hosted staging URL; document `VITE_RELEASE_PROFILE=release1` for local QA.

---

## Assumptions (explicit — validate at kickoff)

1. Star Trans Odoo 17 is **Community or Enterprise** with `mrp` installed — not Odoo.sh without API access.
2. Planners use **Arabic** as primary UI language; executives may use English.
3. **≤50 concurrent MOs** in active planning horizon for R1 performance.
4. Network: factory can reach connector URL (HTTPS 443) on schedule.
5. **No bi-directional BOM edit** in R1 — BOM is read-only from Odoo.
6. Single tenant UUID for Star Trans in R1 (`a0eebc99-...` in dev; new UUID in prod).

---

## Clarification workshop agenda (Star Trans kickoff)

| # | Topic | Owner | Output |
|---|-------|-------|--------|
| 1 | OQ-2 hosting | IT + Diligent | Signed deployment model |
| 2 | OQ-11 field mapping | Planner + IT | Completed worksheet |
| 3 | OQ-12 routing | Production mgr | List of routings in Odoo |
| 4 | OQ-4 SOW | Commercial | Signed SOW (T002) |
| 5 | Staging credentials | IT | T003 complete |
| 6 | UAT scenarios | Planner | Checklist in playbook §7 |

---

## Traceability

Unresolved OQs map to tasks: T002, T003, T004, T080–T083, T071.
