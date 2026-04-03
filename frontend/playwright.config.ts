import { defineConfig, devices } from '@playwright/test';
import { defineBddConfig } from 'playwright-bdd';

const testDir = defineBddConfig({
  // 前後端共用同一份 .feature 檔（Single Source of Truth）
  // 路徑相對於 playwright.config.ts 所在目錄 (frontend/)
  features: '../project/features/*.feature',
  featuresRoot: '..',
  steps: 'e2e/steps/**/*.ts',
  importTestFrom: 'e2e/fixtures/index.ts',
  disableWarnings: { importTestFrom: true },
  // 跳過缺少 step definitions 的場景（允許漸進式新增）
  missingSteps: 'skip-scenario',
  // 排除後端專用標籤（@ignore 為後端尚未實作、@command 為純 API 測試）
  tags: 'not @ignore and not @command and not @manual',
});

export default defineConfig({
  globalSetup: './e2e/global-setup.ts',
  testDir,
  timeout: 30_000,
  retries: 0,
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: 'http://localhost:3333',
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
    headless: true,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npx next dev --port 3333',
    port: 3333,
    reuseExistingServer: true,
    timeout: 90_000,
  },
});
