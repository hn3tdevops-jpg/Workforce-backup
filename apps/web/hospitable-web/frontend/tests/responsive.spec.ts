import { test, expect } from '@playwright/test';

test('mobile viewport renders', async ({ page }) => {
  // Set a mobile viewport similar to iPhone 12
  await page.setViewportSize({ width: 390, height: 844 });
  const res = await page.goto('/');
  expect(res && res.ok()).toBeTruthy();
  // Basic smoke checks
  await expect(page.locator('body')).toBeVisible();
});

