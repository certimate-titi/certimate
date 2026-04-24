# ToDoList 自動巡檢處理紀錄

**執行時間**：2026-04-25 04:07 (UTC+8)
**觸發方式**：排程任務 check-todo（titi-commander）
**執行模式**：自主執行（無人值守）

---

## 一、盤點摘要

對 `docs/ToDoList.md` 全部未完成項目進行程式碼比對，分三類盤點：

### 🔴 Feature 缺失（Gherkin Scenario）

| 項目 | 盤點結果 | 處理 |
|------|----------|------|
| Feature 07（錯題複習與 AI 教練）**高優先** | 後端 step definitions 齊全（20 Rules），但規格檔 feature-level @ignore 未移除 | ✅ 已修復 |
| Feature 21（番茄鐘）| 15 個 active Scenario，無 @ignore | ✅ 更新 ToDoList 為已完成 |
| Feature 11（資源庫管理）| 15 個 active Scenario，無 @wip | ✅ 更新 ToDoList 為已完成 |
| Feature 13（Dashboard）| 仍有 34 個 @ignore | 維持待辦 |
| Feature 03（知識心智圖）| 仍 @ignore | 維持待辦 |
| Feature 10（EDU CSV 匯入）| feature-level @ignore @command | 維持待辦 |
| Feature 16（異常維修管理）| feature-level @ignore @command | 維持待辦 |
| 其他項目 | 狀態未變 | 維持待辦 |

### 🟠 實作缺失（前端功能）

| 項目 | 盤點結果 |
|------|----------|
| /account/resource-library failure_reason | 已透過 tooltip 呈現，✅ 更新為已完成 |
| 其他項目 | 狀態未變，維持待辦 |

### 🟡 空態補強

| 項目 | 盤點結果 |
|------|----------|
| /account/resource-library failure_reason | 已透過 resourceParseService.getStatus() 輪詢 + tooltip 顯示，✅ 已完成 |
| /super-admin/exam-import | errorMessage 已 inline 顯示於 ImportJobsList，✅ 已完成 |
| /practice no-questions 查 job 表 | 仍為靜態文字 hint，未實際查詢 parse jobs | 維持待辦 |
| /library 空態 | Tab 切換由子元件各自處理，無統一空態管理 | 維持待辦 |

---

## 二、修復工作

### 2.1 Feature 07 @ignore 解封（高優先）

**問題**：`project/features/07-錯題複習與AI教練.feature` 整個 Feature 標記 `@ignore @query`，導致所有 scenario 被跳過。但後端 `backend/tests/features/07-*.feature` 已移除 @ignore（僅保留 @query），且 step definitions 完整覆蓋 20 個 Rules。

**修復內容**：

1. **移除 feature-level @ignore**：`@ignore @query` → `@query`
2. **解封 6 個 scenario-level @ignore**：
   - 「錯題側邊列表點擊切換顯示題目」→ `@playwright-e2e`（UI 互動測試）
   - 「使用者錯誤答案與正確答案對比顯示」→ `@playwright-e2e`（UI 互動測試）
   - 「PRO_PLUS 使用者查看引用來源切換」→ 移除 @ignore（API 級可驗證）
   - 「FREE 使用者解說區毛玻璃遮罩遮擋內容」→ 移除 @ignore（API 回傳 locked flag）
   - 「PRO_199 使用者月配額用盡後提示升級」→ 移除 @ignore（API 回傳 429）
   - 「無錯題時顯示回到儀表板連結」→ 移除 @ignore（API 回傳空列表）

3. **維持 @skip 的 13 個 AI 安全 scenario**（標記 `@epic-recon @infra-heavy @skip`）：
   - 需 Llama Guard / Gemini Flash safety classifier 等基礎設施
   - 包含：輸入長度限制、max_tokens、session 限制、prompt injection 偵測、PII 過濾、System Prompt 保護等

**修改檔案**：
- `project/features/07-錯題複習與AI教練.feature`

### 2.2 ToDoList.md 狀態更新

更新 6 個項目為已完成（[x]），附帶確認說明與時間戳記。

**修改檔案**：
- `docs/ToDoList.md`

---

## 三、仍待處理的項目統計

| 類別 | 未完成數 | 說明 |
|------|----------|------|
| 🔴 Feature 缺失 | 12 | Dashboard(5)、Knowledge(2)、Exam(1)、Account(1)、EDU(1)、SuperAdmin(3) |
| 🟠 實作缺失 | 6 | 逐題解析入口、下載 stub、番茄鐘邏輯、三層 Zoom、批次修復 UI、空節點按鈕 |
| 🟡 空態補強 | 2 | practice 查 job 表、library 空態 |
| **合計** | **20** | |

---

## 四、建議優先處理

1. **P1** — `/practice` no-questions 空態應主動查詢 `resource_parse_jobs` 取 `failure_reason`（符合 QA 三層驗收 Layer 3 規則）
2. **P1** — Feature 13（Dashboard）34 個 @ignore 解封（需逐一確認後端 step definitions 是否齊全）
3. **P2** — `/exam/results` 逐題解析入口 + 下載功能實作
4. **P2** — Feature 10（EDU CSV 匯入）解封
