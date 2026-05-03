# TiTi Commander 排程巡檢紀錄

**執行時間**：2026-05-04 20:01:36 UTC
**執行模式**：自動排程（check-todo scheduled task）
**執行者**：TiTi Commander CEO

---

## 巡檢摘要

掃描 `docs/ToDoList.md` 共 14 項未完成待辦，依可行性分析後處理 1 項。

| 分類 | 數量 | 說明 |
|------|------|------|
| 本次修復 | 1 | DPA UI |
| 待後端 API | 3 | review/schedule/weekly-reports Layer 3 |
| 需產品決策 | 2 | StudyBuddyBanner / SSE 進度 |
| 複雜度高（需人工） | 3 | 自動回溯 / 錯題熱力圖 / 通知偏好 API |
| 部署相關 | 3 | Cloud Run / 雲端驗證 / Playwright 補測 |
| 需 UI 設計 | 2 | mindmap 詳情面板 / 打氣語句 |

---

## 已完成項目

### 🔴 L58 `/edu-console` DPA 簽署 UI

**問題描述**：Feature 10 L58-65 規定機構管理員首次匯入學生前須簽署資料處理合約（DPA），但 edu-console/page.tsx 無任何 DPA 相關 UI。

**後端狀態**：✅ 完整
- API: `POST /b2b/dpa/sign`（簽署）、`GET /b2b/dpa`（查詢狀態）
- Service: `b2b_service.py` sign_dpa / get_dpa / import_students 含 DPA 驗證
- DB: `institutions` 表含 `dpa_signed_at`、`dpa_signer_name` 欄位
- Frontend services.ts: `signDpa(signerName)` / `getDpa()` 已存在

**修復內容**：

1. **DpaSignModal 元件**（新增）
   - 合約要點摘要（5 項重點）
   - 簽署人姓名 input
   - 同意 checkbox（必勾才可簽署）
   - 呼叫 `adminService.signDpa(signerName)` 提交
   - 錯誤處理 + loading 狀態

2. **DPA 狀態管理**（新增）
   - `dpaStatus` state + useEffect 在頁面載入時查詢 `adminService.getDpa()`
   - API 失敗時安全預設 `{ signed: false }`

3. **匯入攔截邏輯**（修改）
   - `handleImportClick` 回呼：未簽署 → 開啟 DPA modal；已簽署 → 開啟 CSV 匯入 modal
   - 三處「匯入學生名單」按鈕全部改用 `handleImportClick`

4. **未簽署提示 Banner**（新增）
   - 頁面底部固定 amber Banner，提示「匯入學生前須先簽署 DPA」
   - 「立即簽署」按鈕開啟 DPA modal
   - 已簽署後自動隱藏

5. **簽署後流程**（新增）
   - `handleDpaSigned`：更新 dpaStatus → 關閉 DPA modal → 自動開啟 CSV 匯入 modal

**驗證結果**：
- TypeScript 編譯零錯誤（`npx tsc --noEmit`）
- 工程師自檢 9 項全部通過
- QA 驗收 6 項全部通過

---

## 未處理項目狀態更新

### 🔴 待處理（4 項）

| 項目 | 首見 | 阻塞原因 |
|------|------|---------|
| L51 StudyBuddyBanner | 2026-04-27 | 元件不存在，需產品決策功能範圍 |
| L57 exam/workspace 打氣語句 | 2026-04-29 | 後端 API endpoint 缺失（EncouragementService 存在但無 REST 端點） |
| L59 practice 自動回溯 | 2026-05-04 | 後端 difficulty_progression API 完整但前端整合複雜，需人工處理 |
| L62 mindmap 節點詳情面板 | 2026-05-01 | UI 設計未定（Feature 03b 要求溯源面板 + AI 教練互動） |

### 🟠 待處理（5 項）

| 項目 | 首見 | 阻塞原因 |
|------|------|---------|
| L80 exam/setup SSE 進度 | 2026-05-01 | 需後端 SSE 端點 + 前端 EventSource 整合 |
| L81 account 通知偏好 API | 2026-05-01 | 需後端 notification preferences API |
| L82 knowledge 錯題熱力圖 | 2026-05-04 | 大型 UI 功能，需獨立熱力圖層 + 錯題明細互動 |

### 🟡 待後端（3 項）

| 項目 | 首見 | 前置條件 |
|------|------|---------|
| L99 review Layer 3 | 2026-04-28 | 需後端 examGenerationJobs API |
| L102 schedule Layer 3 | 2026-04-29 | 需後端 scheduleJobs API |
| L103 weekly-reports Layer 3 | 2026-04-30 | 需後端 weeklyReportJobs API |

---

## 修改檔案清單

| 檔案 | 動作 |
|------|------|
| `frontend/app/edu-console/page.tsx` | 新增 DpaSignModal + DPA 狀態管理 + 攔截邏輯 + Banner |
| `docs/ToDoList.md` | L58 標記完成，更新摘要計數 |
| `docs/todo-processing-2026-05-04T20-01-36.md` | 本紀錄檔（新增） |
