import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { When, Then } = createBdd(test);

When(
  '使用者以 Email {string} 申請密碼重設',
  async ({ page }, email: string) => {
    await page.goto('/forgot-password');
    await page.getByPlaceholder('you@example.com').fill(email);
    await page.getByRole('button', { name: '發送重設連結' }).click();
    await page.waitForTimeout(2_000);
  },
);

When('使用者在忘記密碼頁面未輸入任何 Email', async ({ page }) => {
  await page.goto('/forgot-password');
});

When('使用者清空 Email 欄位', async ({ page }) => {
  await page.getByPlaceholder('you@example.com').fill('');
});

Then('送出按鈕應為停用狀態，無法點擊', async ({ page }) => {
  const submitBtn = page.getByRole('button', { name: '發送重設連結' });
  await expect(submitBtn).toBeDisabled();
});

Then('頁面應顯示密碼重設信已寄出的確認訊息', async ({ page }) => {
  await expect(page.getByText('重設信件已寄出')).toBeVisible();
});

Then(
  '確認訊息中應包含使用者輸入的 Email {string}',
  async ({ page }, email: string) => {
    await expect(page.getByText(email)).toBeVisible();
  },
);

Then('頁面應提供返回登入頁面的連結', async ({ page }) => {
  await expect(page.getByRole('link', { name: /返回登入/ })).toBeVisible();
});
