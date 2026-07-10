# Arabic QA Checklist — Release 2 (Sprint S5)

**Gate**: G-R2-04 · **Maps**: PH1-05  
**Locale bundle**: `apps/web/src/locales/ar.json`  
**E2E smoke**: `apps/web/e2e/arabic-r2.spec.ts`

---

## Pre-requisites

- [ ] Web app running (`npm run dev` in `apps/web`, port 8082)
- [ ] Valid demo credentials (`Ahmed@nour` / `admin`) or SSO configured
- [ ] Native Arabic reviewer assigned for sign-off

---

## Language toggle & persistence

- [ ] Toggle visible in sidebar header (`data-testid="language-toggle"`)
- [ ] Click switches UI to Arabic; `document.documentElement.dir` = `rtl`
- [ ] Click again switches to English; `dir` = `ltr`
- [ ] After reload, selected language persists (`localStorage.ipe_locale`)
- [ ] Numbers, percentages, and UUIDs remain LTR-readable

---

## Screen coverage (8+ required)

| # | Screen | Route | Arabic title key | RTL table/form |
|---|--------|-------|------------------|----------------|
| 1 | Control Tower | `/planning/control-tower` | `controlTower.title` | ☐ |
| 2 | Resolution Center | `/planning/resolution` | `resolution.title` | ☐ |
| 3 | Schedule | `/planning/schedule` | `schedule.title` | ☐ |
| 4 | Command Center | `/command-center/dashboard` | `command.subtitle` | ☐ |
| 5 | Admin | `/platform/admin` | `admin.title` | ☐ |
| 6 | Login | `/login` | `auth.title` | ☐ |
| 7 | Copilot | `/ai-governance/copilot` | `copilot.title` | ☐ |
| 8 | Demand Sensing | `/planning/demand` | `demand.title` | ☐ |
| 9 | Scenario Workbench | `/planning/scenarios` | `scenarios.title` | ☐ |

---

## Namespace completeness

- [ ] `resolution.*` — all keys present in `ar.json`
- [ ] `schedule.*` — all keys present
- [ ] `command.*` — all keys present
- [ ] `admin.*` — all keys present
- [ ] `auth.*` — all keys present
- [ ] `errors.*` — all keys present
- [ ] `copilot.*` — all keys present
- [ ] `demand.*` — all keys present
- [ ] `scenarios.*` — all keys present

---

## RTL layout

- [ ] Sidebar border on correct side (logical `border-e`)
- [ ] Table headers use `text-start` alignment
- [ ] Form labels right-aligned in Arabic
- [ ] Copilot chat bubbles mirror correctly (`ms`/`me` spacing)
- [ ] No clipped or overlapping Arabic text in nav
- [ ] Chart legends readable (Demand page)

---

## Terminology review (manufacturing)

| English | Expected Arabic | Verified |
|---------|-----------------|----------|
| Control Tower | برج المراقبة | ☐ |
| Manufacturing Order | أمر تشغيل | ☐ |
| Feasibility | الجدوى | ☐ |
| Resolution | مركز الحلول | ☐ |
| Schedule | الجدولة | ☐ |
| BOM | قائمة مواد | ☐ |
| COGM | تكلفة البضاعة المُصنَّعة | ☐ |

---

## Automated checks

```powershell
cd ipe/apps/web
npx playwright test e2e/arabic-r2.spec.ts --project=desktop
```

- [ ] E2E smoke PASS
- [ ] No console errors on Arabic routes

---

## Sign-off

| Role | Name | Date | Result |
|------|------|------|--------|
| Native Arabic reviewer | | | ☐ PASS / ☐ FAIL |
| QA lead | | | ☐ PASS / ☐ FAIL |
| Product owner | | | ☐ PASS / ☐ FAIL |

**Notes:**
