/**
 * Capture screenshots for all product domains, menus, and module screens.
 * Usage (from apps/web): node scripts/capture-product-screenshots.mjs
 *
 * Env:
 *   IPE_BASE_URL      default http://localhost:8082
 *   TEST_EMAIL        default Ahmed@nour
 *   TEST_PASSWORD     default admin
 *   IPE_SHOT_SETTLE_MS  wait after navigation (default 1800)
 */
import { chromium } from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BASE = process.env.IPE_BASE_URL ?? 'http://localhost:8082';
const OUT = path.resolve(__dirname, '../../../docs/product-screenshots');
const email = process.env.TEST_EMAIL ?? 'Ahmed@nour';
const password = process.env.TEST_PASSWORD ?? 'admin';
const SETTLE = Number(process.env.IPE_SHOT_SETTLE_MS ?? 1800);

/** Full product IA — mirrors productArchitecture + key extras */
const SCREENS = [
  // Auth / homes
  { id: '00-login', route: '/login', label: 'Login', skipAuth: true, fullPage: false },
  { id: '01-home-executive', route: '/home', label: 'Home — Executive', role: 'executive' },
  { id: '02-home-planner', route: '/home', label: 'Home — Planner', role: 'planner' },
  { id: '03-workspace', route: '/workspace', label: 'Workspace (Today)' },

  // Plan domain
  { id: '10-plan-control-tower', route: '/planning/control-tower', label: 'Plan · Control Tower', menu: 'plan' },
  { id: '11-plan-demand', route: '/planning/demand', label: 'Plan · Demand Intelligence', menu: 'plan' },
  { id: '12-plan-resolution', route: '/planning/resolution', label: 'Plan · Resolution Center', menu: 'plan' },
  { id: '13-plan-schedule', route: '/planning/schedule', label: 'Plan · Production Schedule', menu: 'plan' },
  { id: '14-plan-detailed-schedule', route: '/plan/detailed-schedule', label: 'Plan · Detailed Schedule', menu: 'plan' },
  { id: '15-plan-scenarios', route: '/planning/scenarios', label: 'Plan · Scenario Workbench', menu: 'plan' },
  { id: '16-plan-predictions', route: '/planning/predictions', label: 'Plan · Predictive Risk', menu: 'plan' },
  { id: '17-plan-overview', route: '/planning/dashboard', label: 'Plan · Overview', menu: 'plan' },
  { id: '18-plan-root-cause', route: '/planning/root-cause', label: 'Plan · Root Cause' },
  { id: '19-plan-cockpit', route: '/planning/cockpit', label: 'Plan · Cockpit' },
  { id: '1a-plan-horizons', route: '/planning/horizons', label: 'Plan · Three Horizons' },

  // Execute domain
  { id: '20-execute-shop-floor', route: '/shop-floor', label: 'Execute · Shop Floor', menu: 'execute' },
  { id: '21-execute-equipment', route: '/command-center/equipment', label: 'Execute · Equipment', menu: 'execute' },
  { id: '22-execute-projects', route: '/work/projects', label: 'Execute · Projects', menu: 'execute' },
  { id: '23-execute-tasks', route: '/work/tasks', label: 'Execute · Tasks', menu: 'execute' },
  { id: '24-execute-approvals', route: '/work/approvals', label: 'Execute · Approvals', menu: 'execute' },
  { id: '25-execute-meetings', route: '/work/meetings', label: 'Execute · Meetings', menu: 'execute' },
  { id: '26-execute-calendar', route: '/work/calendar', label: 'Execute · Calendar', menu: 'execute' },
  { id: '27-execute-documents', route: '/work/documents', label: 'Execute · Documents', menu: 'execute' },
  { id: '28-execute-knowledge', route: '/work/knowledge', label: 'Execute · Knowledge', menu: 'execute' },
  { id: '29-execute-objectives', route: '/work/objectives', label: 'Execute · Objectives', menu: 'execute' },
  { id: '2a-execute-kpis', route: '/work/kpis', label: 'Execute · KPIs', menu: 'execute' },
  { id: '2b-execute-teams', route: '/work/teams', label: 'Execute · Teams', menu: 'execute' },
  { id: '2c-execute-automation', route: '/work/automation', label: 'Execute · Automation', menu: 'execute' },
  { id: '2d-execute-reports', route: '/work/reports', label: 'Execute · Reports', menu: 'execute' },

  // Supply domain
  { id: '30-supply-planning', route: '/supply-chain/supply-planning', label: 'Supply · Planning', menu: 'supply' },
  { id: '31-supply-inventory', route: '/supply-chain/inventory', label: 'Supply · Inventory', menu: 'supply' },
  { id: '32-supply-procurement', route: '/supply-chain/procurement', label: 'Supply · Procurement', menu: 'supply' },
  { id: '33-supply-suppliers', route: '/supply-chain/suppliers', label: 'Supply · Suppliers', menu: 'supply' },
  { id: '34-supply-orders', route: '/supply-chain/orders', label: 'Supply · Orders' },
  { id: '35-supply-tariff', route: '/supply-chain/tariff', label: 'Supply · Tariff' },
  { id: '36-supply-scn', route: '/supply-chain/scn-portal', label: 'Supply · SCN Portal' },

  // Analyze domain
  { id: '40-analyze-outcomes', route: '/command-center/dashboard', label: 'Analyze · Outcomes & Risk', menu: 'analyze' },
  { id: '41-analyze-war-room', route: '/command-center/war-room', label: 'Analyze · War Room', menu: 'analyze' },
  { id: '42-analyze-cost-of-chaos', route: '/command-center/cost-of-chaos', label: 'Analyze · Cost of Chaos', menu: 'analyze' },
  { id: '43-analyze-executive', route: '/command-center/executive', label: 'Analyze · Executive', menu: 'analyze' },
  { id: '44-analyze-otd', route: '/command-center/otd-analytics', label: 'Analyze · OTD Analytics', menu: 'analyze' },
  { id: '45-analyze-ops-live', route: '/command-center/ops-live', label: 'Analyze · Ops Live', menu: 'analyze' },
  { id: '46-analyze-outcomes-page', route: '/command-center/outcomes', label: 'Analyze · Outcomes' },
  { id: '47-analyze-sop', route: '/command-center/sop-report', label: 'Analyze · S&OP Report' },
  { id: '48-analyze-ops-deep', route: '/command-center/operations-deep', label: 'Analyze · Operations Deep' },
  { id: '49-analyze-intelligence', route: '/intelligence', label: 'Analyze · Intelligence', menu: 'analyze' },

  // Intelligence modules
  { id: '50-intel-pulse', route: '/intelligence/pulse', label: 'Intelligence · Pulse' },
  { id: '51-intel-demand', route: '/intelligence/demand', label: 'Intelligence · Demand' },
  { id: '52-intel-production', route: '/intelligence/production', label: 'Intelligence · Production' },
  { id: '53-intel-supply', route: '/intelligence/supply', label: 'Intelligence · Supply' },
  { id: '54-intel-quality', route: '/intelligence/quality', label: 'Intelligence · Quality' },
  { id: '55-intel-finance', route: '/intelligence/finance', label: 'Intelligence · Finance' },
  { id: '56-intel-customer', route: '/intelligence/customer', label: 'Intelligence · Customer' },
  { id: '57-intel-analytics', route: '/intelligence/analytics', label: 'Intelligence · Analytics' },
  { id: '58-intel-commercial', route: '/intelligence/commercial', label: 'Intelligence · Commercial' },
  { id: '59-intel-procurement', route: '/intelligence/procurement', label: 'Intelligence · Procurement' },

  // Copilot domain
  { id: '60-copilot', route: '/ai-governance/copilot', label: 'Copilot · Chat', menu: 'copilot' },
  { id: '61-copilot-agents', route: '/platform/agents', label: 'Copilot · Agents', menu: 'copilot' },
  { id: '62-copilot-meeting-prep', route: '/ai-governance/meeting-prep', label: 'Copilot · Meeting Prep', menu: 'copilot' },
  { id: '63-copilot-design-ai', route: '/ai-governance/design-ai', label: 'Copilot · Design AI', menu: 'copilot' },

  // Admin domain
  { id: '70-admin-gov-overview', route: '/ai-governance/overview', label: 'Admin · Governance Overview', menu: 'admin' },
  { id: '71-admin-ai-trust', route: '/ai-governance/ai-trust', label: 'Admin · AI Trust', menu: 'admin' },
  { id: '72-admin-compliance', route: '/ai-governance/compliance', label: 'Admin · Compliance', menu: 'admin' },
  { id: '73-admin-quality', route: '/ai-governance/quality', label: 'Admin · Quality', menu: 'admin' },
  { id: '74-admin-mdr', route: '/ai-governance/mdr', label: 'Admin · MDR Gate', menu: 'admin' },
  { id: '75-admin-sustainability', route: '/ai-governance/sustainability', label: 'Admin · Sustainability' },
  { id: '76-admin-platform', route: '/platform/admin', label: 'Admin · Platform', menu: 'admin' },
  { id: '77-admin-upload', route: '/platform/upload', label: 'Admin · Data Upload', menu: 'admin' },
  { id: '78-admin-startrans-upload', route: '/admin/data/upload', label: 'Admin · Star Trans Upload' },
  { id: '79-admin-odoo', route: '/platform/odoo-config', label: 'Admin · Odoo Config' },
  { id: '7a-admin-onboarding', route: '/platform/onboarding', label: 'Admin · Onboarding' },
  { id: '7b-admin-mlops', route: '/platform/ml-ops', label: 'Admin · ML Ops' },
  { id: '7c-admin-ops', route: '/platform/ops', label: 'Admin · Ops' },
  { id: '7d-admin-exceptions', route: '/platform/exceptions', label: 'Admin · Exceptions' },
  { id: '7e-customer-portal', route: '/customer-portal', label: 'Customer Portal' },
];

const MENU_SHOTS = [
  { id: 'm01-menu-home', domain: 'home', route: '/home', label: 'Menu · Home rail' },
  { id: 'm02-menu-plan', domain: 'plan', route: '/planning/control-tower', label: 'Menu · Plan sidebar' },
  { id: 'm03-menu-execute', domain: 'execute', route: '/shop-floor', label: 'Menu · Execute sidebar' },
  { id: 'm04-menu-supply', domain: 'supply', route: '/supply-chain/supply-planning', label: 'Menu · Supply sidebar' },
  { id: 'm05-menu-analyze', domain: 'analyze', route: '/command-center/dashboard', label: 'Menu · Analyze sidebar' },
  { id: 'm06-menu-copilot', domain: 'copilot', route: '/ai-governance/copilot', label: 'Menu · Copilot agents' },
  { id: 'm07-menu-admin', domain: 'admin', route: '/platform/admin', label: 'Menu · Admin sidebar' },
];

function slugFile(id) {
  return `${id}.png`;
}

async function settle(page) {
  await page.waitForLoadState('domcontentloaded').catch(() => {});
  await page.waitForTimeout(SETTLE);
}

async function ensureLoggedIn(page) {
  await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded' });
  await settle(page);
  if (!page.url().includes('/login')) return;
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/(planning|workspace|home|command-center)/, { timeout: 30000 }).catch(() => {});
  await settle(page);
}

async function capture(page, outPath, fullPage = true) {
  await page.screenshot({ path: outPath, fullPage });
  const st = fs.statSync(outPath);
  return st.size;
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
  });

  const catalog = [];
  const errors = [];

  // Login screen (pre-auth)
  try {
    await page.goto(`${BASE}/login`, { waitUntil: 'domcontentloaded' });
    await settle(page);
    const loginFile = slugFile('00-login');
    const size = await capture(page, path.join(OUT, loginFile), false);
    catalog.push({ id: '00-login', label: 'Login', route: '/login', file: loginFile, bytes: size, ok: true });
  } catch (e) {
    errors.push({ id: '00-login', error: String(e) });
  }

  await ensureLoggedIn(page);

  // Domain menus (rail + sidebar)
  for (const m of MENU_SHOTS) {
    try {
      await page.goto(`${BASE}${m.route}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await settle(page);
      // Prefer clipping to icon-rail + domain-sidebar when present
      const rail = page.getByTestId('sidebar');
      const file = slugFile(m.id);
      const outPath = path.join(OUT, file);
      if (await rail.count()) {
        await rail.screenshot({ path: outPath });
      } else {
        await capture(page, outPath, false);
      }
      const size = fs.statSync(outPath).size;
      catalog.push({ id: m.id, label: m.label, route: m.route, file, bytes: size, ok: size > 5000 });
      console.log('menu', m.id, Math.round(size / 1024) + 'KB');
    } catch (e) {
      errors.push({ id: m.id, error: String(e.message || e) });
      console.error('menu FAIL', m.id, e.message || e);
    }
  }

  // All screens
  for (const s of SCREENS) {
    if (s.id === '00-login') continue; // already done
    try {
      if (s.role) {
        await page.evaluate((role) => localStorage.setItem('ipe_demo_role', role), s.role);
      }
      await page.goto(`${BASE}${s.route}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await settle(page);
      const file = slugFile(s.id);
      const size = await capture(page, path.join(OUT, file), s.fullPage !== false);
      catalog.push({
        id: s.id,
        label: s.label,
        route: s.route,
        file,
        bytes: size,
        ok: size > 5000,
        menu: s.menu || null,
      });
      console.log('screen', s.id, Math.round(size / 1024) + 'KB');
    } catch (e) {
      errors.push({ id: s.id, error: String(e.message || e) });
      console.error('screen FAIL', s.id, e.message || e);
    }
  }

  // Feasibility drawer overlay (bonus)
  try {
    await page.goto(`${BASE}/planning/control-tower`, { waitUntil: 'domcontentloaded' });
    await settle(page);
    const badge = page.getByTestId('feasibility-badge').first();
    if (await badge.count()) {
      await badge.click();
      await page.waitForTimeout(800);
    }
    const file = '1b-plan-feasibility-drawer.png';
    const size = await capture(page, path.join(OUT, file), false);
    catalog.push({
      id: '1b-plan-feasibility-drawer',
      label: 'Plan · Feasibility Drawer',
      route: '/planning/control-tower',
      file,
      bytes: size,
      ok: true,
    });
  } catch (e) {
    errors.push({ id: '1b-plan-feasibility-drawer', error: String(e.message || e) });
  }

  await browser.close();

  const md = [
    '# Product screenshots — full IA capture',
    '',
    `**Captured:** ${new Date().toISOString()}`,
    `**Base URL:** ${BASE}`,
    `**Viewport:** 1920×1080`,
    `**Count:** ${catalog.length} files · **Errors:** ${errors.length}`,
    '',
    '## Domain menus',
    '',
    '| File | Label | Route | Size |',
    '|------|-------|-------|------|',
    ...catalog
      .filter((c) => c.id.startsWith('m'))
      .map((c) => `| \`${c.file}\` | ${c.label} | \`${c.route}\` | ${Math.round(c.bytes / 1024)} KB |`),
    '',
    '## Screens',
    '',
    '| File | Label | Route | Size |',
    '|------|-------|-------|------|',
    ...catalog
      .filter((c) => !c.id.startsWith('m'))
      .map((c) => `| \`${c.file}\` | ${c.label} | \`${c.route}\` | ${Math.round(c.bytes / 1024)} KB |`),
    '',
  ];
  if (errors.length) {
    md.push('## Capture errors', '', ...errors.map((e) => `- **${e.id}**: ${e.error}`), '');
  }
  fs.writeFileSync(path.join(OUT, 'README.md'), md.join('\n'), 'utf8');
  fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify({ catalog, errors, base: BASE }, null, 2));

  console.log('\nDONE', catalog.length, 'shots →', OUT);
  console.log('errors', errors.length);
  if (errors.length) process.exitCode = 1;
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
