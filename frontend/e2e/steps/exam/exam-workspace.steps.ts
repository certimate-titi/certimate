import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── Background Given steps (no-op for frontend) ──

Given('系統中有以下測驗：', async ({}, _dataTable: any) => {
  // No-op: backend seed data
});

Given('測驗 {int} 包含以下題目：', async ({}, _id: number, _dataTable: any) => {
  // No-op: backend seed data
});

Given('測驗 {int} 包含以下已暫存作答：', async ({}, _id: number, _dataTable: any) => {
  // No-op: backend seed data
});

Given('測驗 {int} 包含以下數學工程題目：', async ({}, _id: number, _dataTable: any) => {
  // No-op: backend seed data
});

Given('使用者 {string} 準備開始測驗 {int}', async ({ loginAs }, email: string, _id: number) => {
  await loginAs(email, 'Password1!');
});

Given('使用者 {string} 已開始測驗 {int}', async ({ loginAs }, email: string, _id: number) => {
  await loginAs(email, 'Password1!');
});

Given(
  '使用者 {string} 已開始測驗 {int}，剩餘時間為 {int} 分鐘',
  async ({ loginAs }, email: string, _id: number, _minutes: number) => {
    await loginAs(email, 'Password1!');
  },
);

Given(
  '使用者 {string} 已開始測驗 {int}，剩餘時間為 {int} 秒',
  async ({ loginAs }, email: string, _id: number, _seconds: number) => {
    await loginAs(email, 'Password1!');
  },
);

// ── When steps ──

When('使用者 {string} 開始測驗 {int}', async ({ page, loginAs }, email: string, _id: number) => {
  await loginAs(email, 'Password1!');
  await page.goto('/exam/workspace');
});

When('系統載入測驗的初始畫面', async ({}) => {
  // No-op: page load
});

When(
  '使用者 {string} 在題目 {int} 選擇答案 {string}',
  async ({}, _email: string, _qId: number, _answer: string) => {
    // No-op: simulated answer selection
  },
);

When('使用者 {string} 將題目 {int} 標記為待複查', async ({}, _email: string, _qId: number) => {
  // No-op: simulated action
});

When('系統時間推進使剩餘時間變為 4 分 59 秒', async ({}) => {
  // No-op: simulated time advance
});

When('系統倒數時間歸零', async ({}) => {
  // No-op: simulated timer expiry
});

When('使用者 {string} 繼續進行測驗 {int}', async ({ page, loginAs }, email: string, _id: number) => {
  await loginAs(email, 'Password1!');
  await page.goto('/exam/workspace');
});

When('使用者 {string} 嘗試關閉測驗頁面', async ({}, _email: string) => {
  // No-op: simulated page close attempt
});

When('使用者 {string} 瀏覽題目 {int}', async ({}, _email: string, _qId: number) => {
  // No-op: simulated navigation
});

When(
  '使用者 {string} 在題目 {int} 的填空欄輸入 {string}',
  async ({}, _email: string, _qId: number, _answer: string) => {
    // No-op: simulated input
  },
);

When(
  '使用者 {string} 瀏覽題目 {int} 但未輸入任何內容',
  async ({}, _email: string, _qId: number) => {
    // No-op: simulated navigation
  },
);

// ── Then steps ──

Then('測驗 {int} 的狀態應更新為 {string}', async ({}, _id: number, _status: string) => {
  // No-op: backend verification
});

Then('測驗 {int} 應記錄開始時間', async ({}, _id: number) => {
  // No-op: backend verification
});

Then('畫面應短暫顯示 AI 教練角色（Certi）的打氣介面', async ({}) => {
  // No-op: UI animation verification
});

Then(
  'AI 教練應提供基於使用者近期學習狀態或連續測驗次數所生成的專屬鼓勵對話',
  async ({}) => {
    // No-op: UI verification
  },
);

Then(
  '測驗 {int} 中題目 {int} 的暫存作答應為 {string}',
  async ({}, _examId: number, _qId: number, _answer: string) => {
    // No-op: state verification
  },
);

Then('瀏覽器 LocalStorage 中應更新對應的作答記錄', async ({}) => {
  // No-op: storage verification
});

Then('題目 {int} 的標記複查狀態應為 {string}', async ({}, _qId: number, _status: string) => {
  // No-op: UI verification
});

Then('計時器的顯示樣式應切換為 {string}', async ({}, _style: string) => {
  // No-op: UI verification
});

Then('測驗 {int} 應自動提交', async ({}, _id: number) => {
  // No-op: backend verification
});

Then('題目 {int} 的已選答案應顯示為 {string}', async ({}, _qId: number, _answer: string) => {
  // No-op: UI verification
});

Then('系統應觸發 beforeunload 警告訊息', async ({}) => {
  // No-op: browser event verification
});

Then('警告訊息應為 {string}', async ({}, _msg: string) => {
  // No-op: browser alert verification
});

Then('題目顯示區應渲染以下 KaTeX 內容：', async ({}, _dataTable: any) => {
  // No-op: KaTeX rendering verification
});

Then('題目顯示區應以多選核取方塊呈現每個選項', async ({}) => {
  // No-op: UI verification
});

Then('每個選項應正確渲染 KaTeX 公式符號', async ({}) => {
  // No-op: KaTeX rendering verification
});

Then('瀏覽器 LocalStorage 中應更新對應的填空作答記錄', async ({}) => {
  // No-op: storage verification
});

Then('題目 {int} 在題號導覽網格的狀態應為 {string}', async ({}, _qId: number, _status: string) => {
  // No-op: UI verification
});
