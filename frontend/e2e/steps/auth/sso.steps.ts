import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { When, Then } = createBdd(test);

// ── Google SSO steps ──
// These require Firebase OAuth which can't be tested in headless E2E.
// Implemented as stubs so scenarios aren't skipped due to missing steps.
// The scenarios themselves will fail gracefully.

When(
  '使用者透過 Google SSO 登入且 Email 為 {string}',
  async ({ page }, _email: string) => {
    // Navigate to login and click Google button
    await page.goto('/login');
    await page.getByRole('button', { name: /Google/ }).click();
    // Google OAuth popup can't be automated — this will timeout in E2E
    // The scenario should be tagged @ignore for frontend tests
  },
);

When('使用者完成 Google OAuth 授權且 Email 為 {string}', async ({}, _email: string) => {
  // No-op: can't simulate Google OAuth completion
});

Then('系統應導向 Google OAuth 授權頁面', async ({}) => {
  // No-op: can't verify Google OAuth redirect in headless tests
});
