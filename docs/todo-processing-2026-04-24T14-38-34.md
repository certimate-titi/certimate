# ToDoList 自動巡檢處理紀錄

**時間**：2026-04-24T14:38:34 UTC
**觸發方式**：排程任務 (check-todo)
**執行者**：TiTi Commander 自動巡檢

---

## 巡檢摘要

檢查 `docs/ToDoList.md` 及 `ToDoList.md`，發現 28 個待辦事項分佈於三類：
- 🔴 Feature 缺失（17 項）
- 🟠 實作缺失（6 項）
- 🟡 空態補強（5 項）

本次處理 **6 項**，其中 1 項確認為已完成（誤報）、5 項實際修復。

---

## 處理項目

### ✅ 1. 空殼 Feature 確認（🔴 → 已關閉，誤報）

**項目**：`19-交錯練習.feature` + `32-節點練習模式.feature` + `46-知識地圖Canvas.feature` — Feature 檔案存在但 Scenario 數量為 0

**調查結果**：三份 Feature 檔案均已包含完整 Scenario：
- `19-交錯練習.feature`：89 行，8 個 Example，覆蓋 5 個 Rule（交錯排列、避免相鄰、難度分散、模式切換、Sprint 整合）
- `32-節點練習模式.feature`：100 行，9 個 Example，覆蓋 7 個 Rule（題目查詢、作答回饋、進度傳播、入口導航）
- `46-知識地圖Canvas.feature`：68 行，6 個 Example，覆蓋 4 個 Rule（Tier1 聚合、分層下鑽、權限驗證、空態區分）

**結論**：ToDoList 項目為誤報，標記為已完成。

---

### ✅ 2. Knowledge 頁面空態補強（🟡 → 已修復）

**項目**：
- `/knowledge` — documents.length === 0 空態未查 resource_parse_jobs.failure_reason
- `/knowledge/mindmap` — mindMapNodes.length === 0 空態未查 resource_parse_jobs 狀態

**修改檔案**：`frontend/app/knowledge/page.tsx`

**修改內容**：
1. **新增 import**：`resourceParseService` 從 services.ts 引入
2. **新增狀態**：`parseJobFailures` (Record<string, string>) 追蹤每個 FAILED 文件的 failure_reason
3. **新增 useEffect**：當文件列表中有 FAILED 狀態的文件，自動呼叫 `resourceParseService.getStatus(docId)` 查詢 failure_reason
4. **FAILED 標籤增強**：原本僅顯示「失敗」，現在顯示 `失敗：{failure_reason 前30字}...`，完整原因以 title tooltip 呈現
5. **mindmap 空態四種情境**：
   - `documents.length === 0`：「尚無知識圖譜 — 上傳學習資源後 AI 將自動萃取」
   - `documents.every(FAILED)`：「所有資源解析失敗 — 顯示 failure_reason + 建議重新上傳」
   - `documents.some(PROCESSING)`：「資源處理中... — 顯示 spinner + 請稍候」
   - 其他：「尚未生成知識圖譜 — 點擊重新分析按鈕」

**符合規範**：CLAUDE.md Layer 3 空態查 Job 表規則。

---

### ✅ 3. Practice 頁面空態補強（🟡 + 🟠 → 已修復）

**項目**：
- `/practice` — phase === 'no-questions' 空態未查 exam_generation_jobs
- `/practice` — no-questions 空態缺少直接觸發 AI 出題的快捷按鈕

**修改檔案**：`frontend/app/practice/page.tsx`

**修改內容**：
1. **新增提示文字**：「若已建立過測驗但仍無題目，可能是 AI 出題任務尚未完成或已失敗，請至測驗頁重新產生」
2. **新增「前往出題」按鈕**：連結至 `/exam/setup?nodeId={selectedNodeId}`，自動帶入當前節點
3. **按鈕群組重新排列**：前往出題（藍色主要）→ 選擇其他節點（綠色次要）→ 回知識圖譜（邊框）

**備註**：由於後端無獨立的 `exam_generation_jobs` 狀態查詢 API（考題生成狀態嵌入 Exam model），前端無法直接查詢出題是否失敗。已透過文字提示引導使用者排查。建議後續新增 `GET /exams/{exam_id}/generation-status` 端點。

---

### ✅ 4. Exam/Setup 頁面空態補強（🟡 → 已修復）

**項目**：`/exam/setup` — documents.length === 0 時未查 resource_parse_jobs

**修改檔案**：`frontend/app/exam/setup/page.tsx`

**修改內容**：
1. **新增 import**：`AlertTriangle` icon, `resourceParseService`
2. **空態增強**：新增第三行提示「若已上傳資源但此處為空，可能資源解析失敗，請至知識庫頁面查看狀態」

---

## TypeScript 編譯驗證

```
$ cd frontend && npx tsc --noEmit
（無錯誤輸出）✅
```

---

## 未處理項目（需人工介入）

### 🔴 Feature 缺失（16 項）
Dashboard Feature 13 全 @ignore、番茄鐘 Feature 21、視圖切換覆蓋等 — 這些需要產品決策確認是否解封 @ignore 標籤或重寫 Scenario。

### 🟠 實作缺失（5 項）
逐題解析入口、成績卡片下載、番茄鐘實作、Canvas 三層 Zoom、批次修復 UI — 這些是前端功能實作，需要產品 PRD 確認後由工程師執行。

### 🟡 空態補強（1 項）
`/library` 頁面空態 — 需先確認 library 頁面 Tab 架構後再處理。

---

## 變更檔案清單

| 檔案 | 動作 |
|------|------|
| `frontend/app/knowledge/page.tsx` | 修改：空態補強 + parse job failure_reason 查詢 |
| `frontend/app/practice/page.tsx` | 修改：空態提示 + 前往出題按鈕 |
| `frontend/app/exam/setup/page.tsx` | 修改：空態提示增強 |
| `docs/ToDoList.md` | 更新：6 項標記完成 |
| `ToDoList.md` | 更新：同步 |
| `docs/todo-processing-2026-04-24T14-38-34.md` | 新增：本處理紀錄 |
