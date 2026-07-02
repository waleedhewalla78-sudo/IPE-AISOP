import { test, expect } from '@playwright/test';

const EMAIL = process.env.TEST_EMAIL ?? 'Ahmed@nour';
const PASSWORD = process.env.TEST_PASSWORD ?? 'admin';

async function login(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.fill('input[type="email"]', EMAIL);
  await page.fill('input[type="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/planning\/dashboard/, { timeout: 15000 });
}

test.describe('Supply tab', () => {
  test('supply network page renders', async ({ page }) => {
    await login(page);
    await page.goto('/supply-chain/supply-planning');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toContainText(/supply|network|facilit/i);
  });
});
