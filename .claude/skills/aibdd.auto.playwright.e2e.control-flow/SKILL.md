---
name: aibdd.auto.playwright.e2e.control-flow
description: Playwright E2E 全自動批次迴圈。掃描 features 目錄，為每個 .feature 展開完整的 4 phase TODO 清單（step-analysis → red → green → refactor），然後逐一執行直到全數完成。
user-invocable: true
argument-hint: "[feature-file-or-dir]"
input: feature 檔案路徑或 features 目錄
output: 每個 feature 完成完整的前端 Playwright BDD E2E 循環
---

# 指令

你是前端 Playwright BDD 全自動批次執行器。你的工作是：
1. 掃描 feature 檔案
2. 用 TodoWrite 建立完整的任務清單
3. 逐一執行每個任務直到全部完成
4. 不要停下來、不要問問題、不要等待指示

---

# 背景

## 與後端 BDD 的對照

| 面向 | 後端 (Python Behave) | 前端 (Playwright BDD) |
|------|---------------------|----------------------|
| 測試框架 | Behave + FastAPI TestClient | Playwright + playwright-bdd |
| 測試標的 | HTTP API Endpoint | 瀏覽器 UI 頁面 |
| Feature 來源 | `backend/tests/features/` | `project/features/*.feature`（SSOT 共用） |
| Step 位置 | `backend/tests/features/steps/` | `frontend/e2e/steps/` |
| 測試指令 | `behave tests/features/` | `npx bddgen && npx playwright test` |
| 紅燈失敗原因 | HTTP 404（API 未實作） | 缺少 Step / 頁面元素不存在 |
| 綠燈實作 | FastAPI endpoints + services | Next.js 頁面 + 元件 + API 服務層 |
| 資料庫 | Testcontainers PostgreSQL | 真實後端 API（需後端運行） |
| 5 Phase | schema → template → red → green → refactor | analysis → red → green → refactor |

## 前端 4 Phase 流程

前端不需要 Schema Analysis（無 DB schema），也不需要獨立的 Step Template phase（合併進 Red）。

```
Step Analysis → Red → Green → Refactor
     │            │       │        │
     │            │       │        └─ 測試保護下重構
     │            │       └─ 實作 UI 讓測試通過
     │            └─ 寫完整 step definitions（測試失敗：元素/頁面不存在）
     └─ 分析 feature 需要的 steps，盤點現有 steps，規劃缺少的 steps
```

---

# 前置條件

## 必要環境

1. **後端 API 運行中**：`http://localhost:8000/api/v1`（前端 E2E 測試依賴真實後端）
2. **npm install 完成**：`cd frontend && npm install`
3. **Playwright 已安裝**：`npx playwright install`

## 技術棧

- **框架**: Next.js 15 (App Router) + React 19 + TypeScript
- **測試**: Playwright + playwright-bdd
- **樣式**: TailwindCSS 4
- **Feature Files**: `project/features/*.feature`（前後端共用 SSOT）
- **Step Definitions**: `frontend/e2e/steps/**/*.ts`
- **Fixtures**: `frontend/e2e/fixtures/index.ts`（loginAs helper）
- **Global Setup**: `frontend/e2e/global-setup.ts`（測試帳號播種）
- **Config**: `frontend/playwright.config.ts`

## Tag 過濾（重要）

playwright.config.ts 中配置：
```
tags: 'not @ignore and not @command and not @manual'
```

- `@ignore` — 後端尚未實作的 feature（跳過）
- `@command` — 純 API 測試，無 UI（跳過）
- `@manual` — 手動測試場景（跳過）
- 其餘 → 前端需實作

## missingSteps 策略

```
missingSteps: 'skip-scenario'
```

尚未實作 step definitions 的場景會被自動跳過（不會報錯），允許漸進式新增。

---

# Step 1：掃描 Feature 檔案

讀取以下目錄，找出所有 `.feature` 檔案：

```
project/features/*.feature
```

按檔名排序，記錄完整路徑。

**過濾規則**：
- 排除檔案開頭有 `@ignore` 標籤的 feature
- 排除檔案開頭有 `@command` 標籤的 feature（純 API 測試）
- 排除檔案開頭有 `@manual` 標籤的 feature

如果使用者指定了單一 feature file，則只處理該檔案。

---

# Step 2：用 TodoWrite 建立任務清單

對每個 feature 檔案，建立 4 個 TodoWrite 任務。

格式規則：
- `content`：`{feature 檔名} — {phase 名稱}`
- `activeForm`：`{phase 動詞}：{feature 檔名}`
- `status`：全部設為 `pending`

範例（假設有 2 個 feature）：

```
content: "01-身分驗證.feature — Step Analysis"
activeForm: "分析 Steps：01-身分驗證.feature"
status: pending

content: "01-身分驗證.feature — Red"
activeForm: "執行紅燈：01-身分驗證.feature"
status: pending

content: "01-身分驗證.feature — Green"
activeForm: "執行綠燈：01-身分驗證.feature"
status: pending

content: "01-身分驗證.feature — Refactor"
activeForm: "執行重構：01-身分驗證.feature"
status: pending

content: "02-資源上傳.feature — Step Analysis"
activeForm: "分析 Steps：02-資源上傳.feature"
status: pending

...以此類推
```

建完 TODO 清單後，**立即進入 Step 3 開始執行**。

---

# Step 3：逐一執行每個任務

從第一個 pending 任務開始，依序處理。每個任務的執行流程：

```
標記 TodoWrite → in_progress
        ↓
使用 Skill 工具呼叫對應的 skill（帶入 feature file 路徑作為 args）
        ↓
標記 TodoWrite → completed
        ↓
前進到下一個 pending 任務
```

## 任務與 Skill 對照表

| 任務 phase | 呼叫的 Skill |
|-----------|-------------|
| Step Analysis | `/aibdd.auto.playwright.e2e.step-analysis` |
| Red | `/aibdd.auto.playwright.e2e.red` |
| Green | `/aibdd.auto.playwright.e2e.green` |
| Refactor | `/aibdd.auto.playwright.e2e.refactor` |

## 呼叫方式

使用 Skill 工具，將 feature file 的完整路徑作為 `args` 傳入。

---

# Step 4：最終回歸測試

所有任務都 completed 後，執行一次完整回歸測試：

```bash
cd frontend && npx bddgen && npx playwright test
```

- 通過 → 全部完成
- 失敗 → 閱讀錯誤、修正、重新執行，直到全部通過

---

# 全自動規則

1. **不要停下來問問題**。遇到問題就自己修正。
2. **不要跳過任何任務**。每個任務都必須完成。
3. **每個 Skill 完成後立即標記 completed**，然後前進到下一個。
4. **一次只有一個任務是 in_progress**。
5. **Skill 是 lazy loading**：每次呼叫都會完整載入該 phase 的規則，不用擔心 context compaction 後遺忘。

---

# 為什麼用 TodoWrite + Skill 工具

| 機制 | 解決的問題 |
|-----|----------|
| TodoWrite | 任務進度跨 compaction 持久化，不會丟失 |
| Skill 工具 | 每次呼叫都完整載入該 phase 的指令，不受 compaction 影響 |
| 逐一執行 | 一次只處理一個任務，減少 context 壓力 |

---

# Phase 詳細說明

## Phase 1: Step Analysis

**目標**：分析 feature file 需要哪些 step definitions，盤點已有的 steps，規劃缺少的 steps。

**做什麼**：
1. 解析 feature file 中所有 Given/When/Then 步驟
2. 掃描 `frontend/e2e/steps/` 目錄，找出已存在的 step patterns
3. 對比找出缺少的 steps
4. 規劃缺少 steps 的檔案結構與分類
5. 確認 feature 中使用的頁面路由是否已存在

**不做什麼**：
- 不寫程式碼
- 不實作任何 step

**產出**：缺少步驟的清單 + 檔案規劃

## Phase 2: Red（紅燈）

**目標**：寫完整的 step definitions，讓測試可執行但失敗（紅燈）。

**做什麼**：
1. 根據 Step Analysis 的規劃，建立新的 step definition 檔案
2. 每個 step 完整實作 Playwright 操作邏輯
3. 確保 `e2e/fixtures/index.ts` 有所需的 fixtures
4. 執行 `npx bddgen && npx playwright test` 確認紅燈

**紅燈的原因**（前端特色）：
- 頁面元素不存在（UI 尚未實作）
- 導航路由不存在
- 表單欄位、按鈕找不到
- API 回應格式不符預期

**不做什麼**：
- 不修改前端頁面程式碼
- 不實作新的 React 元件

## Phase 3: Green（綠燈）

**目標**：寫最少的前端程式碼讓測試通過。

**做什麼**：
1. 執行測試 → 看錯誤 → 修正 → 再測試（trial-and-error）
2. 實作所需的 Next.js 頁面、React 元件
3. 更新 `lib/api/services.ts` 串接後端 API
4. 確保所有 step definitions 通過

**不做什麼**：
- 不做測試沒要求的 UI 優化
- 不加額外功能

## Phase 4: Refactor（重構）

**目標**：在測試保護下改善程式碼品質。

**做什麼**：
1. 重構前確認綠燈
2. 小步改進（一次一個重構點）
3. 每次重構後確認綠燈
4. 清除測試 warnings

**不做什麼**：
- 不增加新功能
- 不大幅改動架構

---

# Step Definition 組織規範

## 目錄結構

```
frontend/e2e/
├── fixtures/
│   └── index.ts           # Custom fixtures (loginAs, etc.)
├── global-setup.ts        # Test account seeding
├── helpers/
│   └── jwt.ts             # JWT token helper
└── steps/
    ├── auth/              # 身分驗證相關 steps
    ├── exam/              # 測驗流程 steps
    ├── knowledge/         # 知識心智圖 steps
    ├── onboarding/        # 引導流程 steps
    ├── dashboard/         # 儀表板 steps
    ├── review/            # 錯題複習 steps
    ├── feedback/          # 意見反饋 steps
    ├── resource/          # 資源管理 steps
    └── common/            # 跨領域共用 steps
```

## 命名規則

- 按業務領域分目錄（與後端一致）
- 每個檔案可包含相關的多個 steps（不需要一檔一 step）
- 使用 `.steps.ts` 副檔名
- Import `{ createBdd }` from `playwright-bdd` 和 custom `test` from fixtures

## Step Definition 範例

```typescript
import { createBdd } from 'playwright-bdd';
import { test } from '../../fixtures';

const { Given, When, Then } = createBdd(test);

Given('使用者已登入為 {string}', async ({ loginAs }, email: string) => {
  await loginAs(email, 'Password1!');
});

When('使用者點擊「{string}」按鈕', async ({ page }, buttonText: string) => {
  await page.getByRole('button', { name: buttonText }).click();
});

Then('頁面應顯示「{string}」', async ({ page }, text: string) => {
  await expect(page.getByText(text)).toBeVisible();
});
```

---

# 測試指令

```bash
# 開發階段：執行特定 feature（快速迭代）
cd frontend && npx bddgen && npx playwright test --grep "身分驗證"

# 完成驗證：執行所有測試（回歸測試）
cd frontend && npx bddgen && npx playwright test

# UI 模式（互動式除錯）
cd frontend && npx bddgen && npx playwright test --ui

# 有頭模式（看得到瀏覽器）
cd frontend && npx bddgen && npx playwright test --headed
```

---

# 完成條件

**只有當以下全部通過時，才算完成**：

- [ ] 所有 feature 的 4 個 phase 都完成
- [ ] `npx bddgen && npx playwright test` 通過
- [ ] 測試輸出無 warnings
- [ ] TodoWrite 所有任務都 completed
