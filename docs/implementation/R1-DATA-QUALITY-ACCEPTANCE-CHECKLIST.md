# Data Quality Acceptance Checklist — Release 1

**Customer:** _______________________________  
**Odoo version:** 17.0  
**Environment:** ☐ Staging · ☐ Production  
**Assessment date:** _______________  
**Assessed by:** _______________ (Provider) + _______________ (Customer planner/IT)

**Purpose:** Confirm that Odoo master data is sufficient for IPE to score manufacturing orders before UAT sign-off and go-live. This checklist is **Exhibit B8** of the Customer SOW.

---

## 1. How IPE uses your Odoo data

```text
Odoo                          IPE checks                    If missing
─────────────────────────────────────────────────────────────────────────
product.product          →    product sync                  MISSING_PRODUCT
mrp.bom (+ lines)        →    BOM linked to MO              MISSING_BOM
routing / operations     →    operations on BOM             MISSING_ROUTING
mrp.workcenter           →    WC capacity for routing       MISSING_WC
mrp.production           →    MO queue + feasibility        Cannot score
write_date conflict      →    after IPE schedule approve    SYNC_CONFLICT
```

**Important:** Flags labeled “data quality” are **not software defects**. They mean something must be fixed **in Odoo**, then the next sync (within 15 minutes) clears the flag.

---

## 2. Acceptance targets

| Metric | Staging minimum | Production go-live | 30-day post go-live |
|--------|-----------------|--------------------|---------------------|
| MOs visible in Control Tower | 100% of test set (≥10 MOs) | 100% active MOs in horizon | 100% |
| MOs **scorable** (feasibility score shown) | **≥70%** | **≥80%** | **≥85%** |
| MOs with data quality flags | Document each | Remediation plan signed | Trending down |
| Sync success rate (7 days) | **≥90%** | **≥95%** | **≥95%** |
| Write-back success (test MOs) | 3/3 pass | 3/3 pass | No P1 write-back incidents |

---

## 3. Flag reference (planner-facing)

| Flag code | Arabic label (planner UI) | Meaning | Fix in Odoo |
|-----------|---------------------------|---------|-------------|
| `MISSING_BOM` | لا يوجد قائمة مواد | MO has no BOM | Manufacturing → BOMs → link product BOM |
| `MISSING_ROUTING` | لا يوجد مسار تشغيل | BOM has no operations | Add routing / operations to BOM |
| `MISSING_WC` | مركز العمل غير متزامن | Work center missing in IPE | Verify `mrp.workcenter` exists and sync ran |
| `MISSING_PRODUCT` | المنتج غير موجود | Product not synced | Check product active in Odoo |
| `SYNC_CONFLICT` | تعارض مع Odoo | Odoo changed after IPE approval | Open Resolution Center; reconcile dates |

---

## 4. Pre-sync master data checklist (Customer IT + planner)

Complete **before** first staging sync.

### 4.1 Products

- [ ] All manufactured items have active `product.product` records  
- [ ] `default_code` or internal reference populated (recommended for transformer/SKU traceability)  
- [ ] No duplicate product IDs for same physical item  
- [ ] Sample count verified: ______ active manufactured products  

### 4.2 Bills of material

- [ ] Each manufactured product has **at least one active BOM**  
- [ ] BOM **components** (lines) populated — not header-only  
- [ ] BOM quantity matches production UoM (units, kVA rating bucket, etc.)  
- [ ] Phantom/subassembly BOMs documented in field mapping worksheet if used  

### 4.3 Routings and work centers

- [ ] Each BOM has **routing operations** (sequence, work center, duration)  
- [ ] Work centers reflect real bays: winding, assembly, testing, packing, etc.  
- [ ] `default_capacity` or calendar set on work centers (hours/day)  
- [ ] Work center names match shop floor terminology (Arabic/English consistent)  

### 4.4 Manufacturing orders

- [ ] Sample **10 MOs** selected spanning: simple, multi-operation, near-due, far-future  
- [ ] Each sample MO in state `confirmed` or `progress` (not draft/cancelled)  
- [ ] `date_start` / `date_finished` populated  
- [ ] `bom_id` linked on each sample MO  

### 4.5 Service account and connector

- [ ] Odoo service user can read BOM, MO, work center  
- [ ] Service user can **write** `date_start` / `date_finished` on `mrp.production` (write-back test)  
- [ ] `ipe_connector` module installed (staging)  
- [ ] Network path Odoo ↔ IPE verified  

---

## 5. Sample MO assessment (required — fill 10 rows)

Copy from Odoo **Manufacturing → Operations → Manufacturing Orders**.

| # | Odoo MO (e.g. MO/00123) | Product | Has BOM? | Has routing ops? | WC defined? | Scorable in IPE? | Flag if not | Customer action |
|---|-------------------------|---------|----------|------------------|-------------|------------------|-------------|-------------------|
| 1 | | | ☐ | ☐ | ☐ | ☐ | | |
| 2 | | | ☐ | ☐ | ☐ | ☐ | | |
| 3 | | | ☐ | ☐ | ☐ | ☐ | | |
| 4 | | | ☐ | ☐ | ☐ | ☐ | | |
| 5 | | | ☐ | ☐ | ☐ | ☐ | | |
| 6 | | | ☐ | ☐ | ☐ | ☐ | | |
| 7 | | | ☐ | ☐ | ☐ | ☐ | | |
| 8 | | | ☐ | ☐ | ☐ | ☐ | | |
| 9 | | | ☐ | ☐ | ☐ | ☐ | | |
| 10 | | | ☐ | ☐ | ☐ | ☐ | | |

**Scorable MO count:** _____ / 10 = _____%  
**Projected active MO scorable % (Provider estimate):** _____%

---

## 6. Post-sync verification (Provider + planner)

Run after `POST /api/v1/sync/run` or wait one scheduled cycle (15 min).

### 6.1 Control Tower

- [ ] Sync status bar shows green / “محدّث” with timestamp < 20 min  
- [ ] Sample MOs appear in queue with correct product name and dates  
- [ ] MOs with complete Odoo data show **feasibility score** (0–100%)  
- [ ] MOs with gaps show **“لا يمكن التقييم”** + flag badge — matches §5 table  

### 6.2 API cross-check (Provider)

```sql
-- Replace tenant UUID
SELECT flag_code, COUNT(*) 
FROM cdm_data_quality_flag 
WHERE tenant_id = '<tenant-uuid>' AND resolved_at IS NULL
GROUP BY flag_code;
```

| flag_code | count | Acceptable for staging? |
|-----------|-------|-------------------------|
| MISSING_BOM | | ☐ Yes ☐ No — fix required |
| MISSING_ROUTING | | ☐ Yes ☐ No — fix required |
| MISSING_WC | | ☐ Yes ☐ No — fix required |
| SYNC_CONFLICT | | ☐ Expected 0 at UAT |

### 6.3 Write-back spot check

| Test MO | Approve in IPE | Odoo date_start updated? | Pass |
|---------|----------------|--------------------------|------|
| 1 | | ☐ | |
| 2 | | ☐ | |
| 3 | | ☐ | |

---

## 7. Remediation plan (if <80% scorable)

| Priority | Flag / root cause | # MOs affected | Owner | Target date | Status |
|----------|-------------------|----------------|-------|-------------|--------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

**Interim planning rule (if go-live before 100%):** Planners continue Excel for unscored MOs only; scored MOs **must** be managed in IPE.

---

## 8. MENA discrete manufacturing notes

Typical data gaps in transformer / electrical / job-shop environments:

| Pattern | Common gap | Recommended fix |
|---------|------------|-----------------|
| Engineer-to-order | BOM created late after MO | Process: no MO release without BOM |
| Long cycle times | Single WC “Assembly” hides bottlenecks | Split routing: winding, core, test, paint |
| Subcontract ops | Outside processing not in Odoo routing | Add virtual WC or subcontract operation |
| Arabic product names | Display fine; ensure consistent Odoo `name` | No change if readable in Control Tower |
| Legacy Excel routes | Routing only in spreadsheet | Migrate routing to Odoo BOM over 2–4 weeks |

---

## 9. Sign-off

| Criterion | Met? |
|-----------|------|
| ≥80% scorable on staging (or signed remediation plan) | ☐ |
| 10-MO sample worksheet complete | ☐ |
| Write-back 3/3 pass | ☐ |
| Planner acknowledges flag meanings in Arabic | ☐ |
| Customer IT acknowledges Odoo-side ownership of fixes | ☐ |

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Customer planner champion | | | |
| Customer IT / Odoo admin | | | |
| Diligent implementation lead | | | |

**UAT may proceed:** ☐ Yes · ☐ No — return to §7 remediation

---

*Related: `R1-CUSTOMER-SOW-TEMPLATE.md` Exhibit B · `ODOO-FIELD-MAPPING-WORKSHEET.md` §5*
