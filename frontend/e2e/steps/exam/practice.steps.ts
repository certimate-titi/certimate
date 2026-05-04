import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';
import { setResourceMode } from '../../mocks/data';

const { Given, When, Then } = createBdd(test);

// ── L95 /practice no-questions Layer 3 空態 ──
// 步驟與 L101 共享 setResourceMode；practice 頁要求 nodeId 帶入後進入 no-questions phase

When('使用者進入練習頁面（無題目情境）', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(async () => {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'alice@example.com', password: 'Password1!' }),
    });
    const data = await res.json();
    if (data.access_token) {
      localStorage.setItem('certimate_jwt_token', data.access_token);
      localStorage.setItem('certimate_remember', 'true');
    }
  });
  // mock /practice/nodes/{id}/questions 回空 → 進入 no-questions phase
  await page.goto('/practice?nodeId=node-no-questions&nodeName=測試節點');
  await page.waitForLoadState('networkidle').catch(() => {});
});

Then('practice 空態應顯示「尚無練習題」', async ({ page }) => {
  await expect(page.getByText('尚無練習題', { exact: false })).toBeVisible({ timeout: 5000 });
});

Then('practice 空態應提示「AI 出題任務尚未完成或已失敗」', async ({ page }) => {
  await expect(page.getByText('AI 出題任務尚未完成或已失敗', { exact: false })).toBeVisible();
});

Then('practice 空態應顯示「資源解析失敗」紅色警告塊', async ({ page }) => {
  await expect(page.getByText('資源解析失敗', { exact: false })).toBeVisible({ timeout: 5000 });
});

// 重用 L101 的 setup steps（在 knowledge-map.steps.ts 已定義）
// Given '使用者 X 所有資源狀態皆為 COMPLETED'
// Given '使用者 X 所有資源狀態皆為 FAILED'

// 註：F32 Background steps（備考科目、知識節點、練習題）由 common/background.steps.ts 提供

// ── isSuperAdmin 高等設定守衛 ──

Given('使用者 {string} 已登入為 SUPER_ADMIN', async ({ page }, _email: string) => {
  // mock USERS 已有 admin@certimate.com role=ADMIN（mock 不分 ADMIN / SUPER_ADMIN）
  // 為測試 isSuperAdmin 守衛區分，使用 setUserOverride 提升該 email 至 SUPER_ADMIN
  const { setUserOverride } = await import('../../mocks/data');
  setUserOverride('super@certimate.com', { role: 'SUPER_ADMIN' as any, subscription_plan: 'ULTRA' });
  await page.goto('/');
  await page.evaluate(async () => {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'super@certimate.com', password: '*' }),
    });
    const data = await res.json();
    if (data.access_token) {
      localStorage.setItem('certimate_jwt_token', data.access_token);
      localStorage.setItem('certimate_remember', 'true');
    }
  });
});

Given('使用者 {string} 已登入為 ADMIN', async ({ page }, _email: string) => {
  // mock USERS 已有 admin@example.com 為 ADMIN role
  await page.goto('/');
  await page.evaluate(async () => {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'admin@example.com', password: 'Password1!' }),
    });
    const data = await res.json();
    if (data.access_token) {
      localStorage.setItem('certimate_jwt_token', data.access_token);
      localStorage.setItem('certimate_remember', 'true');
    }
  });
});

When('使用者進入系統設定頁', async ({ page }) => {
  await page.goto('/super-admin/settings');
  await page.waitForLoadState('networkidle').catch(() => {});
});

Then('頁面應顯示 {string} 標題', async ({ page }, title: string) => {
  await expect(page.getByRole('heading', { name: title, exact: false })).toBeVisible({ timeout: 5000 });
});

Then('頁面應 redirect 至營運儀表板', async ({ page }) => {
  await page.waitForURL('**/super-admin/dashboard/**', { timeout: 5000 }).catch(() => {});
  expect(page.url()).toContain('/super-admin/dashboard');
});
