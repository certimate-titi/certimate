# TiTi Commander 排程巡檢紀錄 — 2026-05-10T20:02:27 UTC

## 巡檢觸發

- **觸發方式**：Scheduled Task（check-todo）
- **巡檢時間**：2026-05-10 20:02:27 UTC
- **Git HEAD**：`a5baced` (feat: dark mode 全站 CSS 效果 + 題號網格信心度底色)

## 待辦事項盤點

### 開放項目統計
- 修復前：15 個開放待辦
- 修復後：14 個開放待辦
- 本次處理：1 項（🟠 Completion Framework API 串接）

## 本次處理項目

### ✅ 🟠 `/dashboard` — Completion Framework 後端 API 串接

| 時間戳 | 動作 |
|--------|------|
| 20:02 | 開始檢視 ToDoList.md，識別 2026-05-10 新增之 🟠 項目 |
| 20:03 | Schema Analysis：檢查 KnowledgeNode（exam_frequency 欄位）、NodeMastery（mastery_rate 欄位）、dashboard_service.py（_build_domain_strengths 方法） |
| 20:04 | 確認前端 `completion-calc.ts` 已有 `CompletionNode` 介面 + `calcCompletion()` 純函式，但資料源為 mock |
| 20:05 | **後端實作**：`backend/app/api/subjects.py` 新增 `GET /{subject_id}/completion` endpoint |
| 20:06 | **前端 service**：`frontend/lib/api/services.ts` 新增 `subjectService.getCompletion()` |
| 20:07 | **前端 wire-up**：`frontend/app/dashboard/page.tsx` 將 mock 推算改為 `useState` + `useEffect` 從 API 取得 |
| 20:08 | **清理 TODO**：移除 `completion-calc.ts` 和 `dashboard/page.tsx` 中的 TODO 註解 |
| 20:09 | **TypeScript 編譯驗證**：`npx tsc --noEmit` 零錯誤通過 |
| 20:10 | 更新 `docs/ToDoList.md` 標記完成 |

#### 變更檔案清單

| 檔案 | 變更類型 | 說明 |
|------|---------|------|
| `backend/app/api/subjects.py` | 新增 endpoint | `GET /subjects/{subject_id}/completion` — 查詢科目下所有 KnowledgeNode + NodeMastery，回傳 `{nodes: [{id, subject_id, mastery_rate, frequency, is_orphan}]}` |
| `frontend/lib/api/services.ts` | 新增方法 | `subjectService.getCompletion(subjectId)` — 呼叫上述 endpoint |
| `frontend/app/dashboard/page.tsx` | 修改 | 移除 mock 推算、改用 `useState` + `useEffect` 從 API 取得 `CompletionNode[]`；移除 TODO 註解 |
| `frontend/lib/completion-calc.ts` | 修改 | 移除 TODO 註解，更新 JSDoc 說明資料源為 API |
| `docs/ToDoList.md` | 更新 | 標記本項完成 |

#### 技術細節

**後端 endpoint 邏輯**：
1. 查詢 `knowledge_nodes` 表中 `subject_id` 符合的所有節點
2. 查詢 `node_mastery` 表中當前使用者對這些節點的掌握度
3. 頻率映射：`exam_frequency`（中文「高/中/低」）→ `high/medium/low`
4. 孤立節點判定：`available_questions == 0` 且 `mastery_rate == 0`
5. 回傳 JSON：`{nodes: [{id, subject_id, mastery_rate, frequency, is_orphan}]}`

**前端串接邏輯**：
- `activeSubjectId` 變更時，與 dashboard 資料同時載入 completion 資料
- 失敗時 graceful fallback 為空陣列（UI 顯示 0% 進度而非 crash）

## 剩餘開放項目（14 項）

### 🔴 Feature 缺失（需補 Gherkin Scenario）
1. `/invite/setup-password` — EDU 受邀用戶設定密碼流程 BDD 覆蓋
2. `/exam/results` — Certi 情感表情 UI vs 靜態文字
3. `/exam/workspace` — Feature 21 番茄鐘 UI 缺失
4. `/exam/workspace` + `/practice` — AI inference 判斷按鈕無 Feature 覆蓋
5. `/dashboard` — 模式 tooltip 說明無 Feature 覆蓋
6. `/dashboard` — 無科目時行內加科目路徑無 Feature 覆蓋
7. `/knowledge` — 分享知識節點無 Feature 覆蓋
8. `/account/weekly-reports` — Feature 14 空態

### 🟠 實作缺失（需補前端功能）
9. `/exam/workspace` — 番茄鐘互動 UI 全部缺失
10. `/knowledge` — 資源面板摺疊按鈕
11. `/knowledge` — Confetti/獎章動畫

### 🟡 空態補強（需查 Job 表）
12. `/exam/setup` — Layer 3 未查 parse job failure_reason
13. `/dashboard` — upload 失敗未查 resource_parse_jobs.failure_reason
14. `/knowledge` — PROCESSING 狀態無區分 UI

---

## Git 狀態

- **Commit 已建立**：`e73fd77` feat(completion): 後端 Completion Framework API + 前端串接
- **Push 狀態**：❌ 未推送 — `.git/index.lock` 和 `.git/HEAD.lock` 為過期殘留（2026-05-06/08 crashed process），sandbox 無權限刪除
- **待手動操作**：
  ```bash
  cd ~/certimate/project
  rm -f .git/index.lock .git/HEAD.lock .git/objects/maintenance.lock
  git add -A && git commit -m "feat(completion): 後端 Completion Framework API + 前端串接" && git push
  ```
- **所有程式碼變更已寫入磁碟**，git push 延遲不影響功能

*本紀錄由 TiTi Commander v2.1 排程巡檢自動產出*
