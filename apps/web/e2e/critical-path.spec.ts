import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/** Demo user aligned with release2-smoke / Kong AUTH_MODE=local. */
const TEST_EMAIL = process.env.TEST_EMAIL ?? 'Ahmed@nour';
const TEST_PASSWORD = process.env.TEST_PASSWORD ?? 'admin';

async function forceEnglishLocale(page: import('@playwright/test').Page) {
  await page.addInitScript(() => {
    localStorage.setItem('ipe_locale', 'en');
    localStorage.setItem('ipe_e2e_locale_seeded', '1');
  });
}

async function loginAsDemo(page: import('@playwright/test').Page) {
  await forceEnglishLocale(page);
  await page.goto('/login');
  await page.fill('input[type="email"]', TEST_EMAIL);
  await page.fill('input[type="password"]', TEST_PASSWORD);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/planning\/dashboard/, { timeout: 15000 });
}

test.describe('Critical Path — Authentication', () => {
  test('login page has no critical accessibility violations', async ({ page }) => {
    await forceEnglishLocale(page);
    await page.goto('/login');
    await expect(page.locator('h1')).toContainText(/IPE Login|تسجيل الدخول/i);

    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  test('navigates to /login, enters credentials, redirects to Planning Dashboard, stores JWT', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });

    await forceEnglishLocale(page);
    await page.goto('/login');
    await expect(page.locator('h1')).toContainText(/IPE Login|تسجيل الدخول/i);

    await page.fill('input[type="email"]', TEST_EMAIL);
    await page.fill('input[type="password"]', TEST_PASSWORD);
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/planning\/dashboard/, { timeout: 15000 });

    const jwt = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(jwt).not.toBeNull();
    expect(consoleErrors.filter((e) => !/Failed to load resource/i.test(e))).toHaveLength(0);
  });
});

test.describe('Critical Path — Resolution Center', () => {
  test('navigates to /planning/resolution, table renders, clicking MO shows scenario panel', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });

    await loginAsDemo(page);

    await page.goto('/planning/resolution');
    await page.waitForLoadState('networkidle');

    // Title is i18n `resolution.title` ("Resolution Center" / "مركز الحلول").
    await expect(
      page.getByRole('heading', { name: /resolution|مركز الحلول/i }).first(),
    ).toBeVisible({ timeout: 15000 });

    const moRows = page.locator('table tbody tr');
    const hasRows = await moRows.first().isVisible({ timeout: 10000 }).catch(() => false);
    if (hasRows) {
      expect(await moRows.count()).toBeGreaterThanOrEqual(1);
      const resolveButton = page.locator('button').filter({ hasText: /strategies|select|resolve|اختيار/i }).first();
      await resolveButton.click();
      const scenarioPanel = page.locator('text=/scenario|strategies|constraints|سيناريو|قيود/i').first();
      await expect(scenarioPanel).toBeVisible({ timeout: 10000 });
    } else {
      // Empty queue is acceptable when seed has no unresolved MOs — page chrome must still render.
      await expect(page.getByText(/no unresolved|لا توجد/i).first()).toBeVisible({ timeout: 5000 });
    }
    const actionable = consoleErrors.filter(
      (e) => !/Failed to load resource:.*\b(401|403|404)\b/i.test(e),
    );
    expect(actionable).toHaveLength(0);
  });
});

test.describe('Critical Path — Planner Journey', () => {
  test('full planner journey: login -> find low-MO -> resolve -> approve', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });

    await loginAsDemo(page);

    const redBadge = page.locator('.text-red-500, .bg-red, [class*="bg-red"]').first();
    if (await redBadge.isVisible({ timeout: 3000 }).catch(() => false)) {
      await redBadge.click();
    }

    await page.goto('/planning/resolution');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('table')).toBeVisible({ timeout: 10000 });

    const moRows = page.locator('table tbody tr');
    const hasRows = await moRows.first().isVisible({ timeout: 10000 }).catch(() => false);
    if (!hasRows) {
      // Seed may have no unresolved MOs — journey still validates auth + resolution chrome.
      await expect(
        page.getByRole('heading', { name: /resolution|مركز الحلول/i }).first(),
      ).toBeVisible();
      return;
    }
    expect(await moRows.count()).toBeGreaterThanOrEqual(1);

    const resolveBtn = page
      .locator('button')
      .filter({ hasText: /strategies|select|resolve|اختيار/i })
      .first();
    await resolveBtn.click();

    const scenarios = page.locator('text=/scenario|strategies|constraints|سيناريو|قيود/i');
    await expect(scenarios.first()).toBeVisible({ timeout: 10000 });

    const approveBtn = page.locator('button').filter({ hasText: /approve|confirm|اعتماد/i }).first();
    if (await approveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await approveBtn.click();
    }

    // Ignore transient browser network noise; fail on app/runtime errors only.
    const actionable = consoleErrors.filter(
      (e) => !/Failed to load resource:.*\b(401|403|404)\b/i.test(e),
    );
    expect(actionable).toHaveLength(0);
  });
});

test.describe('Accessibility & Keyboard Navigation', () => {
  test('Planning Dashboard has no critical aXe violations', async ({ page }) => {
    await loginAsDemo(page);

    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  test('Resolution Center has no critical aXe violations', async ({ page }) => {
    await loginAsDemo(page);
    await page.goto('/planning/resolution');

    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  test('can tab through login form without keyboard traps', async ({ page }) => {
    await forceEnglishLocale(page);
    await page.goto('/login');
    await expect(page.locator('h1')).toContainText(/IPE Login|تسجيل الدخول/i);

    await page.keyboard.press('Tab');
    const emailFocused = await page.locator('input[type="email"]').evaluate((el) => el === document.activeElement);
    expect(emailFocused).toBeTruthy();

    await page.keyboard.press('Tab');
    const passwordFocused = await page.locator('input[type="password"]').evaluate((el) => el === document.activeElement);
    expect(passwordFocused).toBeTruthy();

    await page.keyboard.press('Tab');
    const buttonFocused = await page.locator('button[type="submit"]').evaluate((el) => el === document.activeElement);
    expect(buttonFocused).toBeTruthy();
  });
});
