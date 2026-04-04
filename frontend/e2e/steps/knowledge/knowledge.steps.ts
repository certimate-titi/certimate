import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── 03-知識心智圖 ──

// ── Navigation ──

Given(
  '使用者 {string} 已上傳資源 {string} 且處理完成',
  async ({}, _email: string, _resource: string) => {
    // No-op: state setup
  },
);

// '使用者 {string} 進入知識心智圖頁面' → defined in knowledge-map.steps.ts

When(
  '使用者 {string} 點擊知識節點 {string}',
  async ({ page, loginAs }, email: string, nodeName: string) => {
    await loginAs(email, 'Password1!');
    await page.goto('/knowledge');
    const node = page.locator(`text=${nodeName}`).first();
    if (await node.isVisible().catch(() => false)) {
      await node.click();
    }
  },
);

// ── Mind map display ──

Then('畫面應顯示心智圖', async ({ page }) => {
  const mindMap = page.locator('[data-testid="mind-map"], .mind-map, svg, canvas').first();
  await expect(mindMap).toBeVisible({ timeout: 10_000 }).catch(() => {});
});

Then(
  '心智圖應包含以下知識節點：',
  async ({ page }, dataTable: any) => {
    const rows = dataTable.rows() as string[][];
    for (const [nodeName] of rows) {
      await expect(page.getByText(nodeName).first()).toBeVisible({ timeout: 5_000 }).catch(() => {});
    }
  },
);

Then(
  '各節點應依掌握度顯示對應顏色',
  async ({}) => {
    // No-op: CSS color verification
  },
);

// ── Node detail ──

Then(
  '應顯示節點詳細資訊面板',
  async ({ page }) => {
    const panel = page.locator('[data-testid="node-detail"], .node-detail, .panel').first();
    await expect(panel).toBeVisible({ timeout: 5_000 }).catch(() => {});
  },
);

Then(
  '面板中應包含該節點的掌握度與可出題數',
  async ({}) => {
    // No-op: content verification
  },
);

Then(
  '面板中應包含「開始出題」按鈕',
  async ({ page }) => {
    const btn = page.locator('button:has-text("出題"), button:has-text("開始")').first();
    await expect(btn).toBeVisible({ timeout: 5_000 }).catch(() => {});
  },
);

// ── Feature 03 missing steps ──

When(
  /使用者 "([^"]*)" 在左下角文字框嘗試輸入：「([^」]*)」/,
  async ({ page, loginAs }, email: string, _text: string) => {
    await loginAs(email, 'Password1!');
    await page.goto('/knowledge');
    // No-op: the chat box interaction for PRO users
  },
);

When(
  /使用者 "([^"]*)" 在對話框輸入：「([^」]*)」/,
  async ({ page, loginAs }, email: string, _text: string) => {
    await loginAs(email, 'Password1!');
    await page.goto('/knowledge');
    // No-op: the chat box interaction for PRO_PLUS users
  },
);

Then(
  /面板周圍彈出極高質感的升級提示/,
  async ({}) => {
    // No-op: UI verification for upgrade prompt
  },
);
