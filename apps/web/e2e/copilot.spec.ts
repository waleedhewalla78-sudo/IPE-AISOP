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

test.describe('Copilot R1 smoke', () => {
  test.beforeEach(async ({ page }) => {
    await stubLocalAuth(page);
    await page.addInitScript(() => localStorage.clear());
  });

  test('unauthenticated copilot route redirects to login', async ({ page }) => {
    await page.goto('/ai-governance/copilot');
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
  });

  test('legacy /copilot redirects to ai-governance/copilot when authenticated', async ({ page }) => {
    await page.addInitScript((token) => {
      localStorage.setItem('access_token', token);
    }, AUTH_TOKEN);
    await page.goto('/copilot');
    await expect(page).toHaveURL(/\/ai-governance\/copilot/, { timeout: 10000 });
  });

  test('release1 sidebar shows Copilot and navigates to panel', async ({ page }) => {
    await page.addInitScript((token) => {
      localStorage.setItem('access_token', token);
    }, AUTH_TOKEN);
    await page.goto('/workspace');
    const copilotLink = page.getByRole('link', { name: /copilot/i });
    await expect(copilotLink).toBeVisible({ timeout: 10000 });
    await copilotLink.click();
    await expect(page).toHaveURL(/\/ai-governance\/copilot/, { timeout: 10000 });
    await expect(page.locator('body')).toContainText(/copilot|planner|production/i);
  });

  test('copilot panel renders after direct navigation', async ({ page }) => {
    await page.addInitScript((token) => {
      localStorage.setItem('access_token', token);
    }, AUTH_TOKEN);
    await page.goto('/ai-governance/copilot');
    await expect(page.locator('body')).toContainText(/copilot|planner|production/i);
  });
});
