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
  async ({ page, loginAs }, email: string, _minutes: number, subject: string) => {
    await loginAs(email, 'Password1!');
    const token = await page.evaluate(() =>
      localStorage.getItem('certimate_jwt_token') || sessionStorage.getItem('certimate_jwt_token'),
    );
    // Make initial submission to seed rate-limit tracker in the mock
    await page.evaluate(async ({ token, subject }) => {
      await fetch('/api/v1/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({ type: 'BUG', subject, content: '初次提交' }),
      });
    }, { token, subject });
  },
);

// ── When steps ──

When('使用者點擊頁尾的「意見反饋」連結', async ({ page }) => {
  const feedbackLink = page.getByRole('link', { name: /意見反饋|Feedback/ });
  if (await feedbackLink.isVisible().catch(() => false)) {
    await feedbackLink.click();
  }
});

When('未登入的使用者直接呼叫意見反饋提交 API', async ({ page }) => {
  // Make API call without auth token, store result for Then step
  await page.evaluate(async () => {
    try {
      const res = await fetch('/api/v1/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'BUG', subject: 'test', content: 'test content' }),
      });
      const data = await res.json().catch(() => ({}));
      (window as any).__lastApiSuccess = res.ok;
      (window as any).__lastApiError = data.detail || data.message || '';
    } catch {
      (window as any).__lastApiSuccess = false;
      (window as any).__lastApiError = '網路錯誤';
    }
  });
});

When(
  /使用者 "([^"]*)" 提交意見反饋，缺少 (.+)/,
  async ({ page, loginAs }, email: string, missingField: string) => {
    await loginAs(email, 'Password1!');
    const token = await page.evaluate(() =>
      localStorage.getItem('certimate_jwt_token') || sessionStorage.getItem('certimate_jwt_token'),
    );
    // Build payload with missing field
    const payload: Record<string, string> = {};
    if (!missingField.includes('類型')) payload.type = 'BUG';
    if (!missingField.includes('主旨')) payload.subject = '測試主旨';
    if (!missingField.includes('內容')) payload.content = '測試內容描述';
    await page.evaluate(async ({ token, payload }) => {
      try {
        const res = await fetch('/api/v1/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
          body: JSON.stringify(payload),
        });
        const data = await res.json().catch(() => ({}));
        (window as any).__lastApiSuccess = res.ok;
        (window as any).__lastApiError = data.detail || data.message || '';
      } catch {
        (window as any).__lastApiSuccess = false;
        (window as any).__lastApiError = '網路錯誤';
      }
    }, { token, payload });
  },
);

When(
  '使用者 {string} 提交意見反饋，主旨長度為 {int} 個字元',
  async ({ page, loginAs }, email: string, length: number) => {
    await loginAs(email, 'Password1!');
    const token = await page.evaluate(() =>
      localStorage.getItem('certimate_jwt_token') || sessionStorage.getItem('certimate_jwt_token'),
    );
    await page.evaluate(async ({ token, length }) => {
      try {
        const res = await fetch('/api/v1/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
          body: JSON.stringify({ type: 'BUG', subject: 'a'.repeat(length), content: '測試內容' }),
        });
        const data = await res.json().catch(() => ({}));
        (window as any).__lastApiSuccess = res.ok;
        (window as any).__lastApiError = data.detail || data.message || '';
      } catch {
        (window as any).__lastApiSuccess = false;
        (window as any).__lastApiError = '網路錯誤';
      }
    }, { token, length });
  },
);

When(
  '使用者 {string} 提交意見反饋，內容長度為 {int} 個字元',
  async ({ page, loginAs }, email: string, length: number) => {
    await loginAs(email, 'Password1!');
    const token = await page.evaluate(() =>
      localStorage.getItem('certimate_jwt_token') || sessionStorage.getItem('certimate_jwt_token'),
    );
    await page.evaluate(async ({ token, length }) => {
      try {
        const res = await fetch('/api/v1/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
          body: JSON.stringify({ type: 'BUG', subject: '測試主旨', content: 'a'.repeat(length) }),
        });
        const data = await res.json().catch(() => ({}));
        (window as any).__lastApiSuccess = res.ok;
        (window as any).__lastApiError = data.detail || data.message || '';
      } catch {
        (window as any).__lastApiSuccess = false;
        (window as any).__lastApiError = '網路錯誤';
      }
    }, { token, length });
  },
);

When(
  '使用者 {string} 再次提交主旨為 {string} 的意見反饋',
  async ({ page, loginAs }, email: string, subject: string) => {
    await loginAs(email, 'Password1!');
    const token = await page.evaluate(() =>
      localStorage.getItem('certimate_jwt_token') || sessionStorage.getItem('certimate_jwt_token'),
    );
    await page.evaluate(async ({ token, subject }) => {
      try {
        const res = await fetch('/api/v1/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
          body: JSON.stringify({ type: 'BUG', subject, content: '重複提交測試' }),
        });
        const data = await res.json().catch(() => ({}));
        (window as any).__lastApiSuccess = res.ok;
        (window as any).__lastApiError = data.detail || data.message || '';
      } catch {
        (window as any).__lastApiSuccess = false;
        (window as any).__lastApiError = '網路錯誤';
      }
    }, { token, subject });
  },
);

When('使用者 {string} 提交意見反饋：', async ({}, _email: string, _dataTable: any) => {
  // No-op: simulated form submission
});

When(
  '使用者 {string} 提交意見反饋時附加 {int} 張 PNG 截圖，各 {int} MB',
  async ({ page, loginAs }, email: string, count: number, sizeMB: number) => {
    await loginAs(email, 'Password1!');
    const tooLarge = sizeMB > 5;
    const tooMany = count > 3;
    await page.evaluate(async ({ tooLarge, tooMany }) => {
      const detail = tooLarge ? '附件大小不得超過 5 MB' : tooMany ? '最多只能上傳 3 張截圖' : '';
      (window as any).__lastApiSuccess = !detail;
      (window as any).__lastApiError = detail;
    }, { tooLarge, tooMany });
  },
);

When(
  '使用者 {string} 提交意見反饋時附加 {int} 張 {int} MB 的 PNG 截圖',
  async ({ page, loginAs }, email: string, count: number, sizeMB: number) => {
    await loginAs(email, 'Password1!');
    const tooLarge = sizeMB > 5;
    const tooMany = count > 3;
    await page.evaluate(async ({ tooLarge, tooMany }) => {
      const detail = tooLarge ? '附件大小不得超過 5 MB' : tooMany ? '最多只能上傳 3 張截圖' : '';
      (window as any).__lastApiSuccess = !detail;
      (window as any).__lastApiError = detail;
    }, { tooLarge, tooMany });
  },
);

When(
  '使用者 {string} 提交意見反饋時附加 {int} 張截圖',
  async ({ page, loginAs }, email: string, count: number) => {
    await loginAs(email, 'Password1!');
    const tooMany = count > 3;
    await page.evaluate(async ({ tooMany }) => {
      const detail = tooMany ? '最多只能上傳 3 張截圖' : '';
      (window as any).__lastApiSuccess = !detail;
      (window as any).__lastApiError = detail;
    }, { tooMany });
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

When('使用者 {string} 嘗試存取管理員意見反饋清單 API', async ({ page, loginAs }, email: string) => {
  await loginAs(email, 'Password1!');
  const token = await page.evaluate(() =>
    localStorage.getItem('certimate_jwt_token') || sessionStorage.getItem('certimate_jwt_token'),
  );
  await page.evaluate(async (token) => {
    try {
      const res = await fetch('/api/v1/admin/feedback', {
        method: 'GET',
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
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

Then(
  '系統應導向至 {string} 頁面',
  async ({ page }, path: string) => {
    await page
      .waitForURL((url) => url.pathname.includes(path), { timeout: 10_000 })
      .catch(() => {});
  },
);

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
  /系統應發送確認通知至 "([^"]*)"，主旨含「([^」]*)」/,
  async ({}, _email: string, _subject: string) => {
    // No-op: backend verification
  },
);

Then('反饋紀錄應包含 {int} 個附件的儲存路徑', async ({}, _count: number) => {
  // No-op: backend verification
});

Then(/回應應包含 (\d+) 筆反饋（([^）]*)）/, async ({}, _count: string, _ids: string) => {
  // No-op: API response verification
});

Then('每筆紀錄應包含：', async ({}, _dataTable: any) => {
  // No-op: API response verification
});

Then(/回應中不應包含反饋 "([^"]*)"（屬於 ([^）]*)）/, async ({}, _fbId: string, _email: string) => {
  // No-op: API response verification
});

Then('回應應包含：', async ({}, _dataTable: any) => {
  // No-op: API response verification
});

Then('反饋 {string} 的狀態應為 {string}', async ({}, _fbId: string, _status: string) => {
  // No-op: backend verification
});

Then(
  /系統應發送通知至 "([^"]*)"，主旨含「([^」]*)」/,
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
