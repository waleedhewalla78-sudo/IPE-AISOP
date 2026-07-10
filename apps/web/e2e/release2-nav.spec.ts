import { test, expect } from '@playwright/test';

const AUTH_TOKEN =
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0Iiwicm9sZSI6InBsYW5uZXIiLCJ0ZW5hbnRfaWQiOiJhMGVlYmM5OS05YzBiLTRlZjgtYmI2ZC02YmI5YmQzODBhMTEiLCJleHAiOjk5OTk5OTk5OTl9.sig';

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

/**
 * Requires dev server with VITE_RELEASE_PROFILE=release2
 * Run: VITE_RELEASE_PROFILE=release2 npx playwright test e2e/release2-nav.spec.ts
 */
test.describe('Release 2 navigation', () => {
  test.beforeEach(async ({ page }) => {
    await stubLocalAuth(page);
    await page.addInitScript((token) => {
      localStorage.clear();
      localStorage.setItem('access_token', token);
    }, AUTH_TOKEN);
  });

  test('sidebar shows Copilot in release2', async ({ page }) => {
    await page.goto('/workspace');
    await expect(page.getByRole('link', { name: /copilot/i })).toBeVisible({ timeout: 10000 });
  });

  test('planning hub shows Demand and Scenarios tabs', async ({ page }) => {
    await page.goto('/planning/control-tower');
    await expect(page.getByRole('link', { name: /^demand$/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('link', { name: /^scenarios$/i })).toBeVisible({ timeout: 10000 });
  });

  test('navigates to demand and scenarios pages', async ({ page }) => {
    await page.goto('/planning/demand');
    await expect(page.locator('body')).toContainText(/demand|forecast/i);

    await page.goto('/planning/scenarios');
    await expect(page.locator('body')).toContainText(/scenario|simulate|what-if/i);
  });

  test('hides POST-R2 hubs (supply chain, shop floor)', async ({ page }) => {
    await page.goto('/workspace');
    await expect(page.getByText('Supply Chain')).not.toBeVisible();
    await expect(page.getByText('Shop Floor')).not.toBeVisible();
  });
});
