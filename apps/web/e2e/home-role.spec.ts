import { test, expect } from '@playwright/test';

/**
 * T100 — Home role smoke (Spec 040): executive vs planner layouts on /home.
 */
const EMAIL = process.env.TEST_EMAIL ?? 'Ahmed@nour';
const PASSWORD = process.env.TEST_PASSWORD ?? 'admin';

async function login(page: import('@playwright/test').Page) {
  await page.addInitScript(() => {
    localStorage.setItem('ipe_locale', 'en');
    localStorage.setItem('ipe_e2e_locale_seeded', '1');
  });
  await page.goto('/login');
  await page.fill('input[type="email"]', EMAIL);
  await page.fill('input[type="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL(/\/(planning|workspace|home|command-center)/, { timeout: 25000 });
}

test.describe('Home role smoke (T100)', () => {
  test('executive home renders KPI layout', async ({ page }) => {
    await login(page);
    await page.evaluate(() => localStorage.setItem('ipe_demo_role', 'executive'));
    await page.goto('/home');
    await expect(page.getByTestId('unified-workspace')).toBeVisible({ timeout: 20000 });
    await expect(page.getByTestId('executive-home')).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('planner-home')).toHaveCount(0);
    await expect(page.getByTestId('demo-role-switcher')).toBeVisible();
  });

  test('planner home renders feasibility heatmap', async ({ page }) => {
    await login(page);
    await page.evaluate(() => localStorage.setItem('ipe_demo_role', 'planner'));
    await page.goto('/home');
    await expect(page.getByTestId('unified-workspace')).toBeVisible({ timeout: 20000 });
    await expect(page.getByTestId('planner-home')).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId('executive-home')).toHaveCount(0);
    await expect(page.getByText(/feasibility heatmap/i)).toBeVisible();
  });

  test('role switcher flips executive ↔ planner without reload crash', async ({ page }) => {
    await login(page);
    await page.evaluate(() => localStorage.setItem('ipe_demo_role', 'executive'));
    await page.goto('/home');
    await expect(page.getByTestId('executive-home')).toBeVisible({ timeout: 15000 });

    await page.getByTestId('demo-role-switcher').locator('select').selectOption('planner');
    await page.reload();
    await expect(page.getByTestId('planner-home')).toBeVisible({ timeout: 15000 });

    await page.getByTestId('demo-role-switcher').locator('select').selectOption('executive');
    await page.reload();
    await expect(page.getByTestId('executive-home')).toBeVisible({ timeout: 15000 });
  });
});
