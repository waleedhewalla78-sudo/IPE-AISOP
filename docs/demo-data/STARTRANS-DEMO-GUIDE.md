# Star Trans — 60-Minute Client Demo Guide

> **Extended session (180 min, hybrid + Copilot + mixed audience):**  
> See **[STARTRANS-DEMO-180MIN-HYBRID-RUNBOOK.md](./STARTRANS-DEMO-180MIN-HYBRID-RUNBOOK.md)**  
> Prep: `.\scripts\prepare-startrans-demo-hybrid.ps1`

**Client**: Star Trans — Electrical Transformer Technology  
**Audience**: Ops planners + C-suite  
**Environment**: Local laptop · http://localhost:8082  
**Login**: `Ahmed@nour` / `admin`

---

## T-90 preparation

```powershell
cd E:\AISOP\ipe
.\scripts\prepare-startrans-demo.ps1
# Separate terminal:
cd apps\web; npm run dev
```

Confirm `docs/demo-data/startrans-pre-demo.txt` shows **32/32 PASS**.

Convert schedule CSV to xlsx (Excel: open `docs/demo-data/startrans/project-plan-startrans-w12.csv` → Save As `.xlsx`).

---

## Opening (5 min) — both audiences

**Say:** “Star Trans runs long-lead transformer builds — copper, CRGO steel, test bay capacity. IPE gives one view from demand through feasibility, resolution, schedule, and AI-assisted planning — with humans in control (shadow mode).”

**Show:** Login → **Planning Hub → Dashboard** (`/planning/dashboard`). Point out MO-ST-001 on Control Tower tab — tenant is branded Star Trans in data (sidebar still shows “IPE”).

---

## Act 1: Problem visibility (10 min) — ops + exec

### Control Tower (`/planning/control-tower`)

- **MO-ST-001** — Distribution Transformer 500 kVA — score ~52 — **material_shortage** (copper wire)
- **MO-ST-007** — score ~45 — CRGO steel + test capacity
- KPI cards: avg feasibility, orders at risk

**C-suite line:** “Red rows are revenue at risk — scored before the shift starts.”

### Resolution Center (`/planning/resolution`)

Select **MO-ST-001**. Show 3 scenarios:

1. Expedite copper PO — Midwest Copper Supply  
2. Substitute wire gauge  
3. Split coil batches  

**Ops line:** “Each option has cost vs delivery impact — planner chooses, AI recommends.”

---

## Act 2: Plan & replan (10 min) — ops focus

### Schedule (`/planning/schedule`)

1. Click **Refresh** — OR-Tools Gantt (Winding → Core & Coil → Test Bay)
2. Click **Upload Project Plan** (button top-right — panel is collapsed by default)
3. Choose **Create new plan**, select `project-plan-startrans-w12.xlsx`, click **Upload New Plan**
4. Under **View**, select **Uploaded project plan** → pick `PLAN-STARTRANS-W12` from dropdown

**Say:** “When ERP sync is delayed, planners upload this week’s Excel plan — same workflow as MS Project exports.”

---

## Act 3: v8 planning loop (10 min) — ops

| Page | Action | Talking point |
|------|--------|---------------|
| **Demand** (`/planning/demand`) | Run sense cycle | Statistical forecast from utility order history |
| **Scenarios** (`/planning/scenarios`) | Create “CRGO delay +5d” → Simulate | Sandbox before committing |
| **Supply** (`/supply-chain/supply-planning`) | View network | Chicago, Houston, Dallas DC, Minneapolis winding |
| **Orders** (optional) | Create order | ATP against FG stock |

---

## Act 4: Copilot live (8 min) — **required**

Open **AI & Governance → Copilot**. Use exact queries from [STARTRANS-COPILOT-CHEATSHEET.md](./STARTRANS-COPILOT-CHEATSHEET.md).

**C-suite line:** “Shadow mode — Copilot reads live Star Trans data; planners approve every action.”

---

## Act 5: Executive view (8 min) — C-suite

| Page | Highlight |
|------|-----------|
| **Executive** (`/command-center/executive`) | OTD trend, delay by cause (material, capacity, equipment) |
| **War Room** (`/command-center/war-room`) | Active alerts, recovery options, cost of chaos |

---

## Act 6: Differentiators + close (7 min)

| Page | Highlight |
|------|-----------|
| **Sustainability** (`/ai-governance/sustainability`) | ESG score, carbon footprint |
| **Quality** (`/ai-governance/quality`) | Defect rate, FPY, trend |
| **Close** | 32 validated checkpoints; ERP/SSO on roadmap; today = integrated planning proof |

---

## Hero reference card

| Entity | Value |
|--------|-------|
| At-risk MOs | MO-ST-001 (copper), MO-ST-007 (CRGO), MO-ST-008 (capacity) |
| Products | Distribution Transformer 500 kVA, Pad-Mount 250 kVA, Power 50 MVA |
| Work centers | Core & Coil Assembly, Winding Station, Tank Fabrication & Test Bay |
| Customers | Great Lakes Utility (Tier 1), Midwest Grid Co |
| Suppliers | Midwest Copper Supply, CRGO Steel International |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Empty Control Tower | `.\scripts\seed-startrans-demo.ps1` |
| Copilot timeout | Ensure Ollama on `:11434`; pre-run cheat sheet queries |
| Login fails | `.\scripts\prepare-startrans-demo.ps1` |
| Upload fails | MO_ID must be MO-ST-*; WC codes WC001–WC003 |

---

## Integration honesty script

> “Live ERP publish and enterprise SSO are scaffolded — we defer to Phase 2 with your SAP/D365 team. Today we prove the planning intelligence layer on representative Star Trans data.”
