import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

// ── Login page navigation ──

Given('使用者在登入頁面', async ({ page }) => {
  await page.goto('/login');
});

// ── Login actions ──

When(
  '使用者以 Email {string} 和密碼 {string} 進行登入',
  async ({ page }, email: string, password: string) => {
    await page.goto('/login');
    await page.getByPlaceholder('電子郵件').fill(email);
    await page.getByPlaceholder('密碼').fill(password);
    await page.getByRole('button', { name: '登入', exact: true }).click();
    // Wait for either navigation away or error message to appear
    await Promise.race([
      page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 8_000 }).catch(() => {}),
      page.locator('.bg-rose-50').waitFor({ state: 'visible', timeout: 8_000 }).catch(() => {}),
    ]);
  },
);

When(
  '使用者 {string} 成功登入系統',
  async ({ page, loginAs }, email: string) => {
    // Map test user emails to their passwords (matching feature Background data)
    const testPasswords: Record<string, string> = {
      'alice@example.com': 'Password1!',
      'bob@example.com': 'Password1!',
      'carol@example.com': 'Password1!',
      'admin@example.com': 'Password1!',
      'newbie@example.com': 'Password1!',
      'admin@certimate.com': 'admin123',
    };
    const password = testPasswords[email] || 'Password1!';
    await loginAs(email, password);
    // If still on login page after loginAs, the client-side router.push may not have worked.
    // Call login API again to get redirect_to and navigate explicitly.
    if (page.url().includes('/login')) {
      const redirectTo = await page.evaluate(async ({ email, password }) => {
        try {
          const res = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
          });
          const data = await res.json().catch(() => ({}));
          return data.redirect_to || '/dashboard';
        } catch {
          return '/dashboard';
        }
      }, { email, password });
      await page.goto(redirectTo);
      await page.waitForTimeout(500);
    }
  },
);

// ── Password visibility toggle ──

Given(
  '使用者在登入頁面的密碼欄位輸入 {string}',
  async ({ page }, password: string) => {
    await page.goto('/login');
    await page.getByPlaceholder('密碼').fill(password);
  },
);

When('使用者點擊密碼欄位的顯示\\/隱藏切換按鈕', async ({ page }) => {
  // The toggle button is inside the password field's parent div
  const toggleBtn = page.locator('#password').locator('..').getByRole('button');
  await toggleBtn.click();
});

Then('密碼欄位應從遮蔽模式切換為明文顯示模式', async ({ page }) => {
  await expect(page.locator('#password')).toHaveAttribute('type', 'text');
});

Then('密碼欄位應從明文顯示模式切換為遮蔽模式', async ({ page }) => {
  await expect(page.locator('#password')).toHaveAttribute('type', 'password');
});

// ── Remember me ──

When('使用者在登入頁面勾選「記住我」', async ({ page }) => {
  await page.goto('/login');
  await page.locator('#remember-me').check();
});

// ── Forgot password link ──

Then('頁面應有忘記密碼連結', async ({ page }) => {
  await expect(page.getByText('忘記密碼？')).toBeVisible();
});

// ── Login page elements ──

Then('頁面應顯示登入表單', async ({ page }) => {
  await expect(page.getByPlaceholder('電子郵件')).toBeVisible();
  await expect(page.getByPlaceholder('密碼')).toBeVisible();
  await expect(page.getByRole('button', { name: '登入', exact: true })).toBeVisible();
});

Then('頁面應有 Google 登入按鈕', async ({ page }) => {
  await expect(page.getByRole('button', { name: /Google/ })).toBeVisible();
});

Then('頁面應有註冊連結', async ({ page }) => {
  await expect(page.getByRole('main').getByRole('link', { name: '免費註冊' })).toBeVisible();
});

// ── Navbar visibility ──

Then(
  '前端導覽列應顯示「{word}」連結，路徑為 {string}',
  async ({ page }, label: string, path: string) => {
    const navLink = page.getByRole('link', { name: label });
    await expect(navLink).toBeVisible();
    // Match with or without trailing slash
    const href = await navLink.getAttribute('href');
    const normalize = (p: string) => p.replace(/\/+$/, '');
    expect(normalize(href || '')).toBe(normalize(path));
  },
);

Then(
  '前端導覽列不應顯示「{word}」連結',
  async ({ page }, label: string) => {
    const navLink = page.getByRole('link', { name: label });
    await expect(navLink).not.toBeVisible();
  },
);
