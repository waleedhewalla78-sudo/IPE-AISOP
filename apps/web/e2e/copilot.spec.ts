import { test, expect } from '@playwright/test';

const LOCAL_AUTH_INFO = {
  data: {
    mode: 'local',
    keycloak_url: '',
    keycloak_realm: 'ipe',
    keycloak_client_id: 'ipe-platform',
  },
};

async function stubLocalAuth(page: import('@playwright/test').Page) {
  await page.route('**/api/v1/auth/info', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(LOCAL_AUTH_INFO),
    });
  });
}

async function loginAsDemo(page: import('@playwright/test').Page) {
  await page.addInitScript(() => {
    localStorage.setItem('ipe_locale', 'en');
    localStorage.setItem('ipe_e2e_locale_seeded', '1');
  });
  await stubLocalAuth(page);
  await page.goto('/login');
  await page.fill('input[type="email"]', process.env.TEST_EMAIL ?? 'Ahmed@nour');
  await page.fill('input[type="password"]', process.env.TEST_PASSWORD ?? 'admin');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/planning\/dashboard/, { timeout: 20000 });
}

test.describe('Copilot R1 smoke', () => {
  test('unauthenticated copilot route redirects to login', async ({ page }) => {
    await stubLocalAuth(page);
    await page.addInitScript(() => localStorage.clear());
    await page.goto('/ai-governance/copilot');
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  });

  test('legacy /copilot redirects to ai-governance/copilot when authenticated', async ({ page }) => {
    await loginAsDemo(page);
    await page.goto('/copilot');
    await expect(page).toHaveURL(/\/ai-governance\/copilot/, { timeout: 10000 });
  });

  test('release1 sidebar shows Copilot and navigates to panel', async ({ page }) => {
    await loginAsDemo(page);
    await page.goto('/workspace');
    const copilotLink = page.getByRole('link', { name: /copilot|المساعد الذكي/i });
    await expect(copilotLink).toBeVisible({ timeout: 10000 });
    await copilotLink.click();
    await expect(page).toHaveURL(/\/ai-governance\/copilot/, { timeout: 10000 });
    await expect(page.locator('body')).toContainText(/copilot|planner|production|المساعد/i);
  });

  test('copilot panel renders after direct navigation', async ({ page }) => {
    await loginAsDemo(page);
    await page.goto('/ai-governance/copilot');
    await expect(page.locator('body')).toContainText(/copilot|planner|production|المساعد/i);
  });
});
