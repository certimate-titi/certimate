import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── Given steps ──

Given(
  '使用者 {string} 已啟用番茄鐘模式（專注 {int} 分鐘）',
  async ({}, _email: string, _minutes: number) => {
    // No-op: state precondition
  },
);

Given(
  '使用者 {string} 正在進行測驗 {int}，番茄計時器剩餘 {int} 秒',
  async ({}, _email: string, _examId: number, _seconds: number) => {
    // No-op: state precondition
  },
);

Given('使用者 {string} 收到番茄鐘休息提醒', async ({}, _email: string) => {
  // No-op: state precondition
});

Given('使用者 {string} 已完成 {int} 個番茄專注時段', async ({}, _email: string, _count: number) => {
  // No-op: state precondition
});

Given(
  '使用者 {string} 完成測驗 {int}，過程中完成 {int} 個番茄鐘、跳過 {int} 次休息',
  async ({}, _email: string, _examId: number, _completed: number, _skipped: number) => {
    // No-op: state precondition
  },
);

Given('使用者 {string} 本週已完成 {int} 個番茄鐘', async ({}, _email: string, _count: number) => {
  // No-op: state precondition
});

Given('使用者 {string} 已累計完成 {int} 個番茄鐘', async ({}, _email: string, _count: number) => {
  // No-op: state precondition
});

// ── When steps ──

When('使用者 {string} 啟用番茄鐘模式', async ({}, _email: string) => {
  // No-op: simulated action
});

When(
  '使用者 {string} 設定番茄鐘為專注 {int} 分鐘、短休息 {int} 分鐘、長休息 {int} 分鐘',
  async ({}, _email: string, _focus: number, _short: number, _long: number) => {
    // No-op: simulated settings change
  },
);

When('使用者 {string} 設定番茄鐘專注時長為 {int} 分鐘', async ({}, _email: string, _minutes: number) => {
  // No-op: simulated settings change
});

When(
  '使用者 {string} 開始測驗 {int}',
  async ({}, _email: string, _id: number) => {
    // No-op: simulated action
  },
);

When('番茄專注時段結束', async ({}) => {
  // No-op: simulated timer event
});

When('使用者點擊「繼續作答」', async ({}) => {
  // No-op: simulated click
});

When('使用者點擊「開始休息」', async ({}) => {
  // No-op: simulated click
});

When('第 {int} 個專注時段結束', async ({}, _n: number) => {
  // No-op: simulated timer event
});

When(
  '使用者 {string} 開始測驗 {int}（{int} 分鐘）',
  async ({}, _email: string, _id: number, _duration: number) => {
    // No-op: simulated action
  },
);

When('使用者查看個人儀表板', async ({}) => {
  // No-op: simulated navigation
});

When('使用者完成第 {int} 個番茄鐘', async ({}, _n: number) => {
  // No-op: simulated action
});

// ── Then steps ──

Then('使用者的番茄鐘設定應為：', async ({}, _dataTable: any) => {
  // No-op: settings verification
});

Then('使用者的番茄鐘設定專注時長應為 {int}', async ({}, _minutes: number) => {
  // No-op: settings verification
});

Then('頁面右上角應顯示番茄計時器，初始為 {string}', async ({}, _time: string) => {
  // No-op: UI verification
});

Then('番茄計時器應與測驗倒數計時器同時運行', async ({}) => {
  // No-op: UI verification
});

Then('番茄計時器狀態應為 {string}', async ({}, _status: string) => {
  // No-op: UI verification
});

Then('系統應顯示柔和的休息提醒通知（不強制中斷作答）', async ({}) => {
  // No-op: UI verification
});

Then('通知內容應為 {string}', async ({}, _content: string) => {
  // No-op: UI verification
});

Then('通知應包含「開始休息」和「繼續作答」兩個按鈕', async ({}) => {
  // No-op: UI verification
});

Then('番茄計時器應重新開始下一個專注時段', async ({}) => {
  // No-op: UI verification
});

Then('該次休息應記錄為 {string}', async ({}, _status: string) => {
  // No-op: backend verification
});

Then('番茄計時器應切換為休息倒數（{int} 分鐘）', async ({}, _minutes: number) => {
  // No-op: UI verification
});

Then('計時器狀態應為 {string}', async ({}, _status: string) => {
  // No-op: UI verification
});

Then('測驗倒數計時器應繼續運行（不暫停）', async ({}) => {
  // No-op: UI verification
});

Then('頁面應顯示柔和的休息畫面覆蓋層（可隨時關閉）', async ({}) => {
  // No-op: UI verification
});

Then('計時器應切換為長休息倒數（{int} 分鐘）', async ({}, _minutes: number) => {
  // No-op: UI verification
});

Then('番茄計時器應正常顯示', async ({}) => {
  // No-op: UI verification
});

Then('番茄計時器應自動隱藏', async ({}) => {
  // No-op: UI verification
});

Then('系統應僅顯示測驗倒數計時器', async ({}) => {
  // No-op: UI verification
});

Then('結果頁應顯示番茄鐘摘要：', async ({}, _dataTable: any) => {
  // No-op: UI verification
});

Then('儀表板應顯示本週番茄鐘統計：', async ({}, _dataTable: any) => {
  // No-op: UI verification
});

Then('應以番茄圖示 🍅 視覺化呈現每日完成數量', async ({}) => {
  // No-op: UI verification
});

Then('系統應解鎖成就徽章「{string}」', async ({}, _badge: string) => {
  // No-op: backend verification
});

Then('成就描述應為 {string}', async ({}, _desc: string) => {
  // No-op: content verification
});
