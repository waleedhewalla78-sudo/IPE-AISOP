# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: e2e\login.spec.ts >> Login flow >> login and dashboard loads
- Location: e2e\login.spec.ts:7:3

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected pattern: /\/planning\/dashboard/
Received string:  "http://localhost:8082/login"
Timeout: 15000ms

Call log:
  - Expect "toHaveURL" with timeout 15000ms
    33 × unexpected value "http://localhost:8082/login"

```

```yaml
- heading "IPE Login" [level=1]
- text: Email
- textbox "admin@demo.com": Ahmed@nour
- text: Password
- textbox "Enter password": admin
- button "Sign In"
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const EMAIL = process.env.TEST_EMAIL ?? 'Ahmed@nour';
  4  | const PASSWORD = process.env.TEST_PASSWORD ?? 'admin';
  5  | 
  6  | test.describe('Login flow', () => {
  7  |   test('login and dashboard loads', async ({ page }) => {
  8  |     await page.goto('/login');
  9  |     await page.fill('input[type="email"]', EMAIL);
  10 |     await page.fill('input[type="password"]', PASSWORD);
  11 |     await page.click('button[type="submit"]');
  12 |     await page.waitForLoadState('networkidle');
> 13 |     await expect(page).toHaveURL(/\/planning\/dashboard/, { timeout: 15000 });
     |                        ^ Error: expect(page).toHaveURL(expected) failed
  14 |     await expect(page.locator('body')).toBeVisible();
  15 |   });
  16 | });
  17 | 
```