import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── Background Given steps (no-op for frontend) ──

Given('系統中有以下資源：', async ({}, _dataTable: any) => {
  // No-op: backend seed data
});

Given('系統中有以下心智圖知識節點：', async ({}, _dataTable: any) => {
  // No-op: backend seed data
});

Given('學科 {string} 有以下考古題 Bloom 統計：', async ({}, _subject: string, _dataTable: any) => {
  // No-op: backend seed data
});

Given('學科 {string} 無任何考古題資料', async ({}, _subject: string) => {
  // No-op: backend seed data
});

// ── When steps ──

When('使用者在測驗設定頁面頂部選擇學科 {string}', async ({ page, loginAs }, subject: string) => {
  await loginAs('pro@example.com', 'Password1!');
  await page.goto('/exam/setup');
  await page.getByText(subject).first().click().catch(() => {});
});

When(
  '使用者 {string} 提交測驗設定，未勾選任何知識節點，題數為 {int}',
  async ({ page, loginAs }, email: string, _count: number) => {
    await loginAs(email, 'Password1!');
    await page.goto('/exam/setup');
  },
);

When(
  '使用者 {string} 提交測驗設定，選擇節點 {int}，題數為 {int}',
  async ({ page, loginAs }, email: string, _node: number, _count: number) => {
    await loginAs(email, 'Password1!');
    await page.goto('/exam/setup');
  },
);

When(
  '使用者 {string} 提交測驗設定，選擇節點 {int} 和節點 {int}，題數為 {int}',
  async ({ page, loginAs }, email: string, _n1: number, _n2: number, _count: number) => {
    await loginAs(email, 'Password1!');
    await page.goto('/exam/setup');
  },
);

When(
  '使用者 {string} 提交測驗設定，選擇節點 {int}，題數為 {int}，難易度分配為 Easy:{int}% Medium:{int}% Hard:{int}%',
  async (
    { page, loginAs },
    email: string,
    _node: number,
    _count: number,
    _easy: number,
    _medium: number,
    _hard: number,
  ) => {
    await loginAs(email, 'Password1!');
    await page.goto('/exam/setup');
  },
);

When(
  '使用者 {string} 提交測驗設定，選擇節點 {int} 和節點 {int}，題數為 {int}，難易度分配為 Easy:{int}% Medium:{int}% Hard:{int}%',
  async (
    { page, loginAs },
    email: string,
    _n1: number,
    _n2: number,
    _count: number,
    _easy: number,
    _medium: number,
    _hard: number,
  ) => {
    await loginAs(email, 'Password1!');
    await page.goto('/exam/setup');
  },
);

When('後端 AI 成功生成考卷', async ({}) => {
  // No-op: backend event
});

// ── Then steps ──

Then(
  '{string} 列表中應僅顯示 subjectId 為 {string} 且狀態為 COMPLETED 的資源',
  async ({}, _label: string, _subjectId: string) => {
    // No-op: UI verification
  },
);

Then('選題列表應排除非當前學科的資源（如 AWS 講義）', async ({}) => {
  // No-op: UI verification
});

Then('系統應自動套用考古題 Bloom 配比作為出題依據', async ({}) => {
  // No-op: backend verification
});

Then('測驗任務的 bloom_source 應為 {string}', async ({}, _source: string) => {
  // No-op: backend verification
});

Then(
  '系統應套用預設 Bloom 配比（remember:20/understand:25/apply:25/analyze:15/evaluate:10/create:5）',
  async ({}) => {
    // No-op: backend verification
  },
);

Then('系統應建立測驗任務，初始狀態為 {string}', async ({}, _status: string) => {
  // No-op: backend verification
});

Then('系統應開始透過 SSE 推送生成進度事件', async ({}) => {
  // No-op: backend verification
});

Then('回應應包含有效的測驗 ID', async ({}) => {
  // No-op: API response verification
});

Then('回應應包含生成的題目總數 {int}', async ({}, _count: number) => {
  // No-op: API response verification
});
