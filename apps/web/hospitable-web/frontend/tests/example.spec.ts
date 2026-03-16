import { test, expect } from '@playwright/test';

test('homepage should load', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Hospitable/i);
});
