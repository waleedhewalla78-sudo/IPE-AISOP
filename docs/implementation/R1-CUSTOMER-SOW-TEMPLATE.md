# Statement of Work — IPE Release 1 Implementation

**Template version:** 1.0  
**Product:** Intelligent Planning Engine (IPE) — Release 1  
**Market:** MENA mid-market discrete manufacturing  
**Effective upon signature by both parties**

---

## Parties

| | |
|---|---|
| **Provider** | Diligent [Legal entity name] · [Address] · [Tax ID] |
| **Customer** | [Company legal name] · [Address] · [Country] |
| **Primary contact** | [Name, title, email, mobile/WhatsApp] |
| **Executive sponsor** | [CEO / Operations Director name] |

---

## 1. Background and purpose

**Customer** operates a **discrete manufacturing** facility in the **MENA region** (make-to-order or make-to-stock, batch production, multi-stage routing). Planning today relies primarily on **Odoo MRP** supplemented by **Excel spreadsheets** for feasibility and daily production meetings.

**Provider** delivers **IPE Release 1**: a feasibility-first planning layer that reads live data from Customer’s **Odoo 17** instance, surfaces at-risk manufacturing orders (MOs) in a **Control Tower**, offers structured resolution scenarios, and writes approved schedules back to Odoo.

This SOW defines scope, deliverables, acceptance criteria, timeline, pricing, support model, and responsibilities for a **45-day proof-of-value period** followed by a **12-month subscription**.

---

## 2. Scope summary

### 2.1 In scope

| # | Deliverable | Description |
|---|-------------|-------------|
| D1 | **Odoo connector** | Scheduled sync (every 15 minutes): products, work centers, BOMs, manufacturing orders; audit log and data quality flags |
| D2 | **Control Tower** | Arabic-first planner queue: feasibility scores, at-risk MOs, sync status, data quality badges |
| D3 | **Resolution Center** | Scenario comparison and selection for at-risk orders |
| D4 | **Schedule write-back** | Approved plan dates written to Odoo `mrp.production` |
| D5 | **Executive dashboard** | On-time delivery (OTD) trend and baseline (English or Arabic per user preference) |
| D6 | **Deployment** | Single VM (8 GB RAM): **☐ Diligent-managed cloud** · **☐ Customer on-premises** |
| D7 | **Training** | Three role-based sessions (see `R1-TRAINING-CURRICULUM.md`) |
| D8 | **Support** | WhatsApp + phone, business hours (see §8) |
| D9 | **Documentation** | Implementation playbook, field mapping worksheet, customer support guide |

### 2.2 Explicitly out of scope (Phase 2+)

- AI Copilot / natural language assistant  
- Demand sensing, scenario sandbox, supply network planning  
- Quality, sustainability, or advanced analytics hubs  
- SAP Business One, Microsoft Dynamics, or non-Odoo ERP connectors  
- Single sign-on (Keycloak / Azure AD)  
- Automated billing (Stripe)  
- Custom Odoo module development beyond `ipe_connector` install  
- Historical data migration from legacy Excel (beyond OTD baseline capture)

---

## 3. Customer environment assumptions

| Item | Requirement |
|------|-------------|
| ERP | Odoo **17.0** with modules: `mrp`, `stock`, `purchase`, `sale` |
| Active MOs | ≤ 200 in planning horizon (typical mid-market) |
| Network | HTTPS between Odoo and IPE (cloud) or LAN (on-prem) |
| Service account | Odoo user with MRP read + write on manufacturing orders |
| Planners | Primary UI language: **Arabic** (English optional) |
| Production meeting | Typically **daily, before 08:00** local time — sync must succeed beforehand |
| Users licensed | ☐ ___ planners · ☐ ___ managers · ☐ ___ executives (read-only) |

---

## 4. Implementation timeline

| Phase | Duration | Activities | Exit criteria |
|-------|----------|------------|---------------|
| **Kickoff** | Week 0 | Sign SOW; assign contacts; create WhatsApp group | Kickoff complete |
| **Discovery** | Weeks 1–2 | Field mapping worksheet; Odoo staging access; install `ipe_connector` | Worksheet signed |
| **Staging** | Weeks 3–4 | Deploy IPE staging; first sync; data quality remediation | ≥80% MOs scorable (see checklist) |
| **UAT** | Weeks 5–6 | Planner + manager testing; Arabic UX review; write-back test | UAT sign-off (Exhibit B) |
| **Go-live** | Week 7 | Production deploy; disable demo overlays; first 7am sync verified | Go-live checklist complete |
| **Hypercare** | Weeks 7–10 | Daily WhatsApp check-ins; sync monitoring | No P0 incidents >48h |
| **ROI period** | Days 1–90 post go-live | Adoption and OTD tracking | ROI review (Exhibit C) |

**Target go-live date:** _______________  
**90-day ROI review date:** _______________

---

## 5. Roles and responsibilities

### 5.1 Provider (Diligent)

- Deploy and maintain IPE Release 1 stack  
- Configure Odoo connector and sync schedule  
- Remediate platform defects per SLA  
- Deliver training sessions  
- First-line support via WhatsApp and phone  
- Weekly proactive sync health check (Mondays before customer production meeting)

### 5.2 Customer

- Provide Odoo staging and production access (URL, database, service account)  
- Install `ipe_connector` module on Odoo (IT)  
- Complete and sign field mapping worksheet  
- Assign planner champion, manager, and executive sponsor  
- **Remediate data quality issues in Odoo** (missing BOMs, routings, work centers) — not a platform bug  
- Participate in UAT and sign acceptance  
- Ensure planners use Arabic UI as primary workflow during ROI period  

### 5.3 RACI (key activities)

| Activity | Provider | Customer IT | Customer Planner | Customer Exec |
|----------|----------|-------------|------------------|---------------|
| Odoo credentials | C | R/A | I | I |
| Field mapping | C | R | A | I |
| Data quality fixes | I | C | R/A | I |
| UAT testing | C | I | R/A | I |
| OTD baseline | C | I | C | A |
| Schedule approve in production | I | I | R/A | I |
| ROI review | R | I | C | A |

*R = Responsible · A = Accountable · C = Consulted · I = Informed*

---

## 6. Acceptance criteria

### 6.1 UAT sign-off (required for final payment)

All items in **Exhibit B — UAT Acceptance Checklist** must pass, including:

1. MOs created or updated in Odoo appear in Control Tower within **20 minutes**  
2. **≥80%** of active MOs receive a feasibility score (not “Cannot score”)  
3. Planner completes end-to-end flow: at-risk MO → Resolution → schedule approve → Odoo dates updated  
4. Arabic Control Tower usable by planner champion without English fallback for daily tasks  
5. Sync reliability **≥95%** over 7 consecutive days on staging or production  
6. Customer support guide acknowledged by planner and IT contact  

Detailed data quality criteria: `R1-DATA-QUALITY-ACCEPTANCE-CHECKLIST.md`

### 6.2 90-day ROI success metrics (commercial review, not payment gate)

| Metric | Target |
|--------|--------|
| Planner opens IPE before Excel | ≥4 days/week by week 4 |
| At-risk MOs resolved before late | ≥2 per month |
| OTD trend | Improving vs week-1 baseline |
| Sync reliability | ≥95% scheduled runs succeed |
| Reference call | Executive agrees to 1 reference call with prospect |

---

## 7. Fees and payment

| Item | Amount (USD) | Notes |
|------|--------------|-------|
| **Annual subscription** (12 months) | $________ | Includes license, updates, support per §8 |
| **One-time implementation** | $________ | Discovery, deploy, training, hypercare |
| **On-premises setup surcharge** (if applicable) | $________ | VM hardening, VPN, extra visit |
| **Year 1 total** | $________ | |

**Payment schedule:**

| Milestone | % | Amount | Trigger |
|-----------|---|--------|---------|
| Upon SOW signature | 50% | $________ | Signed SOW + PO |
| Upon UAT sign-off | 50% | $________ | Exhibit B signed |
| Renewal (Year 2+) | 100% annual | $________ | 30 days before anniversary |

**Currency:** USD unless otherwise agreed. **Tax/VAT:** per local law ([Egypt VAT / other]: ________).

---

## 8. Support model — WhatsApp and phone

### 8.1 Channels

| Channel | Use | Hours |
|---------|-----|-------|
| **WhatsApp group** | Primary — screenshots, quick questions, sync alerts | Sun–Thu 08:00–18:00 **Cairo** (adjust: ________) |
| **Phone** | Urgent — sync failure before production meeting | Same hours |
| **Email** | Contracts, formal requests, attachments | Business days, 24h response |

**WhatsApp group name:** `IPE — [Customer short name] Support`  
**Provider L1 contact:** [Name, mobile]  
**Customer contacts in group:** Planner champion, IT contact, optional manager

### 8.2 Service levels

| Severity | Definition | Response target | Resolution target |
|----------|------------|-----------------|-------------------|
| **P0 — Critical** | Sync failed before daily production meeting (<08:00); no current MO data | **2 hours** | Same business day or communicated Excel fallback |
| **P1 — High** | Sync down >4h during business hours; write-back failure blocking approve | Same business day | 1 business day |
| **P2 — Medium** | Single MO wrong score; UI issue on non-critical screen | Next business day | Next release or workaround |
| **P3 — Low** | Cosmetic, feature request, training question | 2 business days | Backlog |

**Not covered under SLA:** Odoo server outages, customer network failures, missing BOMs/routings in Odoo (data quality — customer fixes in Odoo).

### 8.3 What Customer sends on WhatsApp (templates in customer support guide)

- Screenshot of sync bar (red/stale)  
- Odoo MO reference number  
- Time issue was noticed  
- For login issues: browser and whether Arabic or English selected  

---

## 9. Arabic-first planner experience

Release 1 delivers **Arabic as the default planner language**:

- Right-to-left (RTL) layout on Control Tower, navigation, and alerts  
- Language switcher (Arabic ↔ English) — planners should stay in Arabic for daily use  
- Executive views may use English per sponsor preference  
- Training Session A is delivered **in Arabic** (or bilingual if team requires)  

Provider commits to fixing **P1 Arabic layout defects** on in-scope screens before UAT sign-off.

---

## 10. Data ownership and security

- **Customer data** remains Customer property; Provider processes it solely to deliver the service  
- Odoo credentials stored encrypted at rest (production); staging may use secured config per agreement  
- No Customer production data used for other customers or model training  
- Backups: daily DB snapshot on IPE VM; retention 7 days (cloud) or per Customer policy (on-prem)  
- **Data residency:** ☐ Diligent cloud ([region]) · ☐ Customer on-prem — data does not leave Customer network  

---

## 11. Change control

Changes to scope (additional ERP modules, custom Odoo fields, extra sites) require a **Change Request** with written estimate and timeline. Minor mapper patches for agreed custom fields in the signed field mapping worksheet are included during implementation.

---

## 12. Term and termination

- **Initial term:** 12 months from go-live date  
- **Renewal:** Automatic unless either party gives **60 days** written notice  
- **Termination for convenience:** Either party with 60 days notice after initial term  
- **Termination for cause:** Material breach uncured after 30 days written notice  
- Upon termination: Provider assists export of Customer data; connector deactivated; no refund of elapsed subscription  

---

## 13. Exhibits

| Exhibit | Document |
|---------|----------|
| **A** | `docs/integration/ODOO-FIELD-MAPPING-WORKSHEET.md` (completed) |
| **B** | UAT Acceptance Checklist (below + `R1-DATA-QUALITY-ACCEPTANCE-CHECKLIST.md`) |
| **C** | 90-day ROI review template (`converge.md` §90-day) |
| **D** | `docs/implementation/R1-TRAINING-CURRICULUM.md` |
| **E** | `docs/runbooks/R1-CUSTOMER-SUPPORT-GUIDE.md` |

---

## Exhibit B — UAT acceptance checklist (summary)

| # | Criterion | Pass | Date |
|---|-----------|------|------|
| B1 | Staging/production deploy complete | ☐ | |
| B2 | First scheduled sync before 07:00 local verified | ☐ | |
| B3 | ≥80% MOs scorable | ☐ | |
| B4 | Write-back to Odoo confirmed on 3 test MOs | ☐ | |
| B5 | Planner Arabic UX signed off | ☐ | |
| B6 | WhatsApp support group active | ☐ | |
| B7 | Training Sessions A + B + C completed | ☐ | |
| B8 | Data quality acceptance checklist signed | ☐ | |

---

## Signatures

By signing below, both parties agree to the terms of this Statement of Work.

| | Provider | Customer |
|---|----------|----------|
| **Name** | | |
| **Title** | | |
| **Date** | | |
| **Signature** | | |

---

*Template: IPE Release 1 · MENA mid-market discrete manufacturing · Odoo 17 · Arabic-first planner UX*
