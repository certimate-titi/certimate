# Link Contracts — 全站關鍵跨頁連結登記

> 登記目的：QA Layer 4 必須對每一條登記的連結驗證「來源頁參數 → 目標頁狀態」一致。
> 新增/修改 `<Link>` 或 `router.push` 必須同步更新此檔，CTO Review 會卡關。

## 連結清單

### 1. 學習庫 → 知識地圖（解析內容）

- **來源**：`frontend/app/account/resource-library/page.tsx` L219
- **目標**：`frontend/app/knowledge/page.tsx`
- **必傳 query**：`subjectId`（資源所屬科目）、`resourceId`
- **目標頁必呈現狀態**：
  - `activeSubjectId` 必須等於 query.subjectId（含 UserSubject.id 與 subjectId 兩種匹配）
  - `selectedDocId` 必須等於 query.resourceId
  - `expandedDocId` 必須等於 query.resourceId（自動展開該資源的 chunks）
- **失敗模式**：少帶 subjectId → active subject 不符 → 退回該科目首筆
- **驗證 SOP**：登入 → /account/resource-library → click「解析內容」→ 驗 URL 含 subjectId+resourceId → 驗右上角科目切換器顯示正確科目 → 驗左側資料列表選中該資源

### 2. 學習庫 → 題目候選

- **來源**：`frontend/app/account/resource-library/page.tsx` L226
- **目標**：`frontend/app/resources/[id]/candidates/page.tsx`
- **動態路由 param**：`id` = resource_id
- **目標頁必呈現狀態**：
  - 從 `window.location.pathname` 解析 resource_id（**禁用 useParams**，會被 Firebase rewrite stub 騙）
  - 載入該 resource 的 question_candidates
- **失敗模式**：用 useParams() 讀到字面值 `[id]` 或 `detail`
- **驗證 SOP**：登入 → /account/resource-library → click「題目確認」→ 驗 URL 路徑 → 驗候選題目列表非空（或正確空態）

### 3. Dashboard → 各功能入口

- **來源**：`frontend/app/dashboard/page.tsx`
- **目標**：`/practice` `/exam/setup` `/knowledge` `/review` 等
- **必傳 query**：`subjectId`（從 SubjectSwitcher）
- **驗證**：每個進入點 click 後目標頁的 active subject 必須一致

### 4. 知識地圖節點 → 練習/測驗

- **來源**：`frontend/app/knowledge/page.tsx` L780–781
- **目標**：`/practice?nodeId=X&nodeName=...`、`/exam/setup?nodeId=X`
- **必傳 query**：`nodeId`（必）、`nodeName`（建議，UI 顯示用）
- **目標頁必呈現狀態**：練習/測驗以該節點為範圍出題

### 5. 練習頁 → 結果頁

- **來源**：`frontend/app/practice/page.tsx`
- **目標**：`/exam/results/[id]`
- **動態路由 param**：`id` = attempt_id
- **驗證**：結果頁顯示對應 attempt 的成績與題目回顧

---

## 待補登記（QA 巡檢時擴充）

- [ ] /resources/[id]/* 各子頁
- [ ] /super-admin/* 各管理頁
- [ ] /edu-console/* 機構管理頁
- [ ] /pricing → /account/subscribe
- [ ] /onboarding 各步驟跳轉

---

## 新增規則

PR 觸發 Layer 4 時：
1. 在此檔案新增/更新對應條目
2. 在 QA 報告中附 Link Contract 卡（見 `qa-charter.md` Layer 4）
3. CTO Review 會檢查兩處是否同步
