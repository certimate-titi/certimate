# ToDoList 定期巡檢報告

**執行時間**：2026-05-01 20:03 (TiTi Commander 自動排程)
**執行者**：TiTi Commander — CEO 角色自動巡檢
**來源**：`docs/ToDoList.md`

---

## 巡檢摘要

| 類別 | 總數 | 本次解決 | 本次確認仍開放 | 新發現 |
|------|------|----------|----------------|--------|
| 🔴 Feature 缺失 | 6 | 1 | 5 | 0 |
| 🟠 實作缺失 | 8 | 0 | 8 | 0 |
| 🟡 空態補強 | 6 | 0 | 6 | 0 |
| **合計** | **20** | **1** | **19** | **0** |

---

## 本次解決項目

### ✅ `/pricing` — PRO_PLUS_399「進階 AI 教練」顯示 false（誤報關閉）

**原報告**：PRO_PLUS_399 方案功能矩陣「進階 AI 教練」顯示 false，與 Feature 03 明定可使用完整 AI 教練相違背。

**巡檢結果**：
- `frontend/app/pricing/page.tsx` line 71 確認 PRO_PLUS_399 的 `進階 AI 教練` 為 `included: false`
- Feature 07（`07-錯題複習與AI教練.feature`）L151-153 明確規定：「非 ULTRA 用戶請求進階 AI 教練失敗」，回傳錯誤「進階 AI 教練為 ULTRA 方案專屬功能」
- PRO_PLUS_399 享有基礎 AI 教練（100 次/月、max_tokens 2048），但**進階 AI 教練為 ULTRA_1599 專屬**
- 原報告誤將 Feature 03（基礎 AI 教練互動）與 Feature 07（進階 AI 教練權限）混淆

**決議**：定價頁顯示正確，標記為已解決。

---

## 確認仍開放項目（逐項驗證結果）

### 🔴 Feature 缺失（5 項仍開放）

#### 1. `/dashboard` — StudyBuddyBanner（ULTRA 共讀橫幅）無 Feature 覆蓋
- **狀態**：仍開放
- **優先級**：P2（低風險，純展示性 UI）

#### 2. `/exam/workspace` — Feature 05 AI 打氣語句（Certi）無 UI 實作
- **狀態**：確認仍缺失
- **驗證**：`frontend/app/exam/workspace/page.tsx`（467 行）無任何「打氣」「Certi」「motivational」相關程式碼
- **優先級**：P2

#### 3. `/knowledge/mindmap` — 節點點擊互動行為無 Feature Scenario
- **狀態**：仍開放
- **優先級**：P2

#### 4. `/exam/results` — Feature 06 LinkedIn 分享/下載成績卡片 placeholder vs 已實作
- **狀態**：仍開放（Feature Scenario 需更新以反映已實作狀態）
- **優先級**：P1（防回歸測試誤判）

#### 5. `/account` — 通知偏好規格與實作不同步
- **狀態**：確認不同步
- **驗證**：前端使用 localStorage（`certimate_notif_daily` 等），後端 `update_notification_preferences` API 存在但未被呼叫
- **優先級**：P1（功能不完整）

### 🟠 實作缺失（8 項仍開放）

#### 1. `/super-admin/anomaly` — Feature 16 批次修復缺 UI
- **狀態**：仍開放
- **優先級**：P2

#### 2. `/knowledge` — 「+ 新增資源」按鈕導向 `/dashboard` 而非開啟上傳 modal
- **狀態**：仍開放
- **優先級**：P2

#### 3. `/exam/workspace` — Feature 20 信心度校準 emoji UI（😰😐😎）缺失
- **狀態**：確認缺失
- **驗證**：`page.tsx` 無任何 emoji 信心度按鈕或 confidence_level state
- **優先級**：P1（Feature 20 核心 UI）

#### 4. `/practice` — Feature 20 信心度校準 emoji UI（😰😐😎）缺失
- **狀態**：確認缺失
- **驗證**：`page.tsx` L611 僅顯示 AI 推論信心度百分比（唯讀），非使用者自評 emoji 選擇器
- **優先級**：P1（Feature 20 核心 UI）

#### 5. `/exam/setup` — 進階出題配方面板 `isAdmin` 守衛應為 `isUltra`
- **狀態**：確認 bug
- **驗證**：`page.tsx` L64 destructure `isAdmin`，L699 以 `{isAdmin && (...)}` 守衛。無 `isUltra` 參考
- **優先級**：**P0**（ULTRA 付費用戶無法存取已付費功能）

#### 6. `/exam/setup` — SSE 即時進度 vs 模擬假動畫
- **狀態**：確認未實作 SSE
- **驗證**：L22 import `ExamLoadingOverlay`，L360 為 plain async/await，L425-428 為 hardcoded `LOADING_STAGES` 假動畫。無 EventSource 或 streaming 邏輯
- **優先級**：P2（功能可用但體驗不佳）

#### 7. `/account` — 通知偏好需改後端 API 儲存
- **狀態**：確認需修改
- **驗證**：前端 localStorage 三個 key（`certimate_notif_daily/preexam/weekly`），後端 API 已存在但前端未呼叫
- **優先級**：P1

#### 8. `/exam/workspace` — Feature 05 AI 打氣語句 UI 缺失（與 🔴 #2 同一問題）
- **狀態**：確認缺失（重複條目，建議合併）

### 🟡 空態補強（6 項仍開放，全部違反 Layer 3 規則）

| # | 頁面 | 查詢 job 表 | 說明 |
|---|------|------------|------|
| 1 | `/practice` | ❌ | no-questions 空態僅文字提示，未查 `resource_parse_jobs` |
| 2 | `/review` | ❌ | `wrongQuestions.length === 0` 顯示靜態「全部答對！」，未查 `exam_generation_jobs` |
| 3 | `/schedule` | ❌ | `recs.length === 0` 顯示靜態「尚無備考科目」，未查 job 表 |
| 4 | `/account/weekly-reports` | ❌ | `reports.length === 0` 顯示靜態說明，未自動查 cron job 失敗記錄 |
| 5 | `/knowledge/mindmap` | ❌ | `mindMapNodes.length === 0` 顯示靜態「上傳教材後自動生成」，未查 `resource_parse_jobs` |
| 6 | `/knowledge` | ⚠️ 部分 | FAILED 文件時會查 `resource_parse_jobs`，但 `documents.length === 0` 時不查 |

---

## CEO 建議行動清單（按優先級排序）

| # | 優先級 | 行動項 | 負責角色 | 影響 |
|---|--------|--------|----------|------|
| 1 | **P0** | `/exam/setup` isAdmin → isUltra 守衛修正 | 前端工程師 | ULTRA 付費用戶無法使用 Bloom 配方 |
| 2 | P1 | `/exam/workspace` + `/practice` Feature 20 信心度 emoji UI | 前端工程師 | Feature 20 核心互動缺失 |
| 3 | P1 | `/account` 通知偏好改用後端 API | 前端工程師 | 跨裝置設定不同步 |
| 4 | P1 | `/exam/results` Feature 06 Scenario 更新（已實作狀態） | 測試工程師 | 回歸測試誤判風險 |
| 5 | P2 | 6 個 Layer 3 空態違規修正 | 前端工程師 | 違反 QA 三層驗收規則 |
| 6 | P2 | `/exam/setup` SSE 即時進度 | 前端+後端工程師 | UX 改善 |
| 7 | P2 | 其餘 Feature 缺失補 Scenario | 測試工程師 | 回歸保護 |

---

## 備註

- ToDoList 中 `/exam/workspace` Feature 05 打氣語句重複出現兩次（line 36 與 line 38），建議合併
- `/pricing` 誤報已關閉，原因為 Feature 03（基礎 AI 教練）與 Feature 07（進階 AI 教練權限層級）規格範圍混淆
- 下次巡檢建議重點：P0 isAdmin→isUltra 修正是否完成
