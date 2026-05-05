# ToDoList 排程巡檢處理紀錄

**時間**：2026-05-06 TiTi Commander 排程巡檢（自動執行）
**觸發**：Cowork 排程任務 `check-todo`

---

## 待辦清單狀態摘要

掃描 `docs/ToDoList.md` 後發現 15 項未完成待辦（🔴7 🟠4 🟡4）。
本次處理 4 項，優先選取安全性高、自我封閉、低風險的任務。

---

## 已處理項目

### 1. 🔴 `/radar-demo` — 新增 isSuperAdmin 守衛（安全修復）

**問題**：開發沙盒頁無任何 auth 守衛，生產環境可被任何人直接訪問。

**修復**：
- 檔案：`frontend/app/radar-demo/page.tsx`
- 新增 `useAuth()` hook，取得 `isSuperAdmin`、`isAuthenticated`
- `useEffect` 中判斷：未認證或非 SUPER_ADMIN → redirect `/dashboard`
- 載入中或無權限時顯示 spinner（避免閃現內容）

**影響範圍**：僅 `/radar-demo` 頁面，無外部依賴。

---

### 2. 🟠 `/exam/results` — FREE 用戶 AI 考後總評 tier check

**問題**：Feature 06 規定 FREE 用戶「不應包含 AI 考後總評文字」並應顯示升級提示，
但 `page.tsx` 無 tier check，直接渲染 `aiSummary`。

**修復**：
- 檔案：`frontend/app/exam/results/page.tsx`
- 從 `useAuth()` 取得 `subscriptionTier` 和 `isAdmin`
- 計算 `isFreeUser = subscriptionTier === 'FREE' && !isAdmin`
- 條件渲染：
  - FREE 用戶：灰色區塊 + 「升級至 PRO_199 方案即可解鎖 AI 考後總評分析」+ Link 至 `/pricing`
  - 付費用戶 / 管理者：維持原 AI 摘要渲染

**對齊規格**：Feature 06 L規定。

---

### 3. 🟡 `/edu-console` — 空態匯入按鈕 DPA 攔截修復

**問題**：DPA 已簽署但學員清單空時，缺明確「邀請第一位學員」CTA；
且空態的匯入按鈕直接呼叫 `setImportModalOpen(true)` 跳過 DPA 檢查。

**修復**：
- 檔案：`frontend/app/edu-console/page.tsx`
- 空態匯入按鈕改用 `handleImportClick`（會自動攔截未簽 DPA 的情況）
- 按鈕文字改為「邀請第一位學員」，更符合空態語境

---

### 4. 🟡 `/account/weekly-reports` — 確認為誤報

**問題**：TODO 記錄「reports.length === 0 時靜默空白，無尚無週報說明文字」。

**實際狀況**：`page.tsx` lines 82-89 已有完整空態 UI：
- Calendar icon
- 「尚無週報」標題
- 「活躍用戶（每週至少做 1 份測驗）會在週日自動收到報告」說明文字

**結論**：誤報，標記為已完成。

---

## 驗證

- TypeScript 編譯零錯誤（`npx tsc --noEmit`）
- 無新增外部依賴

---

## 剩餘未處理項目（11 項）

### 🔴 Feature 缺失（6 項）
- `/exam/workspace` — 番茄鐘 Scenario 無對應前端觸發路徑
- `/exam/workspace` + `/practice` — AI inference 判斷按鈕無 Feature Scenario
- `/dashboard` — 模式 tooltip 說明按鈕無 Feature Scenario
- `/dashboard` — 儀表板無科目時 modal 路徑無 Feature 覆蓋
- `/knowledge` — 分享知識節點無 Scenario 且未實作
- `/account/weekly-reports` — Feature 14 未覆蓋 reports 空態情境

### 🟠 實作缺失（3 項）
- `/exam/workspace` — 番茄鐘互動 UI 缺失（啟用開關、時長設定、選擇按鈕）
- `/knowledge` — 資源面板摺疊按鈕
- `/knowledge` — Confetti/獎章動畫

### 🟡 空態補強（2 項）
- `/dashboard` — 上傳失敗未查 resource_parse_jobs.failure_reason
- `/knowledge` — PROCESSING 狀態未向使用者說明
