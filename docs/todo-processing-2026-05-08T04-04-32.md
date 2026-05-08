# TiTi Commander 排程巡檢紀錄 — 2026-05-08T04:04:32

> **觸發方式**：Scheduled Task `check-todo`
> **執行角色**：TiTi Commander (CEO → 前端工程師 → QA 自檢)

---

## 巡檢摘要

掃描 `docs/ToDoList.md` 待辦事項，本次處理 **2 項**：

| # | 項目 | 分類 | 狀態 |
|---|------|------|------|
| 1 | `/account` dark mode 全站 CSS 效果 | 🟠 實作缺失 (2026-05-08) | ✅ 已修復 |
| 2 | `/exam/workspace` 題號網格信心度底色 | 🔴 Feature 缺失 (2026-05-08) | ✅ 已修復 |

---

## 修復詳情

### 1. Dark Mode 全站 CSS 效果

**問題**：`/account` 頁面 `darkMode` state 與 toggle UI 已存在，但切換後全站無視覺變化——`globals.css` 缺少 `.dark` class 下的 CSS 覆寫規則。

**修復內容**：

#### `frontend/app/globals.css`
- 新增 `:root` 亮色 CSS 變數（`--color-bg-primary` / `--color-text-primary` 等 16 組）
- 新增 `.dark` 暗色 CSS 變數覆寫（slate-900/800/700 色調）
- 新增 `.dark` 全局覆寫規則：
  - `.dark body` — 背景 + 文字
  - `.dark .bg-white` — 卡片/面板 → slate-800
  - `.dark .bg-slate-50/100` — 背景層級
  - `.dark .text-slate-*` — 全系列文字色覆寫
  - `.dark .border-slate-*` — 邊框色覆寫
  - `.dark input/textarea/select` — 輸入框
  - `.dark nav` — 導覽列
  - `.dark [role="dialog"]/[role="menu"]` — 彈窗/選單
  - `.dark hover:bg-slate-*:hover` — hover 效果
  - `.dark ::placeholder` — placeholder 文字
  - `.dark ::-webkit-scrollbar*` — scrollbar 樣式
  - `.dark .bg-slate-50\/50` — 半透明背景

#### `frontend/app/layout.tsx`
- 新增 FOUC 防護 inline script：在 `<head>` 中以 `dangerouslySetInnerHTML` 注入 dark mode 初始化腳本
- 在 hydration 前讀取 `localStorage('certimate_dark_mode')` 並套用 `.dark` class 到 `<html>`
- `suppressHydrationWarning` 移至 `<html>` 層級（涵蓋 class 變動）

**驗證**：
- TypeScript 編譯零錯誤（`npx tsc --noEmit`）
- 切換流程：`/account` → 點擊深色模式 toggle → `document.documentElement.classList.add('dark')` → 全站 CSS 變數切換 → 視覺主題變更

---

### 2. 題號導覽網格信心度底色

**問題**：Feature 20 Rule「後置（回應）- 題號導覽網格應以不同底色標示信心度」要求網格格子依信心度上色，但目前僅有 answered/unanswered/marked/current 四種狀態色。

**修復內容**：

#### `frontend/app/exam/workspace/page.tsx`

**網格按鈕邏輯（L301-315）**：
- 讀取 `confidences[q.id]` 信心度值
- 已作答 + `confident`（😎 非常確定）→ `bg-emerald-500`（綠色，與原已作答相同）
- 已作答 + `somewhat`（😐 有點把握）→ `bg-amber-400`（琥珀色）
- 已作答 + `guessing`（😰 完全猜測）→ `bg-rose-400`（玫瑰色）
- 已作答但未選信心度 → 維持 `bg-emerald-500`（向下相容）
- 優先級保持：current > marked > confidence-colored answered > unanswered

**圖例更新（L327-334）**：
- 原「已作答」單一圖例 → 拆為三個信心度圖例（😎/😐/😰 + 對應色塊）
- 新增圖例：「😎 非常確定」綠 / 「😐 有點把握」琥珀 / 「😰 完全猜測」玫瑰

**驗證**：
- TypeScript 編譯零錯誤
- `confidences` state 已於 L59 定義，`confidence-selector` UI 已於 L394-420 實作

---

## 未處理項目（下次巡檢）

以下項目因複雜度較高或需後端配合，本次未處理：

| 項目 | 原因 |
|------|------|
| `/exam/results` Certi 安撫表情 | 需設計 Certi mascot 情感 UI 資源（非純程式碼修復） |
| `/dashboard` 信心度趨勢 | 需後端新增趨勢 API endpoint + 前端圖表元件 |
| `/exam/workspace` 番茄鐘啟用開關 (2026-05-06) | 需 UI/UX 設計確認互動規格 |
| 其他 2026-05-06 項目 | 依優先級排隊 |

---

## 檔案變更清單

| 檔案 | 變更類型 | 說明 |
|------|----------|------|
| `frontend/app/globals.css` | 修改 | 新增 Dark Mode CSS 變數 + 全局覆寫規則 |
| `frontend/app/layout.tsx` | 修改 | 新增 FOUC 防護 dark mode 初始化 script |
| `frontend/app/exam/workspace/page.tsx` | 修改 | 題號網格信心度底色 + 圖例更新 |
| `docs/todo-processing-2026-05-08T04-04-32.md` | 新增 | 本紀錄檔 |
