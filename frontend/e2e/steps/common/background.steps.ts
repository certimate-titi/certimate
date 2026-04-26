import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';
import { setUserOverride } from '../../mocks/data';

const { Given } = createBdd(test);

// ── Background steps — update mock state for user overrides ──

Given('系統中有以下使用者帳號：', async ({}, _dataTable) => {
  // No-op: mock data already has the Background users
});

Given('系統中有以下證照科目分類：', async ({}, _dataTable) => {
  // No-op
});

Given('使用者 {string} 備考科目為 {string}（科目 ID: {int}）', async ({}) => {
  // No-op
});

Given('使用者 {string} 帳號狀態為 {string}', async ({}, email: string, status: string) => {
  setUserOverride(email, { status });
});

Given('使用者 {string} 尚未完成 Onboarding', async ({}, email: string) => {
  setUserOverride(email, { onboarding_completed: false });
});

Given('使用者 {string} 已完成 Onboarding', async ({}, email: string) => {
  setUserOverride(email, { onboarding_completed: true });
});

Given('使用者 {string} 訂閱方案為 {string}', async ({}, email: string, plan: string) => {
  // Map display names to backend plan names
  const planMap: Record<string, string> = { FREE: 'FREE', PRO_199: 'PRO', PRO_PLUS_399: 'PRO_PLUS', ULTRA_1599: 'ULTRA' };
  setUserOverride(email, { subscription_plan: planMap[plan] || plan });
});

Given('使用者 {string} 角色為 {string}', async ({}, email: string, role: string) => {
  setUserOverride(email, { role });
});

Given('使用者 {string} 訂閱方案為 {string} 且角色為 {string}', async ({}, email: string, plan: string, role: string) => {
  const planMap: Record<string, string> = { FREE: 'FREE', PRO_199: 'PRO', PRO_PLUS_399: 'PRO_PLUS', ULTRA_1599: 'ULTRA' };
  setUserOverride(email, { subscription_plan: planMap[plan] || plan, role });
});

Given('使用者 {string} 原本為 Email\\/密碼註冊方式', async ({}) => {
  // No-op
});

Given('使用者 {string} 已完成註冊驗證', async ({}, email: string) => {
  setUserOverride(email, { status: '已啟用' });
});

Given('該使用者尚未建立任何學習歷程', async ({}) => {
  // No-op: mock data doesn't track learning journeys
});

Given('使用者 {string} 已建立至少一個備考科目的學習歷程', async ({}, email: string) => {
  setUserOverride(email, { onboarding_completed: true });
});

Given('使用者已開啟服務條款彈窗', async ({ page }) => {
  await page.goto('/signup');
  await page.getByRole('button', { name: '服務條款' }).click();
});

Given('使用者已開啟隱私權政策彈窗', async ({ page }) => {
  await page.goto('/signup');
  await page.getByRole('button', { name: '隱私權政策' }).click();
});

Given('密碼欄位目前為明文顯示模式', async ({ page }) => {
  const toggleBtn = page.locator('#password').locator('..').getByRole('button');
  await toggleBtn.click();
});

Given('使用者尚未登入（無有效 JWT）', async ({ page }) => {
  // Clear any stored JWT tokens
  await page.goto('/');
  await page.evaluate(() => {
    localStorage.removeItem('certimate_jwt_token');
    sessionStorage.removeItem('certimate_jwt_token');
  });
});

Given('使用者在忘記密碼頁面已輸入 {string}', async ({ page }, email: string) => {
  await page.goto('/forgot-password');
  await page.getByPlaceholder('you@example.com').fill(email);
});
