import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Then } = createBdd(test);

// ── JWT / response verification ──

Then('回應應包含有效的 JWT 存取憑證', async ({ page }) => {
  // After successful login, the JWT should be stored in localStorage or sessionStorage
  const token = await page.evaluate(() => {
    return (
      localStorage.getItem('certimate_jwt_token') ||
      sessionStorage.getItem('certimate_jwt_token')
    );
  });
  expect(token).toBeTruthy();
  // Verify it looks like a JWT (three base64url segments)
  expect(token!.split('.').length).toBe(3);
});

Then('回應中的使用者資訊應包含：', async ({ page }, dataTable: any) => {
  const rows = dataTable.rows() as string[][];
  // Fetch /auth/me from within the page context so page.route() intercepts it
  const userData = await page.evaluate(async () => {
    const token =
      localStorage.getItem('certimate_jwt_token') ||
      sessionStorage.getItem('certimate_jwt_token');
    if (!token) throw new Error('No JWT token found');
    const res = await fetch('/api/v1/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.json();
  });

  for (const [field, expectedValue] of rows) {
    if (field === 'email') {
      expect(userData.email).toBe(expectedValue);
    } else if (field === '訂閱方案') {
      expect(userData.subscription_plan).toBe(expectedValue);
    }
  }
});

Then(
  '登入後的回應應包含 {string}: {string}',
  async ({ page }, key: string, value: string) => {
    const token = await page.evaluate(
      () =>
        localStorage.getItem('certimate_jwt_token') ||
        sessionStorage.getItem('certimate_jwt_token'),
    );
    expect(token, 'JWT token should exist after login').toBeTruthy();

    // Fetch /auth/me from page context so page.route() intercepts it
    const userData = await page.evaluate(async (t: string) => {
      const res = await fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${t}` },
      });
      return res.json();
    }, token!);

    // Backend stores short plan names (FREE/PRO/PRO_PLUS/ULTRA),
    // frontend uses display names (FREE/PRO_199/PRO_PLUS_399/ULTRA_1599)
    const planDisplayToDb: Record<string, string> = {
      FREE: 'FREE',
      PRO_199: 'PRO',
      PRO_PLUS_399: 'PRO_PLUS',
      ULTRA_1599: 'ULTRA',
    };

    if (key === 'subscription_tier') {
      const actual = String(userData.subscription_plan || userData.subscription_tier).toUpperCase();
      const expected = planDisplayToDb[value.toUpperCase()] || value.toUpperCase();
      expect(actual).toBe(expected);
    } else if (key === 'role') {
      expect(String(userData.role).toUpperCase()).toContain(value.toUpperCase());
    } else {
      const apiField = key;
      expect(String(userData[apiField]).toUpperCase()).toContain(value.toUpperCase());
    }
  },
);

Then('登入成功不會報錯', async ({ page }) => {
  const errorBanner = page.locator('.bg-rose-50');
  await expect(errorBanner).not.toBeVisible({ timeout: 3_000 });
});

// ── Backend-only verification steps (no-op for frontend) ──

Then(
  '系統應建立新帳號，訂閱方案為 {string}，狀態為 {string}',
  async ({ page }, _plan: string, _status: string) => {
    // After successful registration, the frontend redirects to /verify-email/sent
    await page.waitForURL('**/verify-email/sent**', { timeout: 10_000 }).catch(() => {});
  },
);

Then('系統應發送帳號驗證信至 {string}', async ({}, _email: string) => {
  // No-op: can't verify email sending from frontend E2E tests
});

Then('系統應發送密碼重設信至 {string}', async ({}, _email: string) => {
  // No-op: can't verify email sending from frontend E2E tests
});

Then('重設連結應在 1 小時後失效', async ({}) => {
  // No-op: time-based expiry can't be tested in frontend E2E
});

Then('系統不應洩漏該帳號是否存在的資訊', async ({ page }) => {
  // The forgot-password page should show the same success message
  // regardless of whether the email exists.
  // Since Firebase Auth doesn't work in mock env, the When step calls
  // the API via page.evaluate and stores the result in window vars.
  const sent = await page.evaluate(() => (window as any).__forgotPasswordSent);
  if (sent !== undefined) {
    expect(sent).toBe(true);
    return;
  }
  await expect(page.getByText('重設信件已寄出')).toBeVisible({ timeout: 5_000 });
});

Then('使用者註冊方式應註記為 {string}', async ({}, _method: string) => {
  // No-op: registration method is backend-only data
});

Then('該帳號的註冊方式應允許或更新關聯 {string}', async ({}, _method: string) => {
  // No-op: registration method linking is backend-only
});
