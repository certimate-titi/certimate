import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── Signup page navigation ──

Given('使用者在註冊頁面', async ({ page }) => {
  await page.goto('/signup');
});

// ── Signup actions ──

When(
  '使用者以 Email {string} 和密碼 {string} 進行註冊',
  async ({ page }, email: string, password: string) => {
    await page.goto('/signup');
    await page.getByPlaceholder('電子郵件').fill(email);
    // Trigger blur to activate email validation
    await page.getByPlaceholder('密碼 (至少 8 個字元)').fill(password);
    await page.locator('#terms').check();
    await page.getByRole('button', { name: '免費註冊' }).click();
    await page.waitForTimeout(1_500);
  },
);

When(
  '使用者以 Email {string} 和密碼 {string} 進行註冊，但未勾選同意「服務條款與隱私權宣告」',
  async ({ page }, email: string, password: string) => {
    await page.goto('/signup');
    await page.getByPlaceholder('電子郵件').fill(email);
    await page.getByPlaceholder('密碼 (至少 8 個字元)').fill(password);
    // Intentionally NOT checking the terms checkbox
    await page.getByRole('button', { name: '免費註冊' }).click();
    await page.waitForTimeout(500);
  },
);

// ── Password strength ──

When('使用者輸入密碼 {string}', async ({ page }, password: string) => {
  await page.goto('/signup');
  await page.getByPlaceholder('密碼 (至少 8 個字元)').fill(password);
});

When(
  '使用者在註冊頁面輸入密碼 {string}',
  async ({ page }, password: string) => {
    await page.goto('/signup');
    await page.getByPlaceholder('密碼 (至少 8 個字元)').fill(password);
  },
);

Then('密碼強度指示條應顯示 {string}', async ({ page }, level: string) => {
  await expect(page.getByText(`密碼強度：${level}`)).toBeVisible();
});

// ── Terms & Privacy modals ──

When('使用者在註冊頁面點擊「服務條款」連結', async ({ page }) => {
  await page.goto('/signup');
  await page.getByRole('button', { name: '服務條款' }).click();
});

When('使用者在註冊頁面點擊「隱私權政策」連結', async ({ page }) => {
  await page.goto('/signup');
  await page.getByRole('button', { name: '隱私權政策' }).click();
});

Then('系統應顯示服務條款彈窗', async ({ page }) => {
  await expect(page.getByRole('heading', { name: '服務條款' })).toBeVisible();
});

Then('系統應顯示隱私權政策彈窗', async ({ page }) => {
  await expect(
    page.getByRole('heading', { name: '隱私權政策' }),
  ).toBeVisible();
});

Then('彈窗內容應包含服務條款全文', async ({ page }) => {
  await expect(page.getByText('AI 內容免責聲明')).toBeVisible();
});

Then('彈窗內容應包含隱私權政策全文', async ({ page }) => {
  await expect(page.getByText('AI 模型訓練排除聲明')).toBeVisible();
});

// ── Password visibility (signup) ──

Given(
  '使用者在註冊頁面的密碼欄位輸入 {string}',
  async ({ page }, password: string) => {
    await page.goto('/signup');
    await page.getByPlaceholder('密碼 (至少 8 個字元)').fill(password);
  },
);

// ── Modal close ──

When('使用者點擊彈窗的關閉按鈕', async ({ page }) => {
  await page.getByRole('button', { name: '我已閱讀，關閉' }).click();
});

Then('服務條款彈窗應關閉', async ({ page }) => {
  await expect(page.getByRole('heading', { name: '服務條款' })).not.toBeVisible();
});

Then('隱私權政策彈窗應關閉', async ({ page }) => {
  await expect(page.getByRole('heading', { name: '隱私權政策' })).not.toBeVisible();
});

Then('使用者應回到註冊頁面', async ({ page }) => {
  await expect(page.getByRole('heading', { name: '建立帳號' })).toBeVisible();
});

// ── Google signup button ──

Then('頁面應有 Google 註冊按鈕', async ({ page }) => {
  await expect(page.getByRole('button', { name: /Google/ })).toBeVisible();
});
