import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Critical Path — Authentication', () => {
  test('login page has no critical accessibility violations', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('h1')).toContainText('IPE Login');

    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  test('navigates to /login, enters credentials, redirects to Control Tower, stores JWT', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });

    await page.goto('/login');

    await expect(page.locator('h1')).toContainText('IPE Login');

    await page.fill('input[type="email"]', 'admin@demo.com');
    await page.fill('input[type="password"]', 'admin');

    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/control-tower/, { timeout: 10000 });

    const jwt = await page.evaluate(() => localStorage.getItem('access_token'));
    expect(jwt).not.toBeNull();
    expect(consoleErrors).toHaveLength(0);
  });
});

test.describe('Critical Path — Resolution Center', () => {
  test('navigates to /resolution, table renders, clicking MO shows scenario panel', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });

    await page.goto('/resolution');

    await expect(page.locator('h2, h3').filter({ hasText: /unresolved|resolution/i }).first()).toBeVisible();

    const moRows = page.locator('table tbody tr');
    await expect(moRows.first()).toBeVisible({ timeout: 5000 });
    expect(await moRows.count()).toBeGreaterThanOrEqual(1);

    const resolveButton = page.locator('button').filter({ hasText: /strategies|select|resolve/i }).first();
    await resolveButton.click();

    const scenarioPanel = page.locator('text=/scenario|strategies|constraints/i').first();
    await expect(scenarioPanel).toBeVisible({ timeout: 5000 });
    expect(consoleErrors).toHaveLength(0);
  });
});

test.describe('Critical Path — Planner Journey', () => {
  test('full planner journey: login -> find low-MO -> resolve -> approve', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });

    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@demo.com');
    await page.fill('input[type="password"]', 'admin');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/control-tower/, { timeout: 10000 });

    const redBadge = page.locator('.text-red-500, .bg-red, [class*="bg-red"]').first();
    if (await redBadge.isVisible({ timeout: 3000 }).catch(() => false)) {
      await redBadge.click();
    }

    await page.goto('/resolution');
    await expect(page.locator('table')).toBeVisible({ timeout: 5000 });

    const moRows = page.locator('table tbody tr');
    await expect(moRows.first()).toBeVisible({ timeout: 5000 });
    expect(await moRows.count()).toBeGreaterThanOrEqual(1);

    const resolveBtn = page.locator('button').filter({ hasText: /strategies|select|resolve/i }).first();
    await resolveBtn.click();

    const scenarios = page.locator('text=/scenario|strategies|constraints/i');
    await expect(scenarios.first()).toBeVisible({ timeout: 5000 });

    const approveBtn = page.locator('button').filter({ hasText: /approve|confirm/i }).first();
    if (await approveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await approveBtn.click();
    }

    expect(consoleErrors).toHaveLength(0);
  });
});

test.describe('Accessibility & Keyboard Navigation', () => {
  test('Control Tower has no critical aXe violations', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@demo.com');
    await page.fill('input[type="password"]', 'admin');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/control-tower/, { timeout: 10000 });

    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  test('Resolution Center has no critical aXe violations', async ({ page }) => {
    await page.goto('/resolution');

    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations.filter((v) => v.impact === 'critical')).toHaveLength(0);
  });

  test('can tab through login form without keyboard traps', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('h1')).toContainText('IPE Login');

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
