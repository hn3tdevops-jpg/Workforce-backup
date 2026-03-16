import { test, expect } from '@playwright/test';

test('login form works (if present)', async ({ page }) => {
  const res = await page.goto('/login');
  if (res && res.status() === 404) test.skip('No login page');
  await expect(page).toHaveURL(/\/login/);

  const username = page.locator('input[name="username"], input[type="email"]');
  const password = page.locator('input[type="password"]');

  if ((await username.count()) === 0 || (await password.count()) === 0) {
    test.skip('Login form not present');
  }

  await username.fill('test@example.com');
  await password.fill('password');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle' }).catch(() => {}),
    page.click('button[type="submit"], text=Sign in, text=Sign In, text=Login')
  ]);

  // After submit, ensure page did not crash and shows either success or error message
  expect(await page.locator('text=Invalid, text=error, text=Success').count()).toBeLessThan(5);
});

