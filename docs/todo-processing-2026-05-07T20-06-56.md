# TiTi Commander 排程巡檢紀錄 — 2026-05-07T20:06:56 UTC

## 觸發方式
自動排程巡檢（scheduled task: check-todo）

## 檢查結果
ToDoList.md 尚有多項未完成待辦事項，本次處理以下兩項：

---

## 已處理項目

### 1. 🟠 `/knowledge` — searchQuery 未傳遞給 MindMapTree/ForceGraph（2026-05-07 新增）

**問題描述**：searchQuery state 僅用於過濾左側文件列表，未傳給 MindMapTree 或 ForceGraph 元件。Feature 03 Scenario 期待「心智圖導覽區節點可依關鍵字即時篩選」，實際不符。

**修復內容**：

1. **ForceGraph.tsx**：
   - 新增 `searchQuery?: string` prop
   - 搜尋時不匹配的節點 opacity 降至 0.2，連線 opacity 降至 0.08
   - useEffect 依賴陣列加入 searchQuery

2. **MindMapTree.tsx**：
   - 新增 `searchQuery?: string` prop
   - 實作遞迴樹狀過濾：保留匹配節點及其祖先路徑
   - 搜尋啟用時自動展開全部節點
   - 搜尋無結果時顯示空態提示（Search icon + 「無符合…的知識節點」）

3. **knowledge/page.tsx**：
   - ForceGraph 與 MindMapTree 呼叫處新增 `searchQuery={searchQuery}` prop

**驗證**：TypeScript 編譯零錯誤（`npx tsc --noEmit` 通過）

---

### 2. 🔴 Feature 13 科目切換器 Scenario 未同步（2026-05-07 新增）

**問題描述**：SubjectSwitcher 已於 2026-05 從 dashboard 移除（改由 /knowledge + /onboarding 承載），Feature 13 L40-58 的「備考多科時顯示科目切換器」和「切換科目後儀表板數據更新」兩個 Scenario 必然失敗。

**修復內容**：
- 將 Rule 標題改為「儀表板應透過學習排程卡片展示全部備考科目」
- 標記 `@removed` 並加上註解說明歷史原因
- 改寫兩個 Example Scenario：
  - 「備考多科時學習排程卡片列出全部科目」— 驗證 ScheduleWeekCard 顯示科目+倒數+今日複習入口
  - 「儀表板預設顯示第一個科目的學習數據」— 驗證核心指標卡預設對應第一科

---

## Git 紀錄
- Commit: `b54b73d` on main
- Message: `fix: 知識地圖搜尋節點篩選 + Feature 13 科目切換器 Scenario 同步`
- Push: ❌ 失敗（sandbox 無 GitHub 認證），需使用者手動 `git push origin main`

---

## 未處理項目（待後續巡檢）

### 🔴 高優先
- `/knowledge` — Feature 03 搜尋節點 Scenario：前端已修復，但 Scenario 仍需確認 step definitions 是否對齊新實作
- `/exam/workspace` — Feature 21 番茄鐘互動 UI 缺失（3 個 Scenario 無對應前端觸發路徑）
- `/exam/workspace` + `/practice` — AI inference 判斷按鈕無 Feature Scenario
- `/dashboard` — 模式 tooltip + 無科目 modal 路徑無 Feature Scenario
- `/knowledge` — 「分享知識節點」無 Scenario 且未實作
- `/account/weekly-reports` — Feature 14 未覆蓋 reports 為空的 UI 情境

### 🟠 中優先
- `/exam/workspace` — 番茄鐘互動 UI 全部缺失
- `/knowledge` — Feature 03b 摺疊按鈕 UI 缺失
- `/knowledge` — AI 教練灑花恭喜獎章動畫未實作

### 🟡 低優先
- `/exam/setup` — 空文件態未主動查 parse job failure_reason（Layer 3 未達）
- `/dashboard` — upload failed 未查 resource_parse_jobs.failure_reason
- `/knowledge` — PROCESSING 狀態未區分三種情境
