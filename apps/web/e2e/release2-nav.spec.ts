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
  await expect(page).toHaveURL(/\/planning\/dashboard/, { timeout: 15000 });
}

/**
 * Requires release2 profile (docker web-ui or Vite with VITE_RELEASE_PROFILE=release2).
 * Uses real Kong login — fake JWTs are rejected by ProtectedRoute when auth/info is keycloak.
 */
test.describe('Release 2 navigation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDemo(page);
  });

  test('sidebar shows Copilot in release2', async ({ page }) => {
    await page.goto('/workspace');
    await expect(
      page.getByRole('link', { name: /copilot|المساعد الذكي/i }),
    ).toBeVisible({ timeout: 10000 });
  });

  test('planning hub shows Demand and Scenarios tabs', async ({ page }) => {
    await page.goto('/planning/control-tower');
    await expect(page.getByRole('link', { name: /^demand$|استشعار الطلب/i })).toBeVisible({
      timeout: 10000,
    });
    await expect(page.getByRole('link', { name: /^scenarios$|منصة السيناريوهات/i })).toBeVisible({
      timeout: 10000,
    });
  });

  test('navigates to demand and scenarios pages', async ({ page }) => {
    await page.goto('/planning/demand');
    await expect(page.locator('body')).toContainText(/demand|forecast|استشعار|طلب/i);

    await page.goto('/planning/scenarios');
    await expect(page.locator('body')).toContainText(/scenario|simulate|what-if|سيناريو/i);
  });

  test('hides POST-R2 hubs (supply chain, shop floor)', async ({ page }) => {
    await page.goto('/workspace');
    await expect(page.getByText('Supply Chain')).not.toBeVisible();
    await expect(page.getByText('Shop Floor')).not.toBeVisible();
  });
});
