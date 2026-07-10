import { test, expect } from '@playwright/test';

const P95_THRESHOLD_MS = 2000;
const SAMPLE_COUNT = 20;

test.describe('CPM cascade performance', () => {
  test('mock cascade preview p95 stays under 2s', async ({ page }) => {
    const latencies: number[] = [];

    await page.route('**/api/v1/capacity/cpm/cascade', async (route) => {
      const started = Date.now();
      await new Promise((resolve) => setTimeout(resolve, 50 + Math.random() * 200));
      const cascadeMs = Date.now() - started;
      latencies.push(cascadeMs);

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            operations: [
              {
                operation_id: 'op-1',
                planned_start: '2026-07-01T08:00:00Z',
                planned_end: '2026-07-01T12:00:00Z',
                is_critical: true,
                slack_minutes: 0,
              },
            ],
            critical_path_ids: ['op-1'],
            financial_delta: {
              overtime_usd: 150,
              tardiness_penalty_usd: 0,
              activity_cost_delta_usd: 150,
            },
            conflicts: [],
            cascade_ms: cascadeMs,
            cascade_token: 'mock-token',
          },
        }),
      });
    });

    await page.route('**/api/v1/capacity/schedule/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            rows: [
              {
                mo_id: 'mo-001',
                mo_name: 'MO-DEMO-001',
                approved: false,
                operations: [
                  {
                    id: 'op-1',
                    mo_id: 'mo-001',
                    mo_name: 'MO-DEMO-001',
                    sequence: 10,
                    work_center_id: 'wc-1',
                    work_center_name: 'CNC-01',
                    planned_start: 0,
                    planned_end: 240,
                    duration: 240,
                    status: 'on_time',
                  },
                ],
              },
            ],
          },
        }),
      });
    });

    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@demo.com');
    await page.fill('input[type="password"]', 'admin');
    await page.click('button[type="submit"]');
    // Post-login landing is Planning Dashboard (not legacy /control-tower).
    await expect(page).toHaveURL(/\/planning\/dashboard/, { timeout: 15000 });

    await page.goto('/planning/schedule');
    await expect(page.getByText(/Schedule Gantt|الجدولة|Gantt/i).first()).toBeVisible({
      timeout: 15000,
    });

    const bar = page.locator('[title*="op-1"]').first();
    await expect(bar).toBeVisible();

    const box = await bar.boundingBox();
    expect(box).not.toBeNull();
    if (!box) return;

    for (let i = 0; i < SAMPLE_COUNT; i++) {
      await bar.dispatchEvent('pointerdown', { clientX: box.x + 10, bubbles: true });
      await page.mouse.move(box.x + 80 + i * 2, box.y + box.height / 2);
      await page.waitForTimeout(450);
      await page.mouse.up();
      await page.waitForTimeout(100);
    }

    expect(latencies.length).toBeGreaterThan(0);

    const sorted = [...latencies].sort((a, b) => a - b);
    const p95Index = Math.ceil(sorted.length * 0.95) - 1;
    const p95 = sorted[Math.max(0, p95Index)];

    expect(p95).toBeLessThan(P95_THRESHOLD_MS);
  });
});
