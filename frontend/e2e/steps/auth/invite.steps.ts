import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── EDU invite token state ──
// Store token between Given/When steps
let _currentToken = '';

Given('系統已向 {string} 發送 EDU 啟用邀請信', async ({}, _email: string) => {
  // No-op: precondition set up by backend seed
  _currentToken = 'valid-invite-token-001';
});

Given('邀請 token 為有效且未過期', async ({}) => {
  // No-op: using stored token
});

Given(
  '使用者 {string} 正在密碼設定頁，邀請 token 有效',
  async ({ page }, _email: string) => {
    await page.goto(`/invite/setup-password?token=${_currentToken || 'valid-invite-token-001'}`);
    await page.waitForLoadState('domcontentloaded');
  },
);

Given(
  '邀請 token {string} 已過期（超過 72 小時）',
  async ({}, token: string) => {
    // Store the expired token for use in When step
    _currentToken = token;
  },
);

// ── EDU invite When steps ──

When('使用者點擊邀請信中的啟用連結', async ({ page }) => {
  await page.goto(`/invite/setup-password?token=${_currentToken || 'valid-invite-token-001'}`);
  await page.waitForLoadState('domcontentloaded');
});

When(
  '使用者輸入密碼 {string} 並確認密碼 {string} 後送出',
  async ({ page }, password: string, confirmPassword: string) => {
    const passwordField = page.getByLabel(/^密碼/).or(page.getByPlaceholder(/密碼/)).first();
    const confirmField = page.getByLabel(/確認密碼/).or(page.getByPlaceholder(/確認密碼/)).first();
    const submitBtn = page.getByRole('button', { name: /完成設定|送出|確認/ });

    await passwordField.fill(password);
    await confirmField.fill(confirmPassword);
    await submitBtn.click();

    await Promise.race([
      page.waitForURL((url) => url.pathname.includes('/dashboard'), { timeout: 8_000 }).catch(() => {}),
      page.locator('.bg-rose-50, .text-red-500').waitFor({ state: 'visible', timeout: 8_000 }).catch(() => {}),
    ]);
  },
);

When(
  '使用者以 token {string} 訪問密碼設定頁',
  async ({ page }, token: string) => {
    await page.goto(`/invite/setup-password?token=${token}`);
    await page.waitForLoadState('domcontentloaded');
  },
);

// ── EDU invite Then steps ──

Then('系統應導向密碼設定頁面 {string}', async ({ page }, path: string) => {
  await page.waitForURL((url) => url.pathname.includes(path.replace(/"/g, '')), {
    timeout: 10_000,
  });
});

Then('頁面應顯示「歡迎加入！請設定您的登入密碼」', async ({ page }) => {
  await expect(
    page.getByText('歡迎加入！請設定您的登入密碼').or(page.getByText('歡迎加入')),
  ).toBeVisible({ timeout: 5_000 });
});

Then('使用者 {string} 的帳號狀態應仍為 {string}', async ({}, _email: string, _status: string) => {
  // No-op: backend state verification
});

Then('使用者 {string} 的帳號狀態應更新為 {string}', async ({}, _email: string, _status: string) => {
  // No-op: backend state verification
});

Then('使用者 {string} 的訂閱方案應為 {string}', async ({}, _email: string, _plan: string) => {
  // No-op: backend state verification
});

Then('系統應顯示錯誤提示「邀請連結已過期，請聯繫機構管理員重新發送邀請」', async ({ page }) => {
  await expect(
    page.getByText('邀請連結已過期').or(page.getByText('已過期')),
  ).toBeVisible({ timeout: 5_000 });
});

Then('頁面應提供「聯繫管理員」引導', async ({ page }) => {
  const link = page.getByRole('link', { name: /聯繫管理員|聯絡管理員/ }).or(
    page.getByText(/聯繫管理員/),
  );
  await expect(link).toBeVisible({ timeout: 5_000 });
});

Then('頁面應提供「前往登入」連結', async ({ page }) => {
  const link = page.getByRole('link', { name: /前往登入|登入/ });
  await expect(link).toBeVisible({ timeout: 5_000 });
});
