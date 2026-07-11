# Statement of Work — IPE Release 1 Deployment

**Document Number:** IPE-SOW-ST-001-v1  
**Version:** 1.0  
**Date:** 2026-07-11  
**Status:** Draft — Pending Pricing Confirmation (OQ-7)

---

## Section 1 — Parties

**Provider**

| | |
|---|---|
| Company | Diligent AI Transformation |
| Address | Cairo, Egypt |
| Authorized Representative | Waleed Hewalla |
| Title | Chief Executive Officer |
| Email | waleed@diligent-ai.com |

**Client**

| | |
|---|---|
| Company | Star Trans |
| Address | [STAR TRANS ADDRESS] |
| Authorized Representative | [STAR TRANS CONTACT NAME] |
| Title | [STAR TRANS CONTACT TITLE] |

This Statement of Work ("SOW") is entered into between Diligent AI Transformation ("Provider") and Star Trans ("Client") as of the date of last signature below (the "Effective Date").

---

## Section 2 — Scope of Work

Provider shall deploy IPE Release 1 (the "Platform") on the Client's designated server infrastructure. The deployment shall include the following components:

### 2.1 Odoo 19 ERP Connector

A bidirectional integration between the Client's Odoo 19 ERP system and IPE, implemented via Odoo's XML-RPC API on port 8069. The connector shall synchronize the following data entities:

- **Manufacturing Orders** (`mrp.production`): all orders in `confirmed` or `in_progress` state
- **Bills of Material** (`mrp.bom`): BOM headers and line components
- **Routing Operations** (`mrp.routing.workcenter`): work centre sequences and cycle times
- **Work Centres** (`mrp.workcenter`): capacity, name, calendar
- **Products** (`product.product`): name, internal reference, pricing, unit of measure
- **Customers** (`res.partner` where `customer_rank > 0`): name, contact details
- **Suppliers** (`res.partner` where `supplier_rank > 0`): name, contact details, lead times
- **Demand Orders** (`sale.order.line`): sales demand linked to products
- **Supply Orders** (`purchase.order.line`): purchase supply linked to products
- **Inventory** (`stock.quant`): on-hand quantities by location

**Sync schedule:** Automated every 15 minutes. Each sync run generates data quality flags identifying records that cannot be scored and documenting the reason. Sync conflict detection identifies cases where Odoo data changes after IPE has approved a schedule, and surfaces these for planner reconciliation.

### 2.2 Control Tower

A real-time feasibility dashboard that scores every active Manufacturing Order across five constraint gates:

1. **Demand Validity Gate:** Is there a confirmed sales demand linking to this MO?
2. **BOM Completeness Gate:** Does the product have a complete, active Bill of Materials?
3. **Material Availability Gate:** Are all component materials available on-hand or on confirmed purchase order?
4. **Capacity Loading Gate:** Is the required work centre capacity available on the planned production dates?
5. **Delivery Date Gate:** Can the MO be completed before the customer's required delivery date?

Manufacturing Orders that fail one or more gates are classified as "at-risk" and surfaced in a risk queue sorted by financial impact (revenue at risk, delay cost). Planners can filter by gate failure type, product, customer, or financial impact.

### 2.3 Resolution Center

For each at-risk Manufacturing Order, the Resolution Center generates 2–3 structured resolution scenarios. Each scenario includes:

- A plain-language description of the proposed resolution (e.g., "Split MO into two batches", "Reschedule to next available capacity window", "Expedite purchase order for component X")
- Estimated delivery date impact (days early/late vs. original commitment)
- Estimated cost impact (overtime cost, expedite fee, partial shipment penalty)
- Required action (planner approval)

Scenarios are presented side-by-side for comparison. The planner selects a scenario and approves it, triggering the schedule update and Odoo write-back.

### 2.4 Schedule Engine

A finite-capacity scheduling engine built on Google OR-Tools CP-SAT solver. The engine:

- Respects work centre capacity constraints, shift patterns, and calendar holidays
- Optimises the production sequence across all active Manufacturing Orders
- Generates a Gantt-chart view of the recommended schedule
- Requires explicit planner approval before any schedule changes are applied
- Enforces a guardrail: orders with feasibility score below 50% cannot be approved without a documented resolution scenario

### 2.5 OTD Analytics Dashboard

An on-time delivery measurement and trend dashboard providing:

- Rolling OTD percentage (current week, current month, trailing 90 days)
- Root cause breakdown: delay reasons categorised by gate failure type
- Cost-of-chaos metric: estimated revenue impact of late deliveries
- OTD baseline capture: on-go-live, a baseline OTD percentage is captured from Odoo historical data (last 3–6 months) to establish a pre-IPE benchmark

### 2.6 Arabic User Interface

Full Arabic language support across all planning screens, including:

- Control Tower (risk queue, feasibility scores, KPI tiles)
- Resolution Center (scenario cards, cost/delivery impact)
- Schedule (Gantt chart labels, approval workflow)
- Navigation, login page, and system alerts
- Right-to-left (RTL) layout throughout
- Language toggle available on all screens — users may switch between Arabic and English at any time

### 2.7 Odoo Write-Back

When a planner approves a resolution scenario or schedule, the approved dates are automatically written back to the corresponding `mrp.production` record in Odoo:

- `date_start` is updated to the approved planned start date
- `date_finished` is updated to the approved planned end date
- An Odoo chatter note is added documenting that IPE updated the dates and the approving user

### 2.8 Excluded from This SOW

The following features are not included in this Release 1 deployment and are available as a Release 2 upgrade:

- **AI Copilot:** Natural-language query interface for planning data
- **Demand Sensing:** Forecast generation from Odoo sales history using ML models
- **Scenario Workbench:** What-if analysis across multiple planning scenarios with version management
- **S&OP Engine:** Consensus planning with multi-stakeholder collaboration and sign-off workflow

---

## Section 3 — Deliverables

| # | Deliverable | Acceptance Criteria | Timeline |
|---|-------------|---------------------|----------|
| D1 | IPE platform deployed and all R1 services healthy | All services return HTTP 200 on `/healthz`; web UI accessible via browser on configured port; database migrations at head | End of Week 1 |
| D2 | Odoo 19 connector configured and performing live sync | First full sync completes without error; Manufacturing Orders visible in Control Tower with correct product names and quantities; sync log shows ≥1 successful run | End of Week 1 |
| D3 | Data quality review completed | All data quality flags reviewed with Client IT; blocking issues (missing BOMs, missing routings, missing work centres) resolved in Odoo; ≥70% of active MOs scorable | End of Week 2 |
| D4 | Feasibility scoring validated by planner | Client planner confirms that feasibility scores are meaningful for their actual Manufacturing Orders; planner can identify genuine at-risk orders in the Control Tower queue | End of Week 2 |
| D5 | Arabic UI verified by planner | Planner completes full daily workflow (login → Control Tower → Resolution Center → Schedule → approve) entirely in Arabic; all UI text is correctly translated and RTL layout renders correctly | End of Week 2 |
| D6 | UAT sessions completed (3 sessions) | All three UAT sessions completed (see Section 3 for session descriptions); zero Priority 0 issues outstanding; planner and Operations Director have signed UAT acceptance form | End of Week 3 |
| D7 | Training delivered | 4-hour training session delivered per `docs/implementation/R1-TRAINING-CURRICULUM.md`; planner can independently triage at-risk MOs, review resolution scenarios, approve a schedule, and verify Odoo write-back; planner receives quick-reference card | End of Week 3 |
| D8 | Production go-live | Planner uses IPE daily on production Odoo data; first production triage session completed with Diligent on standby; planner and Operations Director have signed go-live confirmation | End of Week 4 |
| D9 | OTD baseline documented | Pre-IPE OTD percentage captured from Odoo historical data (last 3–6 months); baseline report signed by Operations Director; target used for 30-day ROI measurement | End of Week 4 |

---

## Section 4 — Implementation Timeline

**Day 0:** SOW signed by both parties. Implementation clock starts.

### Week 1: Deployment and First Sync (Days 1–5)

| Days | Activity |
|------|----------|
| 1–2 | Provider copies deployment package to Client server; configures `.env` file (Odoo URL, credentials, JWT secret, DB connection); runs `docker compose up -d`; executes database migrations; verifies all services healthy via `scripts/star-trans-validate.ps1` |
| 3–4 | Provider configures Odoo connector with Client IT; triggers first full sync; reviews sync logs for errors; reviews data quality flags; documents blocking issues for Week 2 resolution |
| 5 | First planner review: Provider walks planner through Control Tower; confirms product names, MO data, and quantities are correct; confirms Arabic language toggle works; documents any field mapping issues |

**D1 and D2 acceptance review at end of Week 1.**

### Week 2: Calibration and Arabic QA (Days 6–10)

| Days | Activity |
|------|----------|
| 6–7 | Provider works with Client IT to resolve data quality flags (missing BOMs, null routings, undefined work centres); Client IT corrects data in Odoo; Provider triggers re-sync and verifies scores improve |
| 8–9 | Arabic QA: planner walks through full workflow in Arabic; Provider logs any translation issues or RTL rendering problems; critical Arabic issues resolved same-day if possible |
| 10 | Pre-UAT verification: 5+ consecutive scheduled syncs without failure; sync conflict detection tested; write-back tested on staging data; UAT schedule confirmed with planner and Operations Director |

**D3, D4, and D5 acceptance review at end of Week 2.**

### Week 3: UAT and Training (Days 11–15)

| Days | Activity |
|------|----------|
| 11 | **UAT Session 1 — Planner Workflow (2 hours):** Full workflow in Arabic: login → Control Tower → identify at-risk MO → Resolution Center → compare scenarios → approve → verify Schedule; acceptance criterion: planner completes flow independently |
| 12 | **UAT Session 2 — Executive View (1 hour):** OTD Dashboard: review OTD trend, delay root causes, cost-of-chaos metric; acceptance criterion: Operations Director finds the data useful and actionable |
| 13 | **UAT Session 3 — Write-Back and Edge Cases (1 hour):** Approve schedule in IPE → verify Odoo MO updated → verify chatter message; test graceful handling of Odoo unreachable scenario; test MO deleted in Odoo scenario |
| 14 | **Training Session (4 hours):** Full training per `R1-TRAINING-CURRICULUM.md`; covers login, Control Tower, Resolution Center, Schedule, OTD Dashboard, Arabic toggle, troubleshooting; planner receives Arabic quick-reference card |
| 15 | **UAT sign-off:** Review UAT issue log; all P0 items resolved; planner and Operations Director sign UAT acceptance form; go-live date confirmed |

**D6 and D7 acceptance review at end of Week 3.**

### Week 4: Go-Live and Baseline (Days 16–20)

| Days | Activity |
|------|----------|
| 16 | **Production go-live:** Planner switches to daily production use; first morning triage using live Odoo data; Provider on standby via WhatsApp from 7:00am |
| 17–19 | **Intensive support:** Provider daily WhatsApp check-in; monitors sync health; resolves P1 issues immediately; collects usage metrics (login count, MOs scored, scenarios viewed) |
| 20 | **OTD baseline capture:** Provider runs OTD baseline query on Odoo historical data; Operations Director reviews and signs baseline report; Provider issues implementation invoice |

**D8 and D9 acceptance review at end of Week 4.**

### Post-Go-Live: 30-Day Monitoring (Days 21–50)

| Cadence | Activity |
|---------|----------|
| Weekly | Planner check-in (15 minutes via WhatsApp): adoption metrics, open issues |
| Weekly | Provider sync health review; flag any degradation |
| Day 30 | OTD measurement: compare current OTD% to baseline; document improvement |
| Day 30 | Customer satisfaction interview: CEO and Operations Director (30 minutes); target ≥7/10 satisfaction |
| Day 30 | Begin ROI case study for reference programme |

---

## Section 5 — Pricing

| Component | Amount | Payment Trigger |
|-----------|--------|-----------------|
| Annual Platform Licence | [AMOUNT — to be confirmed by Waleed] | Invoiced at go-live (Day 16); annual renewal thereafter on go-live anniversary |
| Implementation Fee (one-time) | [AMOUNT — to be confirmed by Waleed] | 50% at SOW signature (Day 0); 50% at production go-live (Day 16) |
| **Total Year 1** | [LICENCE + IMPLEMENTATION] | Per payment schedule above |
| **Year 2+ (annual renewal)** | [LICENCE AMOUNT] | Invoiced 30 days before anniversary date |

**Payment terms:** Net 30 from invoice date.

**Currency:** United States Dollars (USD). If Client requires billing in Egyptian Pounds (EGP), invoices shall be converted at the official Central Bank of Egypt spot rate on the invoice date. An annual FX adjustment clause applies at each licence renewal: if EGP/USD rate has moved more than 10% since the prior invoice, the EGP amount is adjusted pro-rata to hold the USD equivalent constant.

**Late payment:** Invoices unpaid after 45 days accrue interest at 1.5% per month. Provider may suspend services after 60 days of non-payment with 7 days written notice.

---

## Section 6 — Support Terms

### 6.1 Support Channels

- **Primary:** Dedicated WhatsApp group — `IPE — Star Trans Support` — invite-only, includes Client planner, Client IT contact, and Diligent implementation manager
- **Secondary:** Email — `support@diligent-ai.com` — for formal requests, invoice queries, and escalations
- **Emergency (P0 only):** Phone call when WhatsApp unanswered after 30 minutes during business hours

### 6.2 Business Hours

Sunday – Thursday, 09:00 – 18:00 Cairo time (UTC+2 winter / UTC+3 summer). Support is not included on Fridays, Saturdays, or Egyptian public holidays; best-effort P0 response is provided off-hours.

### 6.3 SLA Response and Resolution Targets

| Priority | Definition | Response Target | Resolution Target |
|----------|------------|-----------------|-------------------|
| **P0 — Critical** | System completely down before production meeting; sync failed and data is stale; all users cannot login | 2 hours | 4 hours |
| **P1 — High** | Core feature broken for planner (cannot approve schedule, cannot view feasibility scores); login broken for all users | Same business day | 1 business day |
| **P2 — Normal** | Single MO showing incorrect data; translation issue on one screen; minor UI rendering problem | Next business day | 1 week |
| **P3 — Question** | "How do I...?" usage question; training reinforcement; report request | Same or next business day | 1 week |

### 6.4 Included in Licence

Support is included in the annual Platform Licence at no additional charge. There is no separate support fee.

### 6.5 Out of Scope for Support

Support does not cover: Client's Odoo server maintenance or uptime; Client's network infrastructure; Client's IT hardware; custom development requests (quoted separately); changes to Odoo data (BOM, routing, work centre setup) — these are Client responsibilities.

---

## Section 7 — Customer Responsibilities

Client acknowledges that the following resources and access are required for a successful deployment and are the Client's sole responsibility to provide:

### 7.1 Server Infrastructure

Client shall provision and maintain a server meeting the following minimum specification:

| Requirement | Minimum Specification |
|-------------|----------------------|
| RAM | 8 GB |
| CPU | 4 vCPU |
| Storage | 100 GB SSD |
| Operating System | Ubuntu 22.04 LTS or Windows Server 2022 |
| Container Runtime | Docker 24.0+ with Docker Compose v2 |
| Network | Static IP or stable DNS; HTTPS accessible from planner workstations |
| Odoo Connectivity | Network path from IPE server to Odoo server on port 8069 |

### 7.2 Odoo Access

Client shall provide, before Week 1 Day 1:

- Odoo 19 staging URL (format: `http://[host]:8069`)
- Odoo 19 production URL
- Database name
- API service account username and password with:
  - **Read access** to: `mrp`, `sale`, `purchase`, `stock`, `product`, `res.partner` models
  - **Write access** to: `mrp.production` (for schedule write-back)
- Confirmation that XML-RPC is enabled on port 8069

### 7.3 People

Client shall make available:

- **Planner champion:** Approximately 8 hours total over Weeks 2–3 for Arabic QA review, UAT sessions (3 × 1–2 hours), and 4-hour training
- **Operations Director:** Approximately 1.5 hours total for UAT Session 2 (1 hour executive view) and go-live sign-off (30 minutes)
- **IT contact:** Available during Week 1 for connector configuration and data quality issue resolution; response within same business day for data correction requests

### 7.4 Network and Security

Client is responsible for ensuring:

- Network connectivity between the IPE server and the Odoo server throughout the contract term
- Firewall rules permitting the IPE server to reach Odoo on port 8069
- Notification to Diligent at least 48 hours before any planned Odoo server maintenance, IP address change, or credential rotation that would affect the connector

---

## Section 8 — Data and Intellectual Property

### 8.1 IPE Platform

IPE software, source code, models, algorithms, and all associated intellectual property remain the exclusive property of Diligent AI Transformation. Client receives a non-exclusive, non-transferable licence to use the Platform during the term of this SOW.

### 8.2 Customer Data

All data originating from Client's Odoo system (manufacturing orders, bills of material, products, customers, suppliers, inventory records, and any derivative data) remains the exclusive property of Client. Provider has no claim to Client data.

### 8.3 Data Storage and Transmission

Client data is stored exclusively on the Client-provided server specified in Section 7.1. Client data is not transmitted to Diligent servers, cloud infrastructure, or any third party, except as described in Section 8.4.

### 8.4 AI API Data Protection

When AI Copilot features are enabled (Release 2 only — not included in this SOW), certain planning queries may be processed by the Anthropic Claude API under Anthropic's enterprise data protection agreement. Under this agreement, Client data is not used to train Anthropic's models. No AI features in Release 1 transmit Client data externally.

### 8.5 Confidentiality

Each party agrees to keep the other's Confidential Information strictly confidential and not to disclose it to third parties without prior written consent, except as required by law. "Confidential Information" includes pricing, technical architecture, manufacturing data, and customer lists.

---

## Section 9 — Acceptance and Go-Live

### 9.1 Go-Live Confirmation

Production go-live is formally confirmed when all of the following conditions are met:

1. All nine deliverables (D1–D9) have been reviewed and accepted
2. Zero Priority 0 (P0) issues are outstanding
3. Client planner has signed the UAT acceptance form
4. Client Operations Director has signed the UAT acceptance form
5. Go-live confirmation email sent by Diligent and acknowledged by Client

### 9.2 Acceptance Process

For each deliverable, Provider notifies Client that the deliverable is ready for review. Client has 3 business days to accept or raise issues. If no response is received within 3 business days, the deliverable is deemed accepted.

### 9.3 P0 Issues and Go-Live Delay

If UAT reveals Priority 0 issues, go-live is delayed until all P0 items are resolved. Such delay does not affect the pricing in Section 5. The implementation fee milestone (50% at go-live) remains tied to actual go-live date, not planned go-live date.

### 9.4 Unsuccessful Go-Live

If the deployment cannot achieve go-live acceptance within 8 weeks of the Effective Date due to issues solely attributable to Provider, Provider shall provide a credit of [AMOUNT — to be confirmed by Waleed] against the next invoice, as Client's sole remedy.

---

## Section 10 — Term and Renewal

### 10.1 Initial Term

This SOW commences on the Effective Date and has an initial term of twelve (12) months from the production go-live date.

### 10.2 Renewal

This SOW shall automatically renew for successive twelve (12) month terms unless either party provides written notice of non-renewal at least sixty (60) days before the end of the then-current term.

### 10.3 Price Adjustment at Renewal

Provider may adjust the annual Platform Licence fee at renewal by up to ten percent (10%) with sixty (60) days written notice before the renewal date.

### 10.4 Termination for Cause

Either party may terminate this SOW with thirty (30) days written notice if the other party materially breaches the SOW and fails to cure the breach within the notice period.

---

## Section 11 — Limitation of Liability

### 11.1 Liability Cap

Provider's total aggregate liability to Client under or in connection with this SOW, whether arising in contract, tort (including negligence), or otherwise, shall not exceed the total fees paid by Client to Provider in the twelve (12) months preceding the event giving rise to the claim.

### 11.2 Exclusion of Consequential Damages

Neither party shall be liable to the other for any indirect, special, incidental, consequential, or punitive damages, including but not limited to loss of profits, loss of revenue, loss of business opportunity, or loss of goodwill, even if advised of the possibility of such damages.

### 11.3 Force Majeure

Neither party shall be liable for delays or failure to perform obligations under this SOW caused by events beyond that party's reasonable control, including but not limited to acts of God, natural disasters, war, civil unrest, government action, pandemic, or failure of third-party infrastructure (including Odoo cloud infrastructure, internet service provider outages, or Anthropic API outages). The affected party shall notify the other party promptly and resume performance as soon as reasonably practicable.

### 11.4 Exceptions

The liability cap in Section 11.1 does not apply to: (a) damages arising from a party's fraud or wilful misconduct; (b) Client's obligation to pay fees owed under Section 5; (c) breach of confidentiality obligations under Section 8.5.

---

## Section 12 — Signatures

This Statement of Work is binding upon execution by authorised representatives of both parties.

| | **Diligent AI Transformation (Provider)** | **Star Trans (Client)** |
|---|---|---|
| **Name** | Waleed Hewalla | [NAME] |
| **Title** | Chief Executive Officer | [TITLE] |
| **Date** | _________________ | _________________ |
| **Signature** | _________________ | _________________ |

---

*This document is subject to final legal review. Pricing fields marked [AMOUNT — to be confirmed by Waleed] must be completed before the document is sent to Client. Contact: waleed@diligent-ai.com*
