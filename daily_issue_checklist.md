# CertiMate Daily QA Issue Checklist
**生成時間**：2026-05-13（自動巡檢 daily-qa-page-audit）
**巡檢範圍**：`frontend/app/**/*.tsx`（優先：dashboard, knowledge, exam/*, practice, review, today, account；次之：其餘頁面）vs `project/features/**/*.feature`

---

## 🔴 Feature 缺失 — 需補 Gherkin Scenario

### 🆕 NEW（2026-05-13）

| # | 頁面 | 問題 | 優先度 |
|---|------|------|--------|
| N1 | `/today` | **整頁無對應 Feature File**：`/today` 是 Sprint 3 以來的「學習首頁」，承載三件事（繼續讀/複習錯題/Sprint 模擬），但 `project/features/` 內無任何 Feature 檔案覆蓋此頁的 Scenario（含 greeting 顯示、三卡片渲染、streak/examDaysLeft 顯示、空態 fallback）。 | P1 |

### 既有未解（從 ToDoList.md 彙整，尚未 ✅）

| # | 頁面 | 問題 | 首見 |
|---|------|------|------|
| E1 | `/exam/results` | Feature 06 Scenario「Then 畫面應顯示 AI 教練（Certi）的陪伴與安撫表情」存在，但前端僅顯示靜態 AI 教練文字，非動態 Certi 情感表情 UI | 2026-05-08 |
| E2 | `/exam/workspace` + `/practice` | AI inference 判斷按鈕（EPIC-035：保留我的答案/採信AI/略過）已在兩頁實作，但無任何 Feature Scenario 覆蓋（Feature 32/04a 皆未涵蓋此 UI 互動） | 2026-05-06 |
| E3 | `/dashboard` | 模式 tooltip 說明按鈕（Sprint/Standard/Mastery 策略說明彈窗）無對應 Feature Scenario（Feature 09/13 皆未覆蓋此互動） | 2026-05-06 |
| E4 | `/dashboard` | 儀表板無科目時「開始選擇科目」dashboard-level modal 路徑，Feature 15 只覆蓋 /onboarding 流程，未涵蓋此行內加科目路徑 | 2026-05-06 |
| E5 | `/knowledge` | 「分享知識節點」Feature 03 提及節點分享，但無對應 Scenario 且前端未實作按鈕 | 2026-05-06 |
| E6 | `/account/weekly-reports` | Feature 14 未覆蓋「reports 為空」時應顯示的 UI 說明情境 | 2026-05-06 |

---

## 🟠 實作缺失 — 需補前端功能

### 🆕 NEW（2026-05-13）

| # | 頁面 | 問題 | 優先度 |
|---|------|------|--------|
| N2 | `/today` | **`scaffold_due_count` 未反映於 UI**：`/dashboard/today` endpoint 回傳 `scaffold_due_count`（P5 SM-2 鷹架到期數），`TodaySnapshot` 型別已含此欄位，但頁面 JSX 完全未使用此值（無顯示、無條件渲染、無任何卡片或 badge），造成 scaffold 到期資料靜默丟失。 | P2 |

### 既有未解（從 ToDoList.md 彙整，尚未 ✅）

| # | 頁面 | 問題 | 首見 |
|---|------|------|------|
| E7 | `/knowledge` | Feature 03 規格「AI 教練可能發送灑花恭喜獎章動畫（節點掌握時）」，頁面未實作 Confetti 或獎章動畫（僅 /exam/results 有 Confetti） | 2026-05-06 |

---

## 🟡 空態補強 — 需查 Job 表

### 🆕 NEW（2026-05-13）

| # | 頁面 | 問題 | 優先度 |
|---|------|------|--------|
| N3 | `/today` | **Layer 3 違規**：三件事卡片中「繼續讀」空態（`snapshot.resume === null`）以及「複習錯題」空態（`reviewCount === 0`）均僅顯示靜態說明文字，未呼叫 `resourceParseService.getStatus()` 查詢是否有 FAILED 資源（failure_reason）。根據 CLAUDE.md 規則：空態必須查 job 表，不可目視判定「合理的空」。 | P2 |

### 既有未解（確認 ToDoList.md 中無對應未解項）

*本次巡檢未發現其他新增 Layer 3 違規（priority pages 均已合規）。*

---

## ✅ 本次確認合規（priority pages）

| 頁面 | Layer 1 | Layer 2 | Layer 3 |
|------|---------|---------|---------|
| `/dashboard` | ✅ | ✅ | ✅ pollParseUntilDone() |
| `/knowledge` | ✅ | ✅ | ✅ FAILED doc 查詢 |
| `/knowledge/mindmap` | ✅ | ✅ | ✅ FAILED doc 查詢 |
| `/knowledge/wrong-answers` | ✅ | ✅ | ✅ FAILED doc 查詢 |
| `/exam/setup` | ✅ | ✅ | ✅ T62 batch 查詢 |
| `/exam/workspace` | ✅ | ✅ | N/A（exam 進行中） |
| `/exam/results` | ✅ | ✅ | N/A（exam 後靜態） |
| `/practice` | ✅ | ✅ | ✅ FAILED doc 查詢 |
| `/review` | ✅ | ✅ | ✅ getRecentFailures() |

---

## 📊 問題彙總

| 類型 | 既有未解 | 本次新增 | 合計 |
|------|---------|---------|------|
| 🔴 Feature 缺失 | 6 | 1 | **7** |
| 🟠 實作缺失 | 1 | 1 | **2** |
| 🟡 空態補強 | 0 | 1 | **1** |
| **合計** | **7** | **3** | **10** |

---

*本檔由 `daily-qa-page-audit` 自動任務生成，每日覆寫。如需歷史版本請查 git log。*
