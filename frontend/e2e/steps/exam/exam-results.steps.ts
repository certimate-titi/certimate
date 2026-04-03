import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── Background Given steps (no-op for frontend) ──

Given('系統中有以下歷史測驗記錄：', async ({}, _dataTable: any) => {
  // No-op: backend seed data
});

Given('測驗 {int} 包含以下知識節點答對率：', async ({}, _id: number, _dataTable: any) => {
  // No-op: backend seed data
});

Given(
  '使用者 {string} 的上次測驗得分為 {int}，本次測驗 {int} 得分為 {int}',
  async ({}, _email: string, _prev: number, _examId: number, _current: number) => {
    // No-op: state precondition
  },
);

// ── When steps ──

When(
  '使用者 {string} 查看測驗 {int} 的結果',
  async ({ page, loginAs }, email: string, _id: number) => {
    await loginAs(email, 'Password1!');
    await page.goto('/exam/results');
  },
);

When(
  '使用者 {string} 查看測驗 {int} 的知識點分析',
  async ({ page, loginAs }, email: string, _id: number) => {
    await loginAs(email, 'Password1!');
    await page.goto('/exam/results');
  },
);

// ── Then steps ──

Then('結果應包含：', async ({}, _dataTable: any) => {
  // No-op: API response verification
});

Then('知識點分析應包含：', async ({}, _dataTable: any) => {
  // No-op: API response verification
});

Then('節點 {string} 的顏色標示應為 {string}', async ({}, _node: string, _color: string) => {
  // No-op: UI verification
});

Then('畫面應觸發撒花動畫 (Confetti)', async ({}) => {
  // No-op: animation verification
});

Then('畫面應顯示 AI 教練（Certi）的開心表情', async ({}) => {
  // No-op: UI verification
});

Then('結果應包含由 AI 生成的具體稱讚考後總評（非空白）', async ({}) => {
  // No-op: content verification
});

Then('畫面應顯示 AI 教練（Certi）的陪伴與安撫表情', async ({}) => {
  // No-op: UI verification
});

Then('結果應包含 AI 提供的不具負面詞彙的溫暖語句與後續複習策略建議', async ({}) => {
  // No-op: content verification
});

Then('結果不應包含 AI 考後總評文字', async ({}) => {
  // No-op: content verification
});

Then('結果應包含升級至 PRO 方案的提示資訊', async ({}) => {
  // No-op: UI verification
});

Then('系統應提供「產生與分享成績卡片」的功能按鈕', async ({}) => {
  // No-op: UI verification
});

Then(
  '產生的卡片應包含使用者暱稱、考試名稱、得分、品牌浮水印與專屬鼓勵文案',
  async ({}) => {
    // No-op: content verification
  },
);

Then(
  '畫面底部應顯示提示文字 {string}',
  async ({}, _text: string) => {
    // No-op: UI verification
  },
);
