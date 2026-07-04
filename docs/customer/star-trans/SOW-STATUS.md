# Star Trans Release 1 — Business Track Status

**Updated**: 2026-07-04  
**Customer**: Star Trans — Electrical Transformers, Egypt/MENA  
**Engineering demo**: 14/14 HTTPS ✅ (local Gate 5)

---

## Track B deliverables (engineering complete)

| Document | Path | Status |
|----------|------|--------|
| Deployment Guide | `docs/customer/star-trans/DEPLOYMENT-GUIDE-v1.md` | ✅ Ready |
| SOW Input | `docs/customer/star-trans/SOW-INPUT.md` | ✅ Ready for legal |
| UAT Test Plan | `docs/customer/star-trans/UAT-TEST-PLAN.md` | ✅ Ready |
| Odoo Field Mapping | `docs/customer/star-trans/ODOO-FIELD-MAPPING-WORKSHEET.md` | ✅ Ready for customer IT |
| Training Curriculum | `docs/implementation/R1-TRAINING-CURRICULUM.md` | ✅ Ready |

---

## Business gates (external — parallel track)

| Gate | Owner | Status | Action |
|------|-------|--------|--------|
| **SOW signature** | Customer Legal | ⬜ Pending | Send `SOW-INPUT.md` to legal; confirm OQ-7 pricing |
| **Odoo staging access** | Customer IT | ⬜ Pending | VM/network + Odoo 17 or 19 staging URL + test MOs |
| **Field mapping worksheet** | Customer IT | ⬜ Pending | Week 1 — custom fields + version confirmation |
| **8GB VM provisioned** | Customer IT | ⬜ Pending | Windows Server 2019+ or Ubuntu 22.04 |
| **Planner champion** | Customer Ops | ⬜ Pending | Assign for Week 2 training |
| **UAT execution** | IPE + Customer | ⬜ Blocked | Requires SOW + staging (see UAT-TEST-PLAN.md) |
| **Go-live sign-off** | IPE + Customer | ⬜ Blocked | Week 4 after UAT PASS |

---

## Open questions for stakeholder decision

| ID | Question | Recommendation |
|----|----------|----------------|
| OQ-1 | Odoo 17 vs 19? | **17 primary** — confirm in field mapping worksheet |
| OQ-3 | UI RBAC priority? | Defer post-R1 unless contract requires |
| OQ-7 | Commercial pricing? | $18K–30K license + $12K–25K implementation (SOW-INPUT) |

---

## Recommended next actions (business)

1. **This week**: Email customer IT the field mapping worksheet + deployment prerequisites
2. **Legal**: Circulate SOW-INPUT for commercial/pricing confirmation (OQ-7)
3. **On SOW sign**: Schedule Week 2 deploy window; request Odoo staging credentials
4. **Week 3–4**: Execute UAT-TEST-PLAN TC-01 through TC-07 on live Odoo data

---

*Engineering does not block on this track — Phase 3 K8s/compliance continues in parallel.*
