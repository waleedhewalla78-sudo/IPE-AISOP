/**
 * Capture Star Trans demo screenshots (T094) against http://localhost:8082
 */
import { chromium } from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';

const BASE = process.env.IPE_BASE_URL ?? 'http://localhost:8082';
const OUT = path.resolve('../../docs/star-trans-demo-screenshots');
const email = process.env.TEST_EMAIL ?? 'Ahmed@nour';
const password = process.env.TEST_PASSWORD ?? 'admin';

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });

  await page.goto(`${BASE}/login`);
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/(planning|workspace|home)/, { timeout: 20000 });
  await page.screenshot({ path: path.join(OUT, '01-login.png'), fullPage: false });

  await page.evaluate(() => localStorage.setItem('ipe_demo_role', 'executive'));
  await page.goto(`${BASE}/home`);
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(OUT, '02-executive-home.png'), fullPage: true });

  await page.evaluate(() => localStorage.setItem('ipe_demo_role', 'planner'));
  await page.goto(`${BASE}/home`);
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(OUT, '03-planner-home.png'), fullPage: true });

  await page.goto(`${BASE}/planning/control-tower`);
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(OUT, '04-control-tower.png'), fullPage: true });

  const badge = page.getByTestId('feasibility-badge').first();
  if (await badge.count()) {
    await badge.click();
    await page.waitForTimeout(800);
    await page.screenshot({ path: path.join(OUT, '05-feasibility-drawer.png'), fullPage: false });
    await page.keyboard.press('Escape');
  } else {
    await page.screenshot({ path: path.join(OUT, '05-feasibility-drawer.png'), fullPage: false });
  }

  await page.goto(`${BASE}/plan/detailed-schedule`);
  await page.waitForTimeout(2500);
  await page.screenshot({ path: path.join(OUT, '06-detailed-schedule.png'), fullPage: true });

  await page.goto(`${BASE}/admin/data/upload`);
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(OUT, '07-data-upload.png'), fullPage: true });

  await page.goto(`${BASE}/home`);
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(OUT, '08-navigation-ia.png'), fullPage: false });

  await browser.close();
  const files = fs.readdirSync(OUT).filter((f) => f.endsWith('.png'));
  console.log('captured', files.length, files.join(','));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
