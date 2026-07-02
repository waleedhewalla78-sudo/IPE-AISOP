# Release 1 Implementation Playbook — Star Trans / Odoo 17

**Customer:** Star Trans — Electrical Transformer Technology (Egypt)  
**ERP:** Odoo 17 Community or Enterprise with `mrp`, `stock`, `purchase`, `sale`  
**IPE release:** v9.0.0-r1  
**Duration:** 6–8 weeks implementation + 90-day ROI period

**Customer-facing package (sign-off ready):**

| Document | Path |
|----------|------|
| SOW template | `docs/implementation/R1-CUSTOMER-SOW-TEMPLATE.md` |
| Data quality acceptance | `docs/implementation/R1-DATA-QUALITY-ACCEPTANCE-CHECKLIST.md` |
| Training curriculum | `docs/implementation/R1-TRAINING-CURRICULUM.md` |
| Customer support guide | `docs/runbooks/R1-CUSTOMER-SUPPORT-GUIDE.md` |
| Engineer support runbook | `docs/runbooks/R1-SUPPORT-RUNBOOK.md` |

---

## 1. Scope of work (fixed SOW)

Full legal template with pricing, SLA, exhibits: **`R1-CUSTOMER-SOW-TEMPLATE.md`**.

### Included

| Deliverable | Description |
|-------------|-------------|
| Odoo connector | 15-min batch sync: products, work centers, BOMs, manufacturing orders |
| Control Tower | Feasibility queue from live Odoo MOs |
| Resolution Center | Scenario comparison for at-risk orders |
| Schedule approve | Write-back approved dates to Odoo `mrp.production` |
| Executive OTD | Weekly trend + baseline capture |
| Arabic MVP | Control Tower, Resolution, nav, login, alerts |
| Deployment | Diligent-managed cloud VM **or** customer on-prem (see OQ-2) |
| Training | 2× half-day sessions (planner + manager) |
| Support | WhatsApp + phone, business hours, same-day response (12 months) |

### Excluded (Phase 2+)

Copilot, demand sensing, scenario sandbox, supply network, quality/sustainability dashboards, SAP/D365, Keycloak SSO, Stripe billing.

---

## 2. Pricing envelope (reference)

| Item | Amount (USD) |
|------|--------------|
| Annual license | $18,000 – $30,000 |
| One-time implementation | $12,000 – $25,000 |
| **Year 1 total** | **$30,000 – $55,000** |

Payment: 50% on SOW signature, 50% on UAT sign-off. Renewal invoiced annually.

---

## 3. Pre-go-live checklist

### Week -2: Discovery

- [ ] Complete `docs/integration/ODOO-FIELD-MAPPING-WORKSHEET.md`
- [ ] Confirm Odoo 17 URL, DB name, service account credentials
- [ ] Install `ipe_connector` module on Odoo staging
- [ ] Network: Odoo → IPE HTTPS (or reverse for on-prem LAN)
- [ ] Identify planner (Arabic), manager, executive sponsor
- [ ] Capture OTD baseline from Odoo or spreadsheet (last 90 days)

### Week -1: Staging

- [ ] Run `scripts/deploy-release1.ps1 -Environment staging`
- [ ] Manual sync: `POST /api/v1/sync/run`
- [ ] Verify ≥80% MOs appear in Control Tower
- [ ] Remediate data quality flags (missing BOM, routing, WC)
- [ ] Test schedule approve → Odoo dates updated
- [ ] Arabic UI review with planner

### Go-live week

- [ ] Production deploy
- [ ] Disable Star Trans SQL overlay (production uses Odoo only)
- [ ] First scheduled sync before 7am production meeting
- [ ] WhatsApp support group created
- [ ] ROI clock starts (90 days)

---

## 4. Data quality acceptance

Full checklist with 10-MO sample, sign-off, MENA notes: **`R1-DATA-QUALITY-ACCEPTANCE-CHECKLIST.md`**.

| Flag | Meaning | Customer action |
|------|---------|-----------------|
| MISSING_BOM | No active BOM for product | Create BOM in Odoo |
| MISSING_ROUTING | No routing operations | Add routing to BOM |
| MISSING_WC | Work center not synced | Verify MRP work centers |
| SYNC_CONFLICT | Odoo changed after IPE approval | Planner reconciles in Resolution |
| MISSING_PRODUCT | Product not in Odoo products | Fix product link |

Target: **≥80% MOs scorable within 30 days** of go-live.

---

## 5. Training agenda

Full curriculum (Planner 3h · Manager 2h · CEO 45m · Arabic-first): **`R1-TRAINING-CURRICULUM.md`**.

### Session A — Planners (3 hours)

1. Login + Arabic toggle
2. Control Tower: reading feasibility scores
3. Data quality badges
4. Resolution Center: comparing scenarios
5. Schedule: refresh, approve, Odoo write-back confirmation

### Session B — Managers + Executive (2 hours)

1. Executive OTD dashboard
2. Approve schedule guardrail (≥85% feasibility)
3. ROI metrics review (`scripts/export-roi-metrics.ps1`)
4. Support escalation path

---

## 6. 90-day success metrics

| Metric | Target |
|--------|--------|
| Planner opens IPE before Excel | ≥4 days/week by week 4 |
| At-risk MOs resolved pre-late | ≥2/month |
| OTD trend | Improving vs week-1 baseline |
| Sync reliability | ≥95% scheduled runs succeed |
| Reference call | CEO agrees to 1 reference |

---

## 7. Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Customer sponsor (Star Trans) | | | |
| Diligent implementation lead | | | |
| Planner champion | | | |
