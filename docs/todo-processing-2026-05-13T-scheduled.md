# ToDoList 排程巡檢處理紀錄 — 2026-05-13

> **觸發方式**：TiTi Commander 排程任務（check-todo）
> **執行時間**：2026-05-13
> **處理項目數**：3 項（全部完成）

---

## 巡檢結果摘要

| # | 類別 | 頁面 | 問題 | 狀態 |
|---|------|------|------|------|
| 1 | 🔴 Feature 缺失 | `/today` | 整頁無對應 Feature File | ✅ 已建立 42-今日學習首頁.feature |
| 2 | 🟠 實作缺失 | `/today` | `scaffold_due_count` 未消費 | ✅ 已修復 |
| 3 | 🟡 Layer 3 違規 | `/today` | 空態未查 Job 表 | ✅ 已修復 |

---

## 詳細處理紀錄

### 1. 🔴 Feature 缺失 — `/today` 無對應 Feature File

**問題**：`/today` 路由（Sprint 3 T30 學習首頁）承載三件事卡片，但 `project/features/` 內無任何 Feature 檔案覆蓋此頁。

**處理**：
- 新建 `project/features/42-今日學習首頁.feature`
- 編號選用 42（38-41 已被佔用）
- 標記 `@frontend @fullstack`
- 覆蓋 14 個 Example Scenario：
  - Greeting 與 Meta（3 個：問候語、距考/streak、無考試日期）
  - 三件事卡片有資料（4 個：繼續讀、複習錯題、Sprint 模擬、距考緊急建議）
  - 鷹架到期提示（2 個：有到期/無到期）
  - 空態渲染（2 個：繼續讀空態、複習空態）
  - Layer 3 空態查 Job 表（3 個：繼續讀偵測 FAILED、複習偵測 FAILED、無 FAILED 不顯示）
  - 快速連結（1 個）

**時間戳**：2026-05-13

---

### 2. 🟠 實作缺失 — `scaffold_due_count` 未消費

**問題**：`/dashboard/today` API 回傳 `scaffold_due_count`（SM-2 鷹架到期數），`TodaySnapshot` 型別已宣告但 JSX 完全未渲染此值。

**處理**：
- **有複習題目時**：複習卡片下方新增紫色提示文字 `📚 另有 N 個學習鷹架到期，建議一併複習`
- **複習空態時**：新增紫色連結 `📚 N 個學習鷹架到期 →`（連結至 /knowledge）
- `scaffoldDueCount === 0` 時兩處皆不顯示（條件渲染）

**修改檔案**：`frontend/app/today/page.tsx`
**時間戳**：2026-05-13

---

### 3. 🟡 Layer 3 違規 — 空態未查 Job 表

**問題**：「繼續讀」空態與「複習錯題」空態均顯示靜態說明文字，未呼叫 `resourceParseService.getStatus()` 查詢是否有 FAILED 資源。

**處理**：
- 新增 `parseJobFailures` state（`Array<{ title: string; reason: string }>`）
- 新增 `useEffect`：snapshot 載入後若有空態（`!snapshot.resume || reviewCount === 0`），自動查 `documentService.list()` 過濾 `status === 'FAILED'` 文件，逐個呼叫 `resourceParseService.getStatus()` 取得 `failure_reason`
- 「繼續讀」空態區塊新增紅色警示卡（`data-testid="resume-empty-parse-failures"`）
- 「複習錯題」空態區塊新增紅色警示卡（`data-testid="review-empty-parse-failures"`）
- 每處最多顯示 3 個失敗原因，超過則顯示「…另 N 個」
- 引入 `AlertTriangle` icon（lucide-react）

**修改檔案**：`frontend/app/today/page.tsx`
**時間戳**：2026-05-13

---

## 品質驗證

| 項目 | 結果 |
|------|------|
| TypeScript 編譯（`npx tsc --noEmit`） | ✅ 零錯誤 |
| Layer 3 模式對齊 | ✅ 與 /practice、/knowledge、/exam/setup 等頁面一致 |
| Feature File 格式 | ✅ Gherkin 語法、繁體中文、Background + Rule + Example 結構 |

---

## 未處理的既有待辦（非本次範圍）

以下項目為 2026-05-08 及更早的 unchecked 待辦，本次巡檢未處理：

1. `/exam/results` — Feature 06 Certi 情感表情 UI（L31）
2. `/exam/workspace` + `/practice` — AI inference 判斷按鈕無 Feature Scenario（L47）
3. `/dashboard` — 模式 tooltip 說明按鈕無 Feature Scenario（L48）
4. `/dashboard` — 行內加科目 modal 路徑無 Feature Scenario（L49）
5. `/knowledge` — 分享知識節點無 Scenario 且未實作（L50）
6. `/account/weekly-reports` — Feature 14 空態 UI 情境未覆蓋（L52）
7. `/knowledge` — Confetti 動畫未實作（L62）
8. 待補稽核：super-admin 高等設定頁 `isSuperAdmin` 守衛 audit（L27）
