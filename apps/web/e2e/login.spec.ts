import { test, expect } from '@playwright/test';

const EMAIL = process.env.TEST_EMAIL ?? 'Ahmed@nour';
const PASSWORD = process.env.TEST_PASSWORD ?? 'admin';

test.describe('Login flow', () => {
  test('login and dashboard loads', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', EMAIL);
    await page.fill('input[type="password"]', PASSWORD);
    await page.click('button[type="submit"]');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/planning\/dashboard/, { timeout: 15000 });
    await expect(page.locator('body')).toBeVisible();
  });
});
