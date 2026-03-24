# 元件拆解策略

## 目標

將 `layout.html` 靜態原型拆解為 React 元件樹，同時**保證視覺保真**。

## 拆解流程

```
1. 掃描 layout.html 結構 → 識別 UI 區塊
2. 分類 UI 區塊 → Shell / Page / Domain / Shared
3. 提取共用元件 → 跨頁面重複的區塊
4. 建立元件樹 → 確定 props 與資料流
5. 遷移樣式 → TailwindCSS 4 classes + cn()
```

## 步驟 1：識別 UI 區塊

掃描 `layout.html`，依 HTML 結構識別以下區塊類型：

| HTML 特徵 | UI 區塊類型 | 範例 |
|-----------|------------|------|
| `<nav>`, 頂部導航 | Navbar | 主導航列 |
| `<table>`, `<thead>`, `<tbody>` | DataTable | 資料清單表格 |
| `<form>`, `<input>`, `<select>` | Form | 新增 / 編輯表單 |
| `<dialog>`, `.modal`, overlay 結構 | Modal / Dialog | 確認刪除對話框 |
| `.card`, 獨立資訊區塊 | Card | 統計卡片、任務卡片 |
| `<button>`, `<a>` 操作區域 | ActionBar / Toolbar | 批次操作列 |
| 空狀態插圖 / Loading 動畫 | StateDisplay | Empty, Loading, Error |

## 步驟 2：分類元件層級

### Shell 層（`app/layout.tsx`）

全站共用的外殼結構：
- `AuthProvider`（Firebase Auth 狀態管理）
- `NavbarWrapper`（條件渲染 Navbar）
- `<main>` 內容區域

**判定規則**：所有頁面都出現的固定結構 → Shell 層。

### Page 層（`app/**/page.tsx`）

每個路由對應的頁面元件：
- **全部使用 `'use client'`**（static export 模式）
- 組合該頁面需要的元件
- 處理資料獲取（`useState` + `useEffect`）
- 傳遞 props 給子元件

### Domain 層（`components/` 根目錄或功能子目錄）

具有業務語意的複合元件：

```
DailyQuestCard      — 每日任務卡片
StreakCounter        — 學習連續天數
AchievementBadge     — 成就徽章
AchievementGrid      — 成就展示網格
SubjectSwitcher      — 科目切換器
SubjectPickerModal   — 科目選擇 Modal
ExamLoadingOverlay   — 考試載入遮罩
GrowthTimeline       — 成長時間軸
Confetti             — 慶祝動畫
```

**判定規則**：元件名稱含業務實體名詞 → Domain 層。

### 功能分組子目錄（`components/onboarding/` 等）

當一組元件屬於同一功能流程時，放入子目錄：

```
components/onboarding/
├── StepWelcome.tsx
├── StepPreferences.tsx
├── SubjectPicker.tsx
└── StepConfirmation.tsx
```

**判定規則**：3 個以上元件服務同一功能流程 → 建立子目錄。

## 步驟 3：提取共用元件

### 提取原則

```
出現 1 次 → 保留在 Page 層，不提取
出現 2 次 → 提取為 components/ 下的元件
出現 3+ 次 → 必須提取為共用元件
```

### 已有共用元件

以下元件已由 Walking Skeleton 提供，**不要重複建立**：

```
components/Navbar.tsx             — 主導航列
components/NavbarWrapper.tsx      — 條件渲染 Navbar
```

擴充已有元件時，保留原有 API，新增 props 而非修改。

## 步驟 4：建立元件樹

產出每個頁面的元件組成圖：

```
/dashboard（學習總覽頁）
├── app/layout.tsx
│   ├── AuthProvider
│   └── NavbarWrapper → Navbar
└── page.tsx（DashboardPage）
    ├── SubjectSwitcher
    ├── StreakCounter
    ├── DailyQuestCard
    ├── AchievementGrid
    │   └── AchievementBadge (×N)
    └── GrowthTimeline
```

### Props 設計原則

1. **資料向下**：父元件獲取資料，透過 props 傳給子元件
2. **事件向上**：子元件透過 callback props 通知父元件（`onSubmit`, `onDelete`）
3. **型別來自 types/**：props 的型別直接使用 `types/models.ts` 的 interface

```typescript
// Domain 元件的 props 範例
import type { DailyQuest } from '@/types'

interface DailyQuestCardProps {
  quest: DailyQuest
  onComplete: (questId: string) => void
  isLoading: boolean
}
```

## 步驟 5：樣式遷移

### 遷移策略

**1. TailwindCSS 4 classes（主要）**

```tsx
<button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
```

**2. `cn()` 合併條件 class**

```typescript
import { cn } from '@/lib/utils'

<div className={cn(
  "rounded-lg border p-4",
  isActive && "border-blue-500 bg-blue-50",
  isDisabled && "opacity-50 cursor-not-allowed"
)}>
```

**3. `cva()` 定義元件 variants**

```typescript
import { cva } from 'class-variance-authority'

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
  {
    variants: {
      variant: {
        default: "bg-slate-100 text-slate-800",
        success: "bg-green-100 text-green-800",
        danger: "bg-red-100 text-red-800",
      },
    },
    defaultVariants: { variant: "default" },
  }
)
```

**4. Design Tokens → CSS 變數（`globals.css`）**

```css
/* globals.css */
@import "tailwindcss";
```

### 禁止項目

- 不使用 `styled-components` 或 `emotion`
- 不使用固定的 inline style objects（`style={{ color: 'red' }}`）
- 不使用 CSS Modules
- 不使用全域 CSS class（除了 `globals.css` 中的 CSS 變數）

## 視覺保真驗證

拆解完成後，進行視覺對照：

1. 將 layout.html 在瀏覽器中開啟，截圖作為基準
2. 將拆解後的 React 頁面在 `npm run dev` 中開啟，截圖比對
3. 逐項檢查：字體、間距、對齊、圖示位置、互動狀態一致
4. 不一致的地方立即修正，不留到後續 Phase
