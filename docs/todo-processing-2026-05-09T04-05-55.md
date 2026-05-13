# TiTi Commander 排程巡檢紀錄 — 2026-05-09

> **觸發方式**：排程任務 `check-todo`（自動執行）
> **執行時間**：2026-05-09 04:05 UTC+8
> **巡檢範圍**：`docs/ToDoList.md` 所有未完成待辦項目

---

## 巡檢摘要

| 項目 | 狀態 | 處理結果 |
|------|------|----------|
| `/super-admin/settings/*` isSuperAdmin 守衛 | ✅ 確認已修復 | 誤報 — settings/layout.tsx 已於 2026-05-03 使用 isSuperAdmin |
| `/dashboard` 信心度校準趨勢 UI | ✅ 已修復 | 新增完整信心度校準趨勢區塊 |

---

## 詳細處理紀錄

### 1. `/super-admin/settings/*` — isSuperAdmin 守衛（確認已修復）

**待辦描述**：高等設定頁使用 `isAdmin` 守衛，依權限模型應改為 `isSuperAdmin`

**巡檢結果**：此條目為 Daily QA Audit 誤報。

- `frontend/app/super-admin/settings/layout.tsx` (L43-52) 已使用 `isSuperAdmin` 守衛
- `frontend/app/super-admin/layout.tsx` (L69-89) 使用 `isAdmin` 守衛（此為正確行為 — 一般管理後台允許 ADMIN + SUPER_ADMIN）
- Feature 12c (L287-300) 已有 Rule「前置（守衛）- 高等設定頁僅 SUPER_ADMIN 可進入」+ 2 個 Example Scenario
- 落地紀錄標示 2026-05-03 完成

**處理**：在 ToDoList.md 標記為已完成（誤報）。

---

### 2. `/dashboard` — 信心度校準趨勢 UI（Feature 20 修復）

**待辦描述**：Feature 20 Rule「儀表板應顯示信心度校準趨勢」要求，但儀表板無任何信心度趨勢 UI 區塊

**修復內容**：

#### 後端確認（已存在，無需修改）
- `GET /api/v1/dashboard/confidence-calibration` — 回傳近 5 場測驗的校準率趨勢
- 回應格式：`{ calibration_rate, status, trend: [{exam_id, submitted_at, calibration_rate}], exam_count }`

#### 前端修改

**`frontend/lib/api/services.ts`**：
- 新增 `dashboardService.getConfidenceCalibration()` 方法

**`frontend/app/dashboard/page.tsx`**：
- 新增 `calibration` state（型別：`{calibration_rate, status, trend[], exam_count} | null`）
- Dashboard 載入時同步呼叫 `getConfidenceCalibration()`
- 右側欄新增「信心度校準趨勢」區塊（`data-testid="confidence-calibration-trend"`）：
  - 校準率百分比大字 + 狀態標籤（校準良好=綠 / 需要改善=琥珀 / 偏差較大=玫瑰）
  - SVG 趨勢折線圖（emerald 色折線 + 圓點 + 80% 虛線參考線）
  - 各點百分比標籤
  - 底部說明文字「近 N 場測驗中，你標記『確定』且答對的比例」
  - 僅在有測驗資料時顯示（`exam_count > 0`）

#### 品質驗證
- TypeScript 編譯零錯誤（`npx tsc --noEmit` 通過）
- Feature 20 L104-111 Scenario 覆蓋：
  - ✅ 顯示「信心校準率」指標
  - ✅ 顯示近 5 場測驗的校準率趨勢折線圖
  - ✅ 校準率超過 80% 時標示為「校準良好」

---

## 未處理項目（本次巡檢識別但未修復）

以下項目仍為未完成狀態，需後續排程或人工處理：

### 🔴 高優先
| 項目 | 首見日期 | 原因 |
|------|----------|------|
| `/invite/setup-password` EDU 邀請流程 | 2026-05-09 | 前端已完成但後端 API 缺失（需新增 token 驗證 + 密碼設定 endpoint），工程量大 |
| `/exam/results` Certi 情感表情 UI | 2026-05-08 | 需設計決策（靜態圖片 vs 動態 Lottie），非排程可自主處理 |

### 🔴 中優先
| 項目 | 首見日期 | 原因 |
|------|----------|------|
| `/exam/workspace` 番茄鐘互動 UI | 2026-05-06 | Feature 21 三個 Scenario 需完整 UI 實作 |
| `/exam/workspace` + `/practice` AI inference 按鈕 Feature 覆蓋 | 2026-05-06 | 需新增 Feature Scenario |
| `/dashboard` 模式 tooltip / 無科目 modal | 2026-05-06 | 需新增 Feature Scenario |
| `/knowledge` 分享節點 / 摺疊按鈕 / 獎章動畫 | 2026-05-06 | 多個小缺失 |

### 🟡 次要
| 項目 | 首見日期 | 原因 |
|------|----------|------|
| `/exam/setup` 空態查 parse job | 2026-05-07 | Layer 3 標準未達 |
| `/dashboard` 上傳失敗查 job 表 | 2026-05-06 | Layer 3 標準未達 |
| `/knowledge` PROCESSING 狀態區分 | 2026-05-06 | 三態區分 UI |

---

## 變更檔案清單

| 檔案 | 變更類型 |
|------|----------|
| `frontend/lib/api/services.ts` | 新增 `getConfidenceCalibration` 方法 |
| `frontend/app/dashboard/page.tsx` | 新增信心度校準趨勢 state + UI 區塊 |
| `docs/ToDoList.md` | 標記 2 項完成、更新最後更新時間 |
| `docs/todo-processing-2026-05-09T04-05-55.md` | 本紀錄檔（新增） |

---

## Git Push 狀態

⚠️ **未完成**：`.git/index.lock` 為前次 session 遺留的 stale lock，sandbox 環境無法刪除。

**需手動執行**：
```bash
cd ~/certimate/project
rm -f .git/index.lock .git/index.lock.bak
git add docs/ToDoList.md frontend/app/dashboard/page.tsx frontend/lib/api/services.ts docs/todo-processing-2026-05-09T04-05-55.md
git commit -m "feat(dashboard): 新增信心度校準趨勢區塊 (Feature 20) — TiTi Commander 排程巡檢 2026-05-09"
git push
```
