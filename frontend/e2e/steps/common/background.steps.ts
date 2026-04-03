import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given } = createBdd(test);

// ── Background steps (no-op for frontend tests) ──
// 後端 BDD 測試會實際建立資料庫資料，前端測試只需要忽略這些 Given 步驟

Given('系統中有以下使用者帳號：', async ({}, _dataTable) => {
  // No-op: frontend tests use mock/demo data
});

Given('系統中有以下證照科目分類：', async ({}, _dataTable) => {
  // No-op
});

Given('使用者 {string} 備考科目為 {string}（科目 ID: {int}）', async ({}) => {
  // No-op
});

Given('使用者 {string} 帳號狀態為 {string}', async ({}) => {
  // No-op
});

Given('使用者 {string} 尚未完成 Onboarding', async ({}) => {
  // No-op
});

Given('使用者 {string} 已完成 Onboarding', async ({}) => {
  // No-op
});

Given('使用者 {string} 訂閱方案為 {string}', async ({}) => {
  // No-op
});

Given('使用者 {string} 角色為 {string}', async ({}) => {
  // No-op
});

Given('使用者 {string} 訂閱方案為 {string} 且角色為 {string}', async ({}) => {
  // No-op
});

Given('使用者 {string} 原本為 Email\\/密碼註冊方式', async ({}) => {
  // No-op
});

Given('使用者 {string} 已完成註冊驗證', async ({}) => {
  // No-op
});

Given('該使用者尚未建立任何學習歷程', async ({}) => {
  // No-op
});

Given('使用者 {string} 已建立至少一個備考科目的學習歷程', async ({}) => {
  // No-op
});

Given('使用者 {string} 已有 Google SSO 帳號且狀態為 {string}', async ({}) => {
  // No-op
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

Given('使用者在忘記密碼頁面已輸入 {string}', async ({ page }, email: string) => {
  await page.goto('/forgot-password');
  await page.getByPlaceholder('you@example.com').fill(email);
});
