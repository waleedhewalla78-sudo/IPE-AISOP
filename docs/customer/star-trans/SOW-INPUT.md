# SOW Input Requirements — IPE Release 1 for Star Trans

## 1. Customer Information

| Field | Value |
|-------|-------|
| Company | Star Trans |
| Industry | Electrical Transformers (Discrete Manufacturing) |
| Location | Egypt |
| IT Contact | &lt;pending&gt; |
| Planner Champion | &lt;pending&gt; |

## 2. Scope (For Legal)

- IPE Release 1 license: **8-service** deployment profile
- Modules: **Control Tower**, **Resolution Center**, **Schedule**
- Integration: **Odoo bidirectional sync** (XML-RPC)
- Language: **English** (Arabic partial for Control Tower nav where enabled)
- Support: **&lt;TBD&gt;** months post-go-live

## 3. Customer Responsibilities

| Item | Owner | Timeline |
|------|-------|----------|
| Provide Odoo staging environment with test data | Customer IT | Week 1 |
| Install `ipe_connector` Odoo module (optional) | Customer IT | Week 1 |
| Provide list of custom Odoo fields | Customer IT | Week 1 |
| Assign planner champion for training | Customer Ops | Week 2 |
| 8GB VM provisioned (cloud or on-prem) | Customer IT | Week 1 |
| Network access: VM ↔ Odoo | Customer IT | Week 1 |
| SOW signature | Customer Legal | &lt;pending&gt; |

## 4. IPE Responsibilities

| Item | Owner | Timeline |
|------|-------|----------|
| Deploy IPE stack on customer VM | IPE Eng | Week 2 |
| Configure Odoo integration | IPE Eng | Week 2 |
| Seed test data and verify sync | IPE Eng | Week 2 |
| Planner training (4 hours) | IPE PM | Week 3 |
| UAT support | IPE Eng | Week 3–4 |
| Go-live sign-off | IPE + Customer | Week 4 |

## 5. Pricing (NEEDS COMMERCIAL CONFIRMATION — OQ-7)

| Item | Annual / One-time Cost | Notes |
|------|------------------------|-------|
| IPE Release 1 License | **$18K–30K** / year | Per spec 013 — **confirm with Sales** |
| Implementation | **$12K–25K** one-time | Deploy, integrate, train, UAT support |
| Optional: Enterprise Add-on (SSO, Vault, Monitoring) | TBD | Phase 0–2 features |

> **OQ-7:** Commercial pricing must be confirmed by Sales before SOW finalization.

## 6. Open Questions for Customer

1. Odoo version: **17 or 19?** (OQ-1)
2. Single-site or multi-site? (affects scaling)
3. Cloud VM provider? (AWS / Azure / local)
4. Number of planner users? (affects license)
5. Custom Odoo fields beyond standard MRP? (affects mapper — see field mapping worksheet)
6. Arabic required for all screens or Control Tower only?
7. Data retention / compliance requirements? (GDPR, local regs)

## 7. Blockers (Current)

| Blocker | Status |
|---------|--------|
| Signed SOW | ⬜ Pending |
| Customer IT Odoo staging access | ⬜ Pending |

## 8. References

- Deployment: `docs/customer/star-trans/DEPLOYMENT-GUIDE-v1.md`
- UAT: `docs/customer/star-trans/UAT-TEST-PLAN.md`
- Field mapping: `docs/customer/star-trans/ODOO-FIELD-MAPPING-WORKSHEET.md`
- Training: `docs/implementation/R1-TRAINING-CURRICULUM.md`
