# Star Trans Release 1 — Business Track Status

**Updated**: 2026-07-11 (Spec 022)  
**Customer**: Star Trans — Electrical Transformers, Egypt/MENA  
**Engineering**: Sprint 1 `v9.2.0-planning` tagged; Sprint 2 GTM package complete; Sprint 3 go-live readiness active

---

## Track B deliverables

| Document | Path | Status |
|----------|------|--------|
| Deployment Guide | `docs/customer/star-trans/DEPLOYMENT-GUIDE-v1.md` | Ready |
| SOW v1 | `docs/customer/star-trans/IPE-Star-Trans-SOW-v1.md` | Artifact ready — **send blocked by OQ-7 pricing** |
| SOW Input | `docs/customer/star-trans/SOW-INPUT.md` | Ready for legal after OQ-7 |
| UAT Test Plan | `docs/customer/star-trans/UAT-TEST-PLAN.md` | Ready |
| Odoo Field Mapping | `docs/customer/star-trans/ODOO-FIELD-MAPPING-WORKSHEET.md` | Ready for customer IT |
| Training Curriculum | `docs/implementation/R1-TRAINING-CURRICULUM.md` | Ready |
| Sales one-pagers EN/AR | `docs/sales/` | Ready (Sprint 2) |
| Support guide | `docs/runbooks/R1-CUSTOMER-SUPPORT-GUIDE.md` | Ready |
| Release notes | `docs/customer/star-trans/RELEASE-NOTES-R1.md` | Ready |
| Deploy package | `deploy/star-trans/` | Ready (Sprint 3 dry-run) |
| Validate script | `scripts/star-trans-validate.ps1` | Ready |

---

## Business gates (external — parallel track)

| Gate | Owner | Status | Action |
|------|-------|--------|--------|
| **OQ-7 pricing** | Waleed | OPEN — BLOCKING | Fill SOW amounts before send |
| **SOW signature** | Customer Legal | Pending | After OQ-7 |
| **Odoo staging access (PH1-02)** | Customer IT | OPEN | Staging URL + test MOs |
| **Odoo version confirm (OQ-1)** | Star Trans IT | OPEN | Confirm 17 or 19 (connector supports both via aliases) |
| **Field mapping worksheet** | Customer IT | Pending | Week 1 |
| **8GB VM provisioned** | Customer IT | Pending | Ubuntu 22.04 or Windows Server |
| **Planner champion** | Customer Ops | Pending | Week 2 training |
| **Arabic native QA (G-R2-04)** | Native reviewer | OPEN | Required before `v9.1.1-r2` |
| **UAT execution** | IPE + Customer | Blocked | Requires SOW + staging |
| **Go-live sign-off** | IPE + Customer | Blocked | After UAT PASS |

---

## Open questions

| ID | Question | Engineering stance | Commercial |
|----|----------|-------------------|------------|
| OQ-1 | Odoo 17 vs 19? | Dual support: validated against 19 locally; 17 field aliases in mapper | Confirm with Star Trans IT |
| OQ-3 | UI RBAC priority? | Defer post-R1 unless contract requires | Formal COM decision |
| OQ-7 | Commercial pricing? | No eng action | **Blocks SOW send** |

---

## Recommended next actions (business)

1. **Waleed**: Decide OQ-7 pricing; remove SOW placeholders; send SOW
2. **Star Trans IT**: Confirm Odoo version (OQ-1) + provision staging (PH1-02)
3. **Native reviewer**: G-R2-04 Arabic sign-off → then cut `v9.1.1-r2` (do **not** push stale `v9.1.0-r2`)
4. **On SOW sign**: Schedule Week 2 deploy; run `scripts/star-trans-validate.ps1`

---

*Engineering does not invent COM closures. Spec 022 documents blockers honestly.*
