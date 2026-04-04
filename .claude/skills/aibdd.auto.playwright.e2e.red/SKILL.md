---
name: aibdd.auto.playwright.e2e.red
description: Playwright E2E Phase 2：紅燈生成器。根據 Step Analysis 規劃，建立完整的 step definitions（Playwright 操作邏輯），測試因 UI 元素不存在而失敗。可被 control-flow 調用，也可獨立使用。
user-invocable: true
argument-hint: "[feature-file]"
input: project/features/*.feature, frontend/e2e/steps/**/*.ts, Step Analysis 報告
output: 新增的 step definition 檔案，測試紅燈（UI 元素不存在）
---

# 角色

紅燈生成器。建立完整可執行的 Playwright step definitions，讓測試因為「前端 UI 尚未實作」而失敗——這就是紅燈。

---

# 入口

## 被 control-flow 調用時

接收參數 `FEATURE_FILE`，直接進入紅燈生成流程。

## 獨立使用時

詢問目標 feature 檔案：

```
請指定要處理的 Feature 檔案路徑：
（例如：project/features/01-身分驗證.feature）
```

---

# 核心任務

將 Step Analysis 報告中標記為「❌ 缺少」的 steps，轉化為完整的 Playwright step definitions。

---

# 技術規範

## 1. 檔案結構

```typescript
// frontend/e2e/steps/{domain}/{name}.steps.ts

import { expect } from '@playwright/test';
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);
```

**重要**：
- 必須 import `test` from `'../../fixtures'`（不是 from `'playwright-bdd'`）
- 必須使用 `createBdd(test)` 而不是 `createBdd()`
- `expect` 從 `@playwright/test` import

## 2. Step Pattern 規則

使用 Cucumber Expressions（不是 RegExp）：

```typescript
// ✅ 正確：Cucumber Expression
Given('使用者已登入為 {string}', async ({ loginAs }, email: string) => { ... });
When('使用者點擊「{string}」按鈕', async ({ page }, text: string) => { ... });
Then('頁面應顯示 {int} 筆資料', async ({ page }, count: number) => { ... });

// ❌ 錯誤：RegExp
Given(/^使用者已登入為 "(.+)"$/, async ({ loginAs }, email: string) => { ... });
```

## 3. Playwright Locator 策略（優先順序）

1. **Role-based**（最佳）：`page.getByRole('button', { name: '登入' })`
2. **Placeholder**：`page.getByPlaceholder('電子郵件')`
3. **Text**：`page.getByText('歡迎回來')`
4. **Label**：`page.getByLabel('密碼')`
5. **Test ID**：`page.getByTestId('submit-btn')`（需要 data-testid）
6. **CSS Selector**（最後手段）：`page.locator('.error-message')`

## 4. 後端專用步驟的處理

Feature 中的後端專用步驟（DB 操作、系統排程等），前端不需要實作。
這些場景會因為 `missingSteps: 'skip-scenario'` 被自動跳過。

**但若 Background 中有後端步驟**，而同一 Feature 有前端場景，則需要：
- 在 `common/background.steps.ts` 中實作一個 pass-through 版本
- 或使用 API 呼叫來設定測試資料

```typescript
// 方案 A：透過 API 設定測試資料
Given('系統中有以下使用者帳號：', async ({ request }, table: DataTable) => {
  // 呼叫後端 admin API 建立測試帳號
  for (const row of table.hashes()) {
    await request.post('http://localhost:8000/api/v1/admin/seed-user', {
      data: { email: row['Email'], plan: row['訂閱方案'] }
    });
  }
});

// 方案 B：No-op（如果 global-setup.ts 已經處理）
Given('系統中有以下使用者帳號：', async ({}, table: DataTable) => {
  // 測試帳號已在 global-setup.ts 中建立，此處為 no-op
});
```

## 5. 等待策略

```typescript
// 頁面導航等待
await page.goto('/dashboard');
await page.waitForURL('**/dashboard');

// 元素可見等待
await expect(page.getByRole('heading', { name: '儀表板' })).toBeVisible();

// 網路請求等待（API 回應）
await page.waitForResponse(resp =>
  resp.url().includes('/api/v1/exams') && resp.status() === 200
);

// 多重條件等待（登入後可能成功或失敗）
await Promise.race([
  page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10_000 }),
  page.locator('.bg-rose-50').waitFor({ state: 'visible', timeout: 10_000 }),
]);
```

---

# 執行步驟

## Step 1：讀取 Feature File 和 Step Analysis

1. 讀取 feature file，提取所有需要的步驟
2. 掃描現有 step definitions，確認哪些已存在
3. 確認缺少的步驟清單

## Step 2：建立 Step Definition 檔案

根據規劃，建立新的 `.steps.ts` 檔案。每個 step 必須：

1. 完整實作 Playwright 操作邏輯
2. 使用正確的 Locator 策略
3. 包含適當的等待策略
4. 不能有空白 `async () => {}` 或 `// TODO`

```typescript
// ✅ 正確：完整的 Playwright 操作邏輯
When('使用者填寫登入表單', async ({ page }) => {
  await page.getByPlaceholder('電子郵件').fill('alice@example.com');
  await page.getByPlaceholder('密碼').fill('Password1!');
  await page.getByRole('button', { name: '登入' }).click();
});

// ❌ 錯誤：空白實作
When('使用者填寫登入表單', async ({ page }) => {
  // TODO: implement
});
```

## Step 3：處理 DataTable

Feature 中的 DataTable 步驟需要正確處理：

```typescript
Given('系統中有以下備考科目：', async ({}, table: DataTable) => {
  // DataTable 處理
  const rows = table.hashes();
  for (const row of rows) {
    console.log(row['科目 ID'], row['名稱']);
  }
});
```

## Step 4：執行 bddgen + 測試

```bash
cd frontend && npx bddgen && npx playwright test --grep "{feature 關鍵字}"
```

確認：
1. `bddgen` 成功產出測試檔案（無 step 未定義錯誤）
2. 測試執行但失敗（紅燈）
3. 失敗原因是「UI 元素不存在」而非「step 未定義」

---

# 紅燈的合格條件

測試失敗原因必須是以下之一（不是 step 未定義）：

| 失敗原因 | 說明 |
|---------|------|
| `Locator.click: Error: getByRole('button', { name: '開始考試' }) - no matching element` | 按鈕不存在 |
| `expect(locator).toBeVisible() - locator resolved to 0 elements` | 元素不可見 |
| `page.goto: net::ERR_CONNECTION_REFUSED` | 後端未運行 |
| `Timeout exceeded while waiting for URL` | 頁面導航失敗 |
| `expect(received).toContain(expected)` | 內容不符 |

**不合格的失敗**：
- `Missing step definition` — 表示 step 沒寫
- `TypeError: ... is not a function` — 表示程式碼有語法錯誤
- `Import error` — 表示 import 路徑有誤

---

# 重要規則

## R1: Step Definition 程式碼必須完整
不能有 `// TODO`、空白函式、`pass`。每個 step 都要有完整的 Playwright 操作。

## R2: 使用 Fixtures
從 `e2e/fixtures/index.ts` import `test`，使用 `loginAs` 等自訂 fixture。

## R3: 不修改前端頁面
紅燈階段不改 `app/`、`components/`、`lib/` 下的任何檔案。只新增/修改 `e2e/steps/` 下的檔案。

## R4: 中文 Step Pattern
Step pattern 使用繁體中文，與 Feature File 一致。

## R5: 一個檔案可包含多個 Steps
不需要一檔一 step。相關的 steps 可以放同一檔案。

## R6: 避免 Step 重複定義
新增 step 前，確認不會與現有 step 衝突（同樣的 pattern 不能定義兩次）。

---

# 完成條件

- [ ] 所有缺少的 step definitions 已建立
- [ ] Step patterns 使用 Cucumber Expressions
- [ ] 所有 steps 有完整的 Playwright 操作邏輯
- [ ] `npx bddgen` 成功（無 step 未定義警告）
- [ ] 測試執行後達到紅燈狀態（UI 元素不存在，不是 step 未定義）
- [ ] 未修改任何前端頁面程式碼（app/、components/、lib/）
