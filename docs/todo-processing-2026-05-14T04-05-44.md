# ToDoList 排程巡檢紀錄 — 2026-05-14T04:05 (UTC+8)

> **執行者**：TiTi Commander v2.1 排程巡檢（自動）
> **觸發方式**：Scheduled Task `check-todo`

---

## 巡檢摘要

本次排程巡檢處理 ToDoList.md 中 6 項 unchecked 待辦：

| # | 項目 | 分類 | 處理方式 | 狀態 |
|---|------|------|----------|------|
| 1 | `/today/reviews` Layer 3 空態 | 前端修復 | 新增 parseJobFailures 偵測 + 警示卡 UI | ✅ 完成 |
| 2 | `/today/reviews` Feature 覆蓋 | BDD Scenario | Feature 42 新增 5 Rules / 7 Scenarios | ✅ 完成 |
| 3 | AI inference 判斷按鈕 BDD 缺口 | BDD Scenario | Feature 20 新增 1 Rule / 4 Scenarios | ✅ 完成 |
| 4 | 模式 tooltip 說明按鈕 BDD 缺口 | BDD Scenario | Feature 13 新增 1 Rule / 2 Scenarios | ✅ 完成 |
| 5 | 儀表板行內加科目 BDD 缺口 | BDD Scenario | Feature 13 新增 1 Rule / 2 Scenarios | ✅ 完成 |
| 6 | weekly-reports 空態 BDD 缺口 | BDD Scenario | Feature 14 新增 1 Example | ✅ 完成 |

---

## 詳細處理紀錄

### 1. `/today/reviews` Layer 3 空態修復

**問題**：`items.length === 0` 時直接顯示「今日無到期複習」，未查後端 job 表，無法區分「真正無到期」vs「資源解析 FAILED 導致鷹架未生成」。

**修復內容**（`frontend/app/today/reviews/page.tsx`）：
- 新增 `parseJobFailures` state
- 新增 `useEffect`：items 載入後若為空，自動查 `documentService.list()` 過濾 FAILED 文件，逐個呼叫 `resourceParseService.getStatus()` 取得 failure_reason
- 空態 UI 新增紅色警示卡（`data-testid="reviews-empty-parse-failures"`）：
  - XCircle icon + 「部分資源解析失敗，可能導致鷹架未生成」
  - 列出最多 3 個失敗資源（名稱 + failure_reason）
  - 「前往學習庫重新解析」連結至 `/account/resource-library`
- Import 新增：`XCircle`（lucide-react）、`documentService`/`resourceParseService`（services）
- **TypeScript 編譯零錯誤**

**設計決策**：
- 沿用 `/today/page.tsx` 既有的 Layer 3 pattern（相同的 documentService.list + getStatus 流程）
- 最多顯示 3 個失敗（避免頁面過長，與 /practice 等頁面一致）
- 警示卡置於空態卡片上方（先看問題，再看引導）

### 2. `/today/reviews` Feature Scenario 覆蓋

**修改檔案**：`project/features/42-今日學習首頁.feature`

新增 5 個 Rule：
1. **SM-2 鷹架複習清單應顯示到期項目的詳細資訊**（3 Examples）
   - 顯示到期複習項目清單（chapter_heading / repetitions / interval_days）
   - 複習卡片顯示類型標籤
   - 複習卡片提供「現在複習」連結
2. **逐項作答流程與複習回饋**（1 Example）
   - 點擊「現在複習」導向閱讀頁
3. **複習清單空態應提供引導文字**（1 Example）
   - 無到期項目時顯示空態引導
4. **Layer 3 空態查 Job 表**（2 Examples）
   - 空清單偵測到資源解析失敗
   - 空清單無解析失敗時不顯示警示

### 3. AI Inference 判斷按鈕 BDD Scenario

**修改檔案**：`project/features/20-信心度校準.feature`

新增 Rule「後置（UI）- 作答後應顯示 AI inference 判斷按鈕」（4 Examples）：
- 練習頁作答後顯示三個判斷選項
- 使用者選擇「保留我的答案」→ judgment=keep_mine
- 使用者選擇「採信 AI」→ judgment=accept_ai
- 使用者選擇「略過」→ judgment=skip

**備註**：目前僅 `/practice` 有實作（L776-784），`/exam/workspace` 尚未整合 blindInferenceService。

### 4. 模式 Tooltip 說明按鈕 BDD Scenario

**修改檔案**：`project/features/13-個人儀表板與成就系統.feature`

新增 Rule「後置（UI）- 備考模式 tooltip 說明按鈕」（2 Examples）：
- 點擊模式 tooltip 按鈕顯示策略說明彈窗
- 再次點擊收合彈窗

**實作確認**：dashboard/page.tsx L82 `showModeTooltip` state + L495 onClick toggle + L500 彈窗渲染。

### 5. 儀表板行內加科目 Modal BDD Scenario

**修改檔案**：`project/features/13-個人儀表板與成就系統.feature`

新增 Rule「後置（UI）- 儀表板無科目時應提供行內新增科目入口」（2 Examples）：
- 無科目使用者在儀表板看到「開始選擇科目」入口
- 點擊後進入科目選擇流程

**實作確認**：dashboard/page.tsx L424-427 顯示「開始選擇科目」按鈕。

### 6. Weekly Reports 空態 BDD Scenario

**修改檔案**：`project/features/14-社群歸屬與主動關懷.feature`

在既有 Rule「查看歷史週報列表」下新增 Example：
- 「週報列表為空時顯示引導說明」（顯示「尚無週報」+ 活躍用戶說明）

**實作確認**：`/account/weekly-reports` 已有空態 UI（Calendar icon + 說明文字）。

---

## 剩餘 Unchecked 項目（3 項）

| # | 項目 | 分類 | 備註 |
|---|------|------|------|
| 1 | `/exam/results` Certi 表情 UI | 前端實作 | Feature 06 要求動態情感表情，目前僅靜態文字 |
| 2 | `/knowledge` 分享知識節點 | 前端實作 + BDD | Feature 03 提及但無 Scenario 且未實作 |
| 3 | `/knowledge` Confetti 動畫 | 前端實作 | Feature 03 規格要求節點掌握時灑花，僅 /exam/results 有 |

---

## 修改檔案清單

| 檔案 | 操作 |
|------|------|
| `frontend/app/today/reviews/page.tsx` | 修改：Layer 3 空態偵測 + 警示卡 UI |
| `project/features/42-今日學習首頁.feature` | 修改：新增 /today/reviews 5 Rules / 7 Scenarios |
| `project/features/20-信心度校準.feature` | 修改：新增 AI inference 判斷 1 Rule / 4 Scenarios |
| `project/features/13-個人儀表板與成就系統.feature` | 修改：新增 tooltip + 行內加科目 2 Rules / 4 Scenarios |
| `project/features/14-社群歸屬與主動關懷.feature` | 修改：新增週報空態 1 Example |
| `docs/ToDoList.md` | 修改：勾選 6 項已完成 |
| `docs/todo-processing-2026-05-14T04-05-44.md` | 新增：本紀錄檔 |
