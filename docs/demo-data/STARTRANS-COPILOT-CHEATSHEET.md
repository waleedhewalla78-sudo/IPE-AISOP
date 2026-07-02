# Star Trans — Live Copilot Cheat Sheet

**Run these in order during the demo.** Wait for full response (~30–90s each).

---

## Pre-flight (T-5 min)

In Copilot UI, confirm **planner** role session (CP30). If slow, run once before clients enter:

```
What is the current FG stock for Distribution Transformer 500 kVA?
```

---

## Query 1 — At-risk orders (feasibility)

```
Which manufacturing orders are at risk this week?
```

**Expected:** Summary mentioning low feasibility scores; may reference MO-ST-001 or material constraints.

**If generic:** Follow up: “What is blocking MO-ST-001?”

---

## Query 2 — Material / copper story

```
What is blocking MO-ST-001?
```

**Expected:** Material shortage, copper winding wire, or Midwest Copper Supply context.

---

## Query 3 — Bottleneck work centers

```
Show bottleneck work centers
```

**Expected:** Winding Station or Core & Coil Assembly under pressure.

---

## Optional (time permitting)

```
What is the current FG stock for Distribution Transformer 500 kVA and Pad-Mount Transformer 250 kVA?
```

**Expected:** `material_status` intent with product names and quantities.

---

## Backup (if Ollama fails)

1. Show pre-run output in `docs/demo-data/startrans-pre-demo.txt` (CP10–11 section)  
2. Say: “LLM runs locally for data privacy — we’ll retry live; the API path is validated.”  
3. Switch to Resolution Center scenarios (same story, no AI)

---

## Do NOT ask

- “Connect to SAP” (not live)
- “Create production order in ERP” (deferred)
- Generic “Widget A” (old demo names — use Distribution Transformer)
