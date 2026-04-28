# ToDoList 自動巡檢紀錄 — 2026-04-29T20:02:03

## 巡檢範圍

檢查 `docs/ToDoList.md` 所有未完成（`- [ ]`）項目，進行驗證、修復與狀態更新。

---

## 巡檢結果摘要

| # | 項目 | 操作 | 結果 |
|---|------|------|------|
| 1 | `/knowledge/mindmap` ForceGraph/MindMapTree 視圖切換 | 驗證 Feature 03b | ✅ 已有 3 個 Example (L231-252)，標記完成 |
| 2 | `/super-admin/settings/version` 版本資訊頁 Feature 覆蓋 | 驗證 Feature 12c | ✅ Rule (L260) + Example (L265-269)，標記完成 |
| 3 | `/library` Tab 切換 | 驗證頁面是否存在 | ✅ 頁面不存在（已於空態區確認），標記為過時參照 |
| 4 | `/exam/results` 逐題解析入口 | 驗證 page.tsx | ✅ L240 已有 Link `/review?examId=&all=1`，標記完成 |
| 5 | `/verify-email/sent` resend silent fail | 程式碼修復 | ✅ 已修復（詳見下方） |
| 6 | `/resources/[id]/candidates` 前端頁面 | 驗證頁面是否存在 | ⚠️ Feature 23 有 spec 但前端頁面未建立，更新說明 |

---

## 修復詳情

### `/verify-email/sent` — resend 重寄失敗 silent fail 修復

**問題**：`handleResend()` 的 `catch {}` block 為空，使用者重寄失敗時無任何錯誤提示。

**修復內容**（`frontend/app/verify-email/sent/page.tsx`）：

1. 新增 `resendError` state（`useState('')`）
2. `catch` block 改為：
   - 重設 `cooldown` 為 0（讓使用者可立即重試）
   - 設定 `setResendError('驗證信寄送失敗，請稍後再試。')`
3. 重寄開始時清除先前錯誤（`setResendError('')`）
4. UI 新增紅色錯誤提示框（`bg-red-50 text-red-700`），與成功提示框風格一致

**驗證**：TypeScript 編譯零錯誤（`npx tsc --noEmit` 通過）

---

## 仍待處理的未完成項目

### 🔴 Feature 缺失
- `/dashboard` — 備考模式標籤 Sprint/Standard/Mastery 無 Feature 覆蓋（前端程式碼 L363-365 已實作三種模式切換邏輯）
- `/exam/results` — 成績卡片下載按鈕無 Feature Scenario（功能為 stub）
- `/exam/workspace` — Feature 05 AI 打氣語句 Certi 介面，頁面無對應 UI 實作（兩條重複項）
- `/dashboard` — StudyBuddyBanner（ULTRA 共讀橫幅）無 Feature 覆蓋
- `/super-admin/platform-subjects` — 平台科目管理無 Feature 覆蓋
- `/resources/[id]/candidates` — Feature 23 有 spec 但前端頁面未建立

### 🟠 實作缺失
- `/exam/results` — 成績卡片下載功能為 alert stub
- `/super-admin/anomaly` — Feature 16「批次修復」UI 缺失
- `/review` — KaTeX 渲染是否由 MathContent 實際執行待確認
- `/knowledge` — 「+ 新增資源」按鈕導向 `/dashboard` 而非上傳 modal

### 🟡 空態補強
- `/practice` — no-questions 空態未查 resource_parse_jobs
- `/review` — wrongQuestions 空態未查 job 表，違反 Layer 3
- `/schedule` — recs 空態未查 job 表，違反 Layer 3

### 其他
- GCP Billing Export — 待部署 Cloud Run 環境變數 + Service Account key

---

## 本次變更檔案

1. `frontend/app/verify-email/sent/page.tsx` — 修復 resend silent fail
2. `docs/ToDoList.md` — 更新 5 項狀態（4 項標記完成、1 項補充說明）
3. `docs/todo-processing-2026-04-29T20-02-03.md` — 本紀錄檔
