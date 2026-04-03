import { test as base } from 'playwright-bdd';

export const test = base.extend<{
  /** Login as a specific user via the UI login form */
  loginAs: (email: string, password: string) => Promise<void>;
}>({
  loginAs: async ({ page }, use) => {
    const fn = async (email: string, password: string) => {
      await page.goto('/login');
      await page.getByPlaceholder('電子郵件').fill(email);
      await page.getByPlaceholder('密碼').fill(password);
      await page.getByRole('button', { name: '登入', exact: true }).click();
      // Wait for either successful navigation or error message
      await Promise.race([
        page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10_000 }),
        page.locator('.bg-rose-50').waitFor({ state: 'visible', timeout: 10_000 }),
      ]).catch(() => {
        // Login timed out — backend may not have this user seeded.
        // Don't throw: let subsequent step assertions determine pass/fail.
      });
    };
    await use(fn);
  },
});
