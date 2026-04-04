import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── Common Then steps ──

Then('操作成功', async ({ page }) => {
  // Check if the last step stored an API response (for API-only steps)
  const apiSuccess = await page.evaluate(() => (window as any).__lastApiSuccess);
  if (apiSuccess !== undefined) {
    // API-only step — check stored result
    if (!apiSuccess) throw new Error('API call returned error');
    return;
  }
  // UI-based check: verify no error messages visible
  const errorBanner = page.locator('.bg-rose-50');
  await expect(errorBanner).not.toBeVisible({ timeout: 5_000 });
});

Then('操作失敗', async ({ page }) => {
  // Check if a When step stored an API result (for API-only steps)
  const apiSuccess = await page.evaluate(() => (window as any).__lastApiSuccess);
  if (apiSuccess !== undefined) {
    if (apiSuccess) throw new Error('Expected operation to fail but API returned success');
    return; // API returned error → operation failed ✓
  }
  // UI-based check: verify at least one error message is visible
  const errorBanner = page.locator('.bg-rose-50, .text-red-400, .text-red-500, .text-rose-500').first();
  await expect(errorBanner).toBeVisible({ timeout: 5_000 });
});

Then('錯誤訊息應為 {string}', async ({ page }, message: string) => {
  // Check API-only result first
  const apiError = await page.evaluate(() => (window as any).__lastApiError);
  if (apiError !== undefined) {
    expect(apiError).toContain(message);
    return;
  }
  // UI-based check
  const error = page.locator('.bg-rose-50, .text-red-400, .text-red-500, .text-rose-500').filter({ hasText: message });
  await expect(error.first()).toBeVisible({ timeout: 5_000 });
});

Then('操作失敗，錯誤為「{string}」', async ({ page }, message: string) => {
  const apiError = await page.evaluate(() => (window as any).__lastApiError);
  if (apiError !== undefined) {
    expect(apiError).toContain(message);
    return;
  }
  const error = page.locator('.bg-rose-50, .text-red-400, .text-red-500, .text-rose-500').filter({ hasText: message });
  await expect(error.first()).toBeVisible({ timeout: 5_000 });
});

// ── Navigation ──

Then('系統應導向至 {string}', async ({ page }, destination: string) => {
  const urlMap: Record<string, string> = {
    '首次登入引導頁': '/onboarding',
    '個人儀表板首頁': '/dashboard',
    '登入頁': '/login',
  };
  const path = urlMap[destination] || destination;
  await page.waitForURL((url) => url.pathname.includes(path), {
    timeout: 10_000,
  });
});
