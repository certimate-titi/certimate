---
name: aibdd.auto.playwright.e2e.green
description: Playwright E2E Phase 3：綠燈階段。Trial-and-error 循環讓測試通過，實作 Next.js 頁面、React 元件、API 服務層串接。可被 control-flow 調用，也可獨立使用。
user-invocable: true
argument-hint: "[feature-file]"
input: project/features/*.feature, frontend/e2e/steps/**/*.ts, frontend/app/**/*.tsx
output: Next.js 頁面、React 元件、API 服務層更新，測試全部通過
---

# 角色

綠燈實作者。在 TDD 紅燈階段已經寫好 Playwright step definitions 並確認失敗（UI 元素不存在）。現在進入綠燈階段：寫最少的前端程式碼讓測試通過，不斷 trial-and-error 直到所有測試變綠。

---

# 入口

## 被 control-flow 調用時

接收參數 `FEATURE_FILE`，直接進入 trial-and-error 循環。

## 獨立使用時

詢問目標 feature 檔案：

```
請指定要處理的 Feature 檔案路徑：
（例如：project/features/01-身分驗證.feature）
```

---

# 核心原則

## 0. 測試驅動開發的鐵律

**必須透過執行自動化測試來驗證實作是否完成，絕不猜測。**

- 每完成一個步驟，立即執行測試
- 無需詢問使用者，直接下達測試指令
- 根據測試結果決定下一步行動
- 絕不假設測試會通過
- 絕不詢問「測試通過了嗎？」

**測試執行策略**：

1. **開發階段：先跑目標 feature 的特定測試**
   ```bash
   cd frontend && npx bddgen && npx playwright test --grep "{feature 關鍵字}"
   ```
   - 快速驗證當前實作
   - 縮短反饋循環

2. **完成前：跑全部測試**
   ```bash
   cd frontend && npx bddgen && npx playwright test
   ```
   - 確認無回歸
   - 最終驗收

## 1. YAGNI — 只實作測試要求的

不加額外功能、不做 UI 美化、不做效能優化。測試要什麼就做什麼。

## 2. 最小實作原則

每次修改只解決一個失敗的測試。修改 → 執行 → 看結果 → 再修改。

---

# Trial-and-Error 循環

```
┌─────────────────────────────────────────┐
│  1. 執行測試                              │
│     cd frontend && npx bddgen &&         │
│     npx playwright test --grep "..."     │
│                                          │
│  2. 看失敗訊息                            │
│     - 哪個 step 失敗？                    │
│     - 失敗原因是什麼？                    │
│     - 需要什麼 UI 元素？                  │
│                                          │
│  3. 實作最小修改                          │
│     - 新增/修改頁面                       │
│     - 新增/修改元件                       │
│     - 更新 API 服務層                     │
│                                          │
│  4. 回到步驟 1                            │
└─────────────────────────────────────────┘

直到所有測試通過（綠燈）
```

---

# 實作範疇

## 可以修改的檔案

| 目錄 | 說明 | 範例 |
|------|------|------|
| `app/` | Next.js 頁面 | `app/dashboard/page.tsx` |
| `components/` | React 元件 | `components/ExamTimer.tsx` |
| `lib/api/services.ts` | API 服務層 | 新增/修改 API 呼叫 |
| `lib/api/client.ts` | HTTP 客戶端 | 少見需修改 |
| `types/` | 型別定義 | `types/models.ts` |
| `e2e/steps/` | Step definitions | 修正 locator、等待策略 |
| `e2e/fixtures/` | 測試 fixtures | 新增自訂 fixture |

## 不可以修改的檔案

| 檔案 | 原因 |
|------|------|
| `project/features/*.feature` | SSOT — 不可修改 |
| `playwright.config.ts` | 全域設定 — 極少需修改 |
| `e2e/global-setup.ts` | 全域初始化 — 除非需要新增測試帳號 |

---

# 前端實作模式

## 1. 頁面實作

```typescript
// app/some-page/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { someService } from '@/lib/api/services';

export default function SomePage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    someService.getData().then(setData);
  }, []);

  return (
    <div>
      <h1>頁面標題</h1>
      {/* 測試需要的 UI 元素 */}
    </div>
  );
}
```

## 2. API 服務層串接

`lib/api/services.ts` 是所有 API 呼叫的唯一真實來源：

```typescript
// 目前可能是 mock 資料
export const examService = {
  async getResults(examId: string) {
    // 替換 mock → 真實 API 呼叫
    const response = await apiClient.get(`/exams/${examId}/results`);
    return response.data;
  },
};
```

## 3. 元件實作

```typescript
// components/SomeComponent.tsx
'use client';

interface Props {
  title: string;
  onAction: () => void;
}

export function SomeComponent({ title, onAction }: Props) {
  return (
    <div>
      <h2>{title}</h2>
      <button onClick={onAction}>執行</button>
    </div>
  );
}
```

## 4. 修正 Step Definitions

如果紅燈階段的 locator 不準確（UI 結構與預期不同），可以在綠燈階段調整：

```typescript
// 紅燈階段的猜測
Then('頁面應顯示考試結果', async ({ page }) => {
  await expect(page.getByRole('heading', { name: '考試結果' })).toBeVisible();
});

// 綠燈階段根據實際 UI 調整
Then('頁面應顯示考試結果', async ({ page }) => {
  await expect(page.getByText('考試結果')).toBeVisible();
});
```

---

# 常見問題處理

## 1. 後端 API 未實作

如果後端 API 尚未準備好，前端服務層可以暫時返回 mock 資料：

```typescript
async getExamResults(examId: string) {
  try {
    const response = await apiClient.get(`/exams/${examId}/results`);
    return response.data;
  } catch {
    // Fallback: mock data for E2E test
    return { score: 85, total: 100, passed: true };
  }
}
```

## 2. 認證狀態

大多數頁面需要登入狀態。Step definition 中使用 `loginAs` fixture：

```typescript
Given('使用者已登入為 {string}', async ({ loginAs }, email: string) => {
  await loginAs(email, 'Password1!');
});
```

## 3. 頁面導航

```typescript
When('使用者進入考試設定頁面', async ({ page }) => {
  await page.goto('/exam/setup');
  await page.waitForURL('**/exam/setup');
});
```

## 4. 表單互動

```typescript
When('使用者填寫以下資料：', async ({ page }, table: DataTable) => {
  for (const row of table.hashes()) {
    const field = row['欄位'];
    const value = row['值'];
    await page.getByLabel(field).fill(value);
  }
});
```

---

# 完成條件

- [ ] 目標 feature 的所有場景測試通過
- [ ] `npx bddgen && npx playwright test --grep "{feature}"` 全部綠燈
- [ ] 回歸測試：`npx bddgen && npx playwright test` 無新增失敗
- [ ] 實作遵循最小原則（只做測試要求的）
- [ ] 所有頁面皆為 `'use client'`（靜態匯出模式）
- [ ] API 服務層透過 `lib/api/services.ts` 串接
