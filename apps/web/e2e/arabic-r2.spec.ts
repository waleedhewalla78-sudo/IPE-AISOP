import { test, expect } from '@playwright/test';

const TENANT_ID = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';

function buildDevJwt(): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(
    JSON.stringify({
      sub: 'arabic-e2e',
      tenant_id: TENANT_ID,
      role: 'planner',
      exp: Math.floor(Date.now() / 1000) + 86400,
    }),
  );
  return `${header}.${payload}.dev-signature`;
}

async function seedArabicSession(page: import('@playwright/test').Page) {
  const token = buildDevJwt();
  await page.addInitScript(
    ({ jwt, loc }: { jwt: string; loc: string }) => {
      localStorage.setItem('access_token', jwt);
      if (!localStorage.getItem('ipe_e2e_locale_seeded')) {
        localStorage.setItem('ipe_locale', loc);
        localStorage.setItem('ipe_e2e_locale_seeded', '1');
      }
    },
    { jwt: token, loc: 'ar' },
  );
}

async function mockProtectedApis(page: import('@playwright/test').Page) {
  await page.route('**/api/v1/**', async (route) => {
    const url = route.request().url();
    if (url.includes('/auth/')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            access_token: buildDevJwt(),
            refresh_token: 'refresh-dev',
            user: { email: 'Ahmed@nour', full_name: 'Ahmed Nour', role: 'planner' },
          },
        }),
      });
      return;
    }
    if (url.includes('/analytics/executive-summary')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            ai_otd_pct: 87.5,
            manual_otd_pct: 82,
            avg_planning_cycle_days: 3,
            inventory_value: 0,
            delay_coverage_pct: 0,
            otd_trend: [],
          },
        }),
      });
      return;
    }
    if (url.includes('/analytics/cost-of-chaos')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: { period: '7d', total_chaos_usd: 12500, categories: [], top_mos: [], war_room_links: [] },
        }),
      });
      return;
    }
    if (url.includes('/analytics/delay-breakdown')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: [] }),
      });
      return;
    }
    if (url.includes('/dashboard/alerts')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: { alerts: [] } }),
      });
      return;
    }
    if (url.includes('/war-room/recovery-plan')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: { recovery_options: [] } }),
      });
      return;
    }
    if (url.includes('/feasibility/queue')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: [] }),
      });
      return;
    }
    if (url.includes('/feasibility/kpis')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: { avg_feasibility_score: 78, active_bottlenecks: 1, orders_at_risk: 2, otd_pct: null },
        }),
      });
      return;
    }
    if (url.includes('/capacity/analyze') || url.includes('/capacity/schedule')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: { bottlenecks: [], schedule: { assignments: [] } } }),
      });
      return;
    }
    if (url.includes('/scenario')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: { scenarios: [] } }),
      });
      return;
    }
    if (url.includes('/demand/')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data: { forecasts: [], mape_pct: null } }),
      });
      return;
    }
    if (url.includes('/copilot/')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: { session_id: 'e2e', agent: 'Planner', follow_up_suggestions: [] },
        }),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true, data: {} }),
    });
  });
}

test.describe('Arabic RTL smoke (R2 S5)', () => {
  test.beforeEach(async ({ page }) => {
    await seedArabicSession(page);
    await mockProtectedApis(page);
  });

  test('sets RTL direction and persists locale', async ({ page }) => {
    await page.goto('/planning/dashboard');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
    await expect(page.locator('html')).toHaveAttribute('lang', 'ar');

    const locale = await page.evaluate(() => localStorage.getItem('ipe_locale'));
    expect(locale).toBe('ar');
  });

  test('sidebar toggle switches locale and reloads', async ({ page }) => {
    await page.goto('/planning/dashboard');
    await page.waitForLoadState('networkidle');
    const toggle = page.getByTestId('language-toggle');
    await expect(toggle).toBeVisible();
    await expect(toggle).toHaveText('EN');

    await toggle.click();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');

    const locale = await page.evaluate(() => localStorage.getItem('ipe_locale'));
    expect(locale).toBe('en');
  });

  test('Arabic labels on 8+ screens', async ({ page }) => {
    const screens: { path: string; text: string }[] = [
      { path: '/planning/control-tower', text: 'برج المراقبة' },
      { path: '/planning/resolution', text: 'مركز الحلول' },
      { path: '/planning/schedule', text: 'الجدولة' },
      { path: '/command-center/dashboard', text: 'عرض تنفيذي موحّد' },
      { path: '/platform/admin', text: 'لوحة الإدارة' },
      { path: '/ai-governance/copilot', text: 'المساعد الذكي' },
      { path: '/planning/demand', text: 'استشعار الطلب' },
      { path: '/planning/scenarios', text: 'منصة السيناريوهات' },
    ];

    for (const { path, text } of screens) {
      await page.goto(path);
      await page.waitForLoadState('domcontentloaded');
      await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
      await expect(page.getByText(text, { exact: false }).first()).toBeVisible({ timeout: 15000 });
    }
  });

  test('login page renders Arabic auth labels', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
    await expect(page.getByText('تسجيل الدخول إلى IPE')).toBeVisible();
    await expect(page.getByText('البريد الإلكتروني')).toBeVisible();
  });
});
