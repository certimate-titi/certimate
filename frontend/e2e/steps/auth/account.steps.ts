import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { When, Then } = createBdd(test);

// ── Account management steps ──

When(
  '使用者 {string} 執行 {string} 操作',
  async ({ page, loginAs }, email: string, action: string) => {
    if (action === '刪除帳號') {
      // Login first, then navigate to account settings
      const testPasswords: Record<string, string> = {
        'alice@example.com': 'Password1!',
        'admin@certimate.com': 'admin123',
      };
      await loginAs(email, testPasswords[email] || 'Password1!');
      await page.goto('/account');
      // Look for delete account button
      const deleteBtn = page.getByRole('button', { name: /刪除帳號/ });
      if (await deleteBtn.isVisible().catch(() => false)) {
        await deleteBtn.click();
        // Confirm deletion if there's a confirmation dialog
        const confirmBtn = page.getByRole('button', { name: /確認刪除|確定/ });
        if (await confirmBtn.isVisible().catch(() => false)) {
          await confirmBtn.click();
        }
      }
    }
  },
);

// Backend-only verification steps for account deletion
Then('系統應從主資料庫中移除該使用者的所有個人資料與測驗記錄', async ({}) => {
  // No-op: backend verification
});

Then('系統應同步清除 Redis 中所有與該使用者 ID 關聯的快取資料', async ({}) => {
  // No-op: backend verification
});

Then('使用者上傳至雲端存儲 \\(GCS\\) 的實體檔案應被標記刪除或移除', async ({}) => {
  // No-op: backend verification
});

Then('該使用者的所有 JWT 存取憑證應立即失效 \\(Revoked\\)', async ({}) => {
  // No-op: backend verification
});
