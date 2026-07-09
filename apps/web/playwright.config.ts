import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  testMatch: ['e2e/**/*.spec.ts', 'tests/**/*.perf.test.ts'],
  timeout: 30000,
  retries: 0,
  use: {
    baseURL: 'http://localhost:8082',
    headless: true,
  },
  projects: [
    {
      name: 'desktop',
      use: { viewport: { width: 1920, height: 1080 } },
    },
    {
      name: 'tablet',
      use: { viewport: { width: 768, height: 1024 } },
    },
    {
      name: 'mobile',
      use: { viewport: { width: 375, height: 667 } },
    },
  ],
  webServer: {
    command: 'npm run dev',
    port: 8082,
    reuseExistingServer: false,
    timeout: 120_000,
    env: {
      ...process.env,
      VITE_RELEASE_PROFILE: process.env.VITE_RELEASE_PROFILE ?? 'release1',
      VITE_API_BASE_URL: process.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:9',
    },
  },
});
