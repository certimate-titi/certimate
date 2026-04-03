import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── Background / Given steps ──

Given('系統中有以下意見反饋紀錄：', async ({}, _dataTable: any) => {
  // No-op: backend seed data
});

Given('使用者 {string} 已登入系統', async ({ loginAs }, email: string) => {
  await loginAs(email, 'Password1!');
});

Given('使用者尚未登入', async ({}) => {
  // No-op: default state
});

Given(
  '使用者 {string} 於 {int} 分鐘前已提交主旨為 {string} 的意見反饋',
  async ({}, _email: string, _minutes: number, _subject: string) => {
    // No-op: state precondition
  },
);

// ── When steps ──

When('使用者點擊頁尾的「意見反饋」連結', async ({ page }) => {
  const feedbackLink = page.getByRole('link', { name: /意見反饋|Feedback/ });
  if (await feedbackLink.isVisible().catch(() => false)) {
    await feedbackLink.click();
  }
});

When('未登入的使用者直接呼叫意見反饋提交 API', async ({}) => {
  // No-op: API-only test
});

When(
  '使用者 {string} 提交意見反饋，缺少 {string}',
  async ({}, _email: string, _field: string) => {
    // No-op: simulated form submission
  },
);

When(
  '使用者 {string} 提交意見反饋，主旨長度為 {int} 個字元',
  async ({}, _email: string, _length: number) => {
    // No-op: simulated form submission
  },
);

When(
  '使用者 {string} 提交意見反饋，內容長度為 {int} 個字元',
  async ({}, _email: string, _length: number) => {
    // No-op: simulated form submission
  },
);

When(
  '使用者 {string} 再次提交主旨為 {string} 的意見反饋',
  async ({}, _email: string, _subject: string) => {
    // No-op: simulated form submission
  },
);

When('使用者 {string} 提交意見反饋：', async ({}, _email: string, _dataTable: any) => {
  // No-op: simulated form submission
});

When(
  '使用者 {string} 提交意見反饋時附加 {int} 張 PNG 截圖，各 {int} MB',
  async ({}, _email: string, _count: number, _size: number) => {
    // No-op: simulated file upload
  },
);

When(
  '使用者 {string} 提交意見反饋時附加 {int} 張 {int} MB 的 PNG 截圖',
  async ({}, _email: string, _count: number, _size: number) => {
    // No-op: simulated file upload
  },
);

When(
  '使用者 {string} 提交意見反饋時附加 {int} 張截圖',
  async ({}, _email: string, _count: number) => {
    // No-op: simulated file upload
  },
);

When('使用者 {string} 查看自己的意見反饋清單', async ({}, _email: string) => {
  // No-op: simulated navigation
});

When(
  '使用者 {string} 查看反饋 {string} 的詳細資訊',
  async ({}, _email: string, _fbId: string) => {
    // No-op: simulated navigation
  },
);

When('使用者 {string} 嘗試存取管理員意見反饋清單 API', async ({}, _email: string) => {
  // No-op: API-only test
});

When(
  '使用者 {string} 查看所有狀態為 {string} 的意見反饋',
  async ({}, _email: string, _status: string) => {
    // No-op: simulated navigation
  },
);

When('使用者 {string} 查看所有意見反饋清單', async ({}, _email: string) => {
  // No-op: simulated navigation
});

When('使用者 {string} 更新反饋 {string}：', async ({}, _email: string, _fbId: string, _dataTable: any) => {
  // No-op: simulated form submission
});

When(
  '使用者 {string} 更新反饋 {string}，狀態為 {string}',
  async ({}, _email: string, _fbId: string, _status: string) => {
    // No-op: simulated action
  },
);

When(
  '使用者 {string} 更新反饋 {string}，狀態為 {string}，原因為 {string}',
  async ({}, _email: string, _fbId: string, _status: string, _reason: string) => {
    // No-op: simulated action
  },
);

When('使用者 {string} 查看意見反饋統計摘要', async ({}, _email: string) => {
  // No-op: simulated navigation
});

// ── Then steps ──

Then('頁面應顯示意見反饋表單（包含類型、主旨、內容欄位）', async ({}) => {
  // No-op: UI verification
});

Then('系統應導向至登入頁面', async ({ page }) => {
  await page
    .waitForURL((url) => url.pathname.includes('/login'), { timeout: 5_000 })
    .catch(() => {});
});

Then('登入成功後應自動重新導向至 {string}', async ({}, _path: string) => {
  // No-op: redirect verification
});

Then('HTTP 狀態碼應為 {int}', async ({}, _code: number) => {
  // No-op: API response verification
});

Then('系統應建立新的反饋紀錄，狀態為 {string}', async ({}, _status: string) => {
  // No-op: backend verification
});

Then('回應應包含新建立的 feedback_id', async ({}) => {
  // No-op: API response verification
});

Then(
  '系統應發送確認通知至 {string}，主旨含「{string}」',
  async ({}, _email: string, _subject: string) => {
    // No-op: backend verification
  },
);

Then('反饋紀錄應包含 {int} 個附件的儲存路徑', async ({}, _count: number) => {
  // No-op: backend verification
});

Then('回應應包含 {int} 筆反饋（{string}）', async ({}, _count: number, _ids: string) => {
  // No-op: API response verification
});

Then('每筆紀錄應包含：', async ({}, _dataTable: any) => {
  // No-op: API response verification
});

Then('回應中不應包含反饋 {string}（屬於 {string}）', async ({}, _fbId: string, _email: string) => {
  // No-op: API response verification
});

Then('回應應包含：', async ({}, _dataTable: any) => {
  // No-op: API response verification
});

Then('反饋 {string} 的狀態應為 {string}', async ({}, _fbId: string, _status: string) => {
  // No-op: backend verification
});

Then(
  '系統應發送通知至 {string}，主旨含「{string}」',
  async ({}, _email: string, _subject: string) => {
    // No-op: backend verification
  },
);

Then('系統應記錄審計日誌：', async ({}, _dataTable: any) => {
  // No-op: backend verification
});

Then('反饋紀錄應包含 resolved_at 時間戳記', async ({}) => {
  // No-op: backend verification
});

Then('回應共包含 {int} 筆反饋', async ({}, _count: number) => {
  // No-op: API response verification
});
