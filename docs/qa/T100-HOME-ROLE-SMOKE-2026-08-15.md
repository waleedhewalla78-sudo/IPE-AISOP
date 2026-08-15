# T100 — Playwright home role smoke

**Date:** 2026-08-15  
**Spec:** `040-startrans-demo-aug18`  
**Spec file:** `apps/web/e2e/home-role.spec.ts`

## Cases

1. Executive `/home` → `executive-home` visible, planner hidden  
2. Planner `/home` → `planner-home` + feasibility heatmap  
3. Role switcher executive ↔ planner survives reload  

## Run

```powershell
cd ipe/apps/web
$env:PLAYWRIGHT_REUSE_SERVER='1'
npx playwright test e2e/home-role.spec.ts --project=desktop
```

## Result

**PASS** — desktop **3/3** (2026-08-15)

```
npx playwright test e2e/home-role.spec.ts --project=desktop
```

