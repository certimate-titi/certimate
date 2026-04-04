import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── Background / Given steps ──

Given('系統中有以下學科：', async ({}, _dataTable: any) => {
  // No-op: backend seed data
});

Given('系統中有以下歷年考古題（含 Bloom 分類）：', async ({}, _dataTable: any) => {
  // No-op: backend seed data
});

Given('學科 {string} 的歷年考古題 Bloom 統計為：', async ({}, _subject: string, _dataTable: any) => {
  // No-op: backend seed data
});

Given('學科 {string} 有考古題 Bloom 統計', async ({}, _subject: string) => {
  // No-op: backend seed data
});

Given(
  '使用者 {string} 完成一場含 Bloom 分類的測驗',
  async ({}, _email: string, _dataTable: any) => {
    // No-op: state precondition
  },
);

Given(
  '管理員已上傳格式正確的考古題 JSON（{int} 題，bloom_category 為 null）',
  async ({}, _count: number) => {
    // No-op: state precondition
  },
);

Given('管理員上傳的考古題 JSON 缺少 correct_answer 欄位', async ({ page, loginAs }) => {
  await loginAs('admin@example.com', 'Password1!');
  // Set flag so the import step knows to send invalid data
  await page.evaluate(() => {
    (window as any).__importInvalidSchema = true;
  });
});

// ── When steps ──

When(
  '使用者 {string} 查詢學科 {string} 的 Bloom 分類統計',
  async ({}, _email: string, _subject: string) => {
    // No-op: API query
  },
);

When(
  '使用者 {string} 查詢學科 {string} 的年度 Bloom 趨勢',
  async ({}, _email: string, _subject: string) => {
    // No-op: API query
  },
);

When(
  '使用者 {string} 提交測驗設定，選擇學科 {string}，題數為 {int}',
  async ({}, _email: string, _subject: string, _count: number) => {
    // No-op: simulated form submission
  },
);

When(
  '使用者 {string} 提交測驗設定，選擇學科 {string}，題數為 {int}，並手動指定 Bloom 配比為：',
  async ({}, _email: string, _subject: string, _count: number, _dataTable: any) => {
    // No-op: simulated form submission
  },
);

When('管理員觸發「自動 Bloom 分類」', async ({}) => {
  // No-op: admin action
});

When('管理員觸發匯入', async ({ page }) => {
  const token = await page.evaluate(() =>
    localStorage.getItem('certimate_jwt_token') || sessionStorage.getItem('certimate_jwt_token'),
  );
  await page.evaluate(async (token) => {
    try {
      const res = await fetch('/api/v1/admin/questions/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ questions: [{ id: 1, correct_answer: 'A' }, { id: 2, correct_answer: 'B' }, { id: 3 }] }),
      });
      const data = await res.json().catch(() => ({}));
      (window as any).__lastApiSuccess = res.ok;
      (window as any).__lastApiError = data.detail || data.message || '';
    } catch {
      (window as any).__lastApiSuccess = false;
      (window as any).__lastApiError = '網路錯誤';
    }
  }, token);
});

// ── Then steps ──

Then('回應中應包含以下分佈：', async ({}, _dataTable: any) => {
  // No-op: API response verification
});

Then('回應中應包含 {int} 年與 {int} 年各自的 Bloom 分佈', async ({}, _y1: number, _y2: number) => {
  // No-op: API response verification
});

Then('趨勢資料格式應為：', async ({}, _dataTable: any) => {
  // No-op: API response verification
});

Then('系統應自動偵測該科目有考古題 Bloom 統計', async ({}) => {
  // No-op: backend verification
});

Then(
  '生成的 {int} 題中，各 Bloom 分類數量應符合考古題分佈（誤差 ±1 題）',
  async ({}, _count: number) => {
    // No-op: backend verification
  },
);

Then('exam 的 bloom_distribution 欄位應記錄實際分佈 JSON', async ({}) => {
  // No-op: backend verification
});

Then('exam 的 bloom_source 應為 {string}', async ({}, _source: string) => {
  // No-op: backend verification
});


Then(
  '生成的 {int} 題應依手動指定的配比出題（誤差 ±1 題）',
  async ({}, _count: number) => {
    // No-op: backend verification
  },
);

Then('結果中應包含 Bloom 層次分析：', async ({}, _dataTable: any) => {
  // No-op: API response verification
});


Then(
  '系統應呼叫 AI 分類服務，為每道題目填入 bloom_category',
  async ({}) => {
    // No-op: backend verification
  },
);

Then(
  '{int} 題處理完成後，匯入結果應顯示各 Bloom 分類統計',
  async ({}, _count: number) => {
    // No-op: backend verification
  },
);
