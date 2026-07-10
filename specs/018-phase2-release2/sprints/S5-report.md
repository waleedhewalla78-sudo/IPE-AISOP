# Sprint S5 Report — Arabic Expansion (8+ Screens)

**Sprint**: S5 · **Spec**: 018-phase2-release2  
**Date**: 2026-07-10  
**Gate prep**: G-R2-04 · **Maps**: PH1-05

---

## Summary

Expanded Arabic i18n from ~4 screens (Control Tower + nav) to **9 screens** with full namespace parity against `en.json`. RTL layout fixes applied to tables, forms, sidebar, and copilot chat. Language toggle persists via `localStorage.ipe_locale`.

**Locale path**: `apps/web/src/locales/{en,ar}.json` (imported by `src/lib/i18n.ts`; guide references `src/i18n/` — canonical bundle is `locales/`).

---

## Deliverables

| ID | Task | Status | Evidence |
|----|------|--------|----------|
| S5-01 | Expand `ar.json` (8+ screens) | ✅ | 299 keys, 100% parity with `en.json` |
| S5-02 | RTL layout validation | ✅ | Table `text-start`, logical borders, `ms`/`me`, globals.css |
| S5-03 | Language toggle persistence | ✅ | `ipe_locale` in localStorage; `setLocale()` on init |
| S5-04 | `docs/qa/arabic-qa-r2.md` | ✅ | Native speaker checklist |
| S5-05 | `e2e/arabic-r2.spec.ts` | ✅ | 4 RTL smoke tests |

---

## Key counts

| Bundle | Before | After | Added |
|--------|--------|-------|-------|
| `en.json` | 89 | 299 | **+210** |
| `ar.json` | ~100 | 299 | **+199** |

### Namespaces added / expanded

| Namespace | Keys | Screens |
|-----------|------|---------|
| `resolution.*` | 30 | Resolution Center |
| `schedule.*` | 33 | Schedule |
| `command.*` | 12 | Command Center dashboard |
| `admin.*` | 18 | Admin (existing, complete) |
| `auth.*` | 9 | Login |
| `errors.*` | 10 | Toast/error messages |
| `copilot.*` | 16 | Copilot chat |
| `demand.*` | 16 | Demand Sensing |
| `scenarios.*` | 19 | Scenario Workbench |
| `controlTower.*` | +14 | Control Tower (extended) |
| `nav.*` | +3 | Sidebar |
| `header.*` | 2 | Header |

---

## Screens with Arabic UI (9)

1. Control Tower — `برج المراقبة`
2. Resolution Center — `مركز الحلول`
3. Schedule — `الجدولة`
4. Command Center — KPI cards + subtitle
5. Admin — `لوحة الإدارة`
6. Login — `auth.*`
7. Copilot — `المساعد الذكي`
8. Demand Sensing — `استشعار الطلب`
9. Scenario Workbench — `منصة السيناريوهات`

---

## RTL changes

- `Table.tsx` — `text-start` on headers
- `Input.tsx` — `text-start` labels/inputs
- `Sidebar.tsx` — `border-e` (logical)
- `globals.css` — LTR embed for `tabular-nums` / `font-mono`
- `CopilotPanel.tsx` — `ms`/`me` bubble margins
- `DemandForecastPage` / `ScenarioWorkbenchPage` — `text-start`, `pe-*` padding
- `ControlTowerPage` — `ms-2` badge spacing

---

## Files changed

| File | Change |
|------|--------|
| `apps/web/src/locales/en.json` | +210 keys |
| `apps/web/src/locales/ar.json` | +199 keys |
| `apps/web/src/lib/i18n.ts` | `isRtl()`, `t()` interpolation |
| `apps/web/src/components/ui/Table.tsx` | RTL table headers |
| `apps/web/src/components/ui/Input.tsx` | RTL form alignment |
| `apps/web/src/components/layout/Sidebar.tsx` | Logical border |
| `apps/web/src/components/layout/Header.tsx` | i18n |
| `apps/web/src/components/LanguageSwitcher.tsx` | `data-testid` |
| `apps/web/src/assets/styles/globals.css` | Numeric LTR in RTL |
| `apps/web/src/features/schedule/SchedulePage.tsx` | i18n |
| `apps/web/src/features/hubs/command-center/CommandCenterDashboardPage.tsx` | i18n |
| `apps/web/src/features/copilot/components/CopilotPanel.tsx` | i18n + RTL |
| `apps/web/src/features/hubs/planning/DemandForecastPage.tsx` | i18n + RTL |
| `apps/web/src/features/hubs/planning/ScenarioWorkbenchPage.tsx` | i18n + RTL |
| `apps/web/src/features/control-tower/components/ControlTowerPage.tsx` | i18n extended |
| `apps/web/src/features/auth/components/LoginForm.tsx` | `auth.*` namespace |
| `apps/web/e2e/arabic-r2.spec.ts` | **new** |
| `docs/qa/arabic-qa-r2.md` | **new** |
| `specs/018-phase2-release2/tasks.md` | S5 complete, G-R2-04 prep |

---

## E2E status

Run: `cd apps/web && npx playwright install chromium && npx playwright test e2e/arabic-r2.spec.ts --project=desktop`

| Test | Status |
|------|--------|
| RTL direction + locale persistence | ✅ PASS |
| Sidebar toggle EN ↔ AR | ✅ PASS |
| Arabic labels on 8+ screens | 🔄 (command-center API mocks added; verify with stack up) |
| Login Arabic auth labels | ✅ PASS |

**Last run**: 3/4 passed (desktop project). Full green requires dev server on `:8082`.

---

## Gate G-R2-04 — remaining

- [ ] Native Arabic speaker sign-off (`docs/qa/arabic-qa-r2.md`)
- [ ] E2E green in CI with stack up

---

*S5 report v1.0 — Phase 2 Release 2*
