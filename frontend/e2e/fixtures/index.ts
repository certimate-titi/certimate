import { test as base } from 'playwright-bdd';
import { installApiMock } from '../mocks/api-mock';
import { clearOverrides } from '../mocks/data';

export const test = base.extend<{
  /** Auto-installs API mock for all tests */
  apiMock: void;
  /** Login as a specific user via the UI login form */
  loginAs: (email: string, password: string) => Promise<void>;
}>({
  // Auto-fixture: install mock API routes before every test
  apiMock: [
    async ({ page }, use) => {
      clearOverrides();
      await installApiMock(page);
      await use();
    },
    { auto: true },
  ],

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
        // Login timed out — let subsequent step assertions determine pass/fail.
      });
    };
    await use(fn);
  },
});
