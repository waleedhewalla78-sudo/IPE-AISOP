# IPE Release 1 — Your Deployment

**Prepared for:** Star Trans — Electrical Transformer Technology  
**Prepared by:** Diligent AI Transformation  
**Date:** 2026-07-11  
**Contact:** Waleed Hewalla — waleed@diligent-ai.com

---

## Platform Overview

IPE (Intelligent Planning Engine) is an AI-assisted manufacturing planning platform that connects directly to your Odoo ERP. It scores every active manufacturing order for feasibility before your morning production meeting, surfaces at-risk orders with structured resolution options, and updates your Odoo schedule automatically when your planner approves. The entire interface is available in Arabic.

---

## Features Included in Your Deployment

### Control Tower

Every active manufacturing order in your Odoo system is scored for feasibility across five constraint gates — material availability, production capacity, bill of materials completeness, confirmed demand, and delivery date. At-risk orders appear in a priority queue sorted by financial impact, so your planner sees the most important problems first. The data refreshes automatically every 15 minutes from your Odoo.

### Resolution Center

When an order is identified as at-risk, IPE generates 2–3 structured resolution scenarios. Each scenario shows the estimated impact on delivery date and cost side by side, so your planner can make an informed decision in minutes rather than spending hours investigating in Odoo. The planner selects a scenario and approves it — IPE takes care of the rest.

### Schedule Engine

IPE uses mathematical optimisation (Google OR-Tools) to generate a finite-capacity production schedule that respects your work centre capacity and shift patterns. Your planner reviews the proposed schedule and approves it — no changes happen automatically without planner approval.

### OTD Analytics

A dashboard tracking your on-time delivery performance: weekly OTD percentage, trend over the last 90 days, root cause breakdown by delay type, and a cost-of-chaos estimate showing the financial impact of late orders. At go-live, a baseline OTD percentage is captured from your Odoo historical data to measure improvement over time.

### Odoo Connector

A live, bidirectional integration to your Odoo 19 system. IPE reads manufacturing orders, bills of material, routings, work centres, products, inventory, sales orders, and purchase orders every 15 minutes. Approved schedules are automatically written back to your Odoo manufacturing orders, including a chatter note documenting who approved and when.

### Write-Back

When your planner approves a resolution scenario or production schedule, IPE automatically updates the planned start and finish dates on the corresponding Odoo manufacturing order. Your Odoo remains the system of record — IPE makes Odoo smarter, it does not replace it.

### Arabic Interface

The full planning interface is available in Arabic with right-to-left layout: Control Tower, Resolution Center, Schedule, OTD Analytics, navigation, and login. Your planner can switch between Arabic and English at any time using the language toggle in the top navigation bar.

---

## Available as a Future Upgrade

The following features are not included in this deployment and are available as a Release 2 upgrade:

- **AI Copilot** — Ask questions about your planning data in natural language (Arabic or English): "Which orders are at risk this week?" "What caused the OTD drop in June?"
- **Demand Sensing** — Forecast generation from your Odoo sales history using machine learning models
- **Scenario Workbench** — What-if analysis across multiple planning scenarios with version management and comparison
- **S&OP Engine** — Sales and Operations Planning with multi-stakeholder review, consensus workflow, and plan version history

---

## What You Need to Provide

**Server:** A server with at least 8 GB RAM, 4 CPU cores, 100 GB SSD storage, and Docker 24 installed. Ubuntu 22.04 or Windows Server 2022. The server must have network access to your Odoo system.

**Odoo access:** An API service account with read access to your Odoo manufacturing, sales, purchasing, inventory, and product data, plus write access to manufacturing orders for schedule updates. Odoo must be accessible from the IPE server on port 8069.

**Planner time:** Approximately 8 hours total over the implementation period — 3 UAT sessions and a 4-hour training session.

---

## Implementation Timeline

| Week | Activity |
|------|----------|
| Week 1 | IPE deployed; first Odoo sync completed; your manufacturing orders visible |
| Week 2 | Data quality issues resolved; feasibility scores validated; Arabic UI confirmed |
| Week 3 | 3 UAT sessions completed; 4-hour training delivered |
| Week 4 | Production go-live; daily planner use begins; OTD baseline captured |
| Days 21–50 | Intensive monitoring; Day 50 OTD measurement vs. baseline |

---

## Support

**Channel:** Dedicated WhatsApp group — "IPE — Star Trans Support"  
**Hours:** Sunday–Thursday, 09:00–18:00 Cairo time  
**Languages:** Arabic and English  
**Response:** Same business day for all issues; P0 (system down) within 2 hours  
**Cost:** Included in annual licence — no separate support fee

**Contact:** Waleed Hewalla, CEO  
**Email:** waleed@diligent-ai.com  
**Company:** Diligent AI Transformation, Cairo, Egypt
