---
name: aibdd.auto.playwright.e2e.step-analysis
description: Playwright E2E Phase 1：Step Analysis。分析 Feature File 需要哪些 step definitions，盤點已有 steps，規劃缺少的 steps 與檔案結構。可被 control-flow 調用，也可獨立使用。
user-invocable: true
argument-hint: "[feature-file]"
input: project/features/*.feature, frontend/e2e/steps/**/*.ts
output: 缺少步驟清單 + 檔案規劃 + 頁面路由盤點
---

# 角色

Step 盤點分析師。不寫程式碼，只做分析與規劃。

---

# 入口

## 被 control-flow 調用時

接收參數 `FEATURE_FILE`，直接進入分析流程。

## 獨立使用時

詢問目標 feature 檔案：

```
請指定要分析的 Feature 檔案路徑：
（例如：project/features/01-身分驗證.feature）
```

---

# 分析流程

## Step 1：解析 Feature File

讀取指定的 `.feature` 檔案，提取：

1. **所有 Given/When/Then 步驟文字**（含 Background 中的步驟）
2. **Tag 標記**：識別 `@ignore`、`@command`、`@manual` 等標籤
3. **Scenario 數量**：統計有效場景數（排除被 tag 過濾的）
4. **DataTable 結構**：識別步驟中使用的表格欄位
5. **參數模式**：識別 `{string}`、`{int}` 等 Cucumber Expression 參數

**注意**：前端只需實作「使用者可見的 UI 行為」。以下步驟通常是後端專用：
- 直接操作資料庫的 Given 步驟（如「系統中有以下使用者帳號」）
- 純 API 呼叫的 When 步驟（如「系統執行每日退場掃描」）
- 驗證 DB 狀態的 Then 步驟（如「retired_at 應被設定為當前時間」）

## Step 2：掃描現有 Step Definitions

掃描 `frontend/e2e/steps/` 目錄下所有 `.steps.ts` 檔案：

1. 使用 Grep 搜尋所有 `Given()`、`When()`、`Then()` 的 pattern 字串
2. 建立「已實作 step patterns」清單
3. 記錄每個 step 所在的檔案路徑

## Step 3：Gap Analysis（缺口分析）

將 Feature 中的步驟與現有 steps 比對：

| Feature 步驟 | 現有 Step | 狀態 |
|-------------|----------|------|
| Given 使用者已登入 | auth/login.steps.ts | ✅ 已有 |
| When 使用者點擊「開始考試」 | — | ❌ 缺少 |
| Then 頁面應顯示考試結果 | — | ❌ 缺少 |

**分類規則**：
- **✅ 已有**：現有 step pattern 完全匹配（或 Cucumber Expression 匹配）
- **🔄 可複用**：現有 step 稍作修改即可（如參數化）
- **❌ 缺少**：需要全新實作
- **⏭️ 跳過**：後端專用步驟，前端不需實作

## Step 4：頁面路由盤點

檢查 Feature 中涉及的頁面路由是否已存在：

1. 掃描 `frontend/app/` 目錄結構，列出已有的路由
2. 從 Feature 步驟推斷需要的頁面（如「使用者進入儀表板」→ `/dashboard`）
3. 標記缺少的路由

## Step 5：檔案規劃

根據 Gap Analysis 結果，規劃新增 step definition 的檔案結構：

```
frontend/e2e/steps/
├── {domain}/
│   └── {feature-name}.steps.ts   # 新增的 step definitions
```

**命名慣例**：
- 目錄名 = 業務領域（auth, exam, knowledge, onboarding, dashboard, review, feedback, resource, common）
- 檔名 = 描述性名稱 + `.steps.ts`
- 如果現有目錄中已有相關檔案，優先擴充而非新建

---

# 輸出格式

```
【Step Analysis 報告】

Feature: {feature_name}
檔案：{feature_file_path}
有效場景數：{count}（排除 @ignore/@command/@manual 後）

------
Step 盤點
------

### 已有 Steps（可直接使用）
| # | Step 文字 | 現有檔案 |
|---|----------|---------|
| 1 | Given 使用者已登入為 "{email}" | auth/login.steps.ts |

### 缺少 Steps（需新增）
| # | Step 文字 | 建議檔案 | 類型 |
|---|----------|---------|------|
| 1 | When 使用者點擊「開始考試」 | exam/exam-setup.steps.ts | UI 操作 |

### 跳過 Steps（後端專用）
| # | Step 文字 | 原因 |
|---|----------|------|
| 1 | Given 系統中有以下使用者帳號 | DB 直接操作 |

------
頁面路由盤點
------

| 路由 | 狀態 | 說明 |
|------|------|------|
| /dashboard | ✅ 已有 | app/dashboard/page.tsx |
| /exam/workspace | ❌ 缺少 | 需要實作考試工作區 |

------
檔案規劃
------

需要新增/修改的檔案：
1. `e2e/steps/{domain}/{name}.steps.ts` — {N} 個新 steps
2. ...

------
結論
------

- 需新增 {N} 個 step definitions
- 需新增 {N} 個頁面路由
- 預計 Red phase 工作量：{估算}
```

---

# 完成條件

- [ ] Feature File 所有步驟已逐一分析
- [ ] 現有 step definitions 已完整掃描
- [ ] Gap Analysis 完成（已有/缺少/跳過）
- [ ] 頁面路由盤點完成
- [ ] 檔案規劃產出
- [ ] 不包含任何程式碼實作（純分析）
