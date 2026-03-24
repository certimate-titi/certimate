---
name: aibdd.auto.frontend.nextjs-pages
description: >
  前端 Next.js 頁面實作。基於已完成的 Walking Skeleton（Firebase + services.ts mock）和
  UI/UX consultant 產出的 layout.html 靜態原型，將靜態頁面轉換為動態 Next.js React 元件。
  當使用者要求實作前端頁面、將 layout.html 轉為 Next.js、或在已有 mock services 的前端專案中
  開發功能頁面時，使用此 skill。需要 specs 目錄下的 activities 或 features 作為規格參考。
  可搭配 /aibdd.auto.frontend.msw-api-layer 所產生的型別與 mock services。
---

# Next.js 頁面實作器

將靜態 HTML 原型 + 規格文件轉換為動態 Next.js 頁面。

**前提假設**：
- Walking Skeleton 已由 `/aibdd.auto.frontend.apifirst.msw.starter` 初始化完成
- 型別與 mock services 已由 `/aibdd.auto.frontend.msw-api-layer` 產生完成
- API service 函式（`lib/api/services.ts`）和 TypeScript 型別（`types/`）已就位

```
1. 參數載入        — 從 arguments.yml 讀取路徑配置
2. 規格校驗        — 確認 activities 或 features 至少擇一存在
3. 盤點頁面        — 從規格推導需要實作的頁面清單
4. 元件拆解        — 將 layout.html 拆解為 React 元件樹
5. 逐頁實作        — 將靜態 HTML 轉為動態 Next.js 頁面
6. 整合驗證        — 確保頁面間導航與資料流正確
```

## Phase 0：參數載入

從 `${SPECS_HOME}/arguments.yml` 讀取路徑配置：

| 參數 | 用途 | 範例值 |
|------|------|--------|
| `PROJECT_ROOT` | 前端專案根目錄 | `frontend/` |
| `SPECS_HOME` | 規格文件目錄 | `specs/` |
| `TYPES_DIR` | TypeScript 型別目錄 | `types` |
| `API_DIR` | API 服務層目錄 | `lib/api` |

額外掃描的路徑（非參數，固定慣例）：

| 路徑 | 用途 |
|------|------|
| `${SPECS_HOME}/activities/*.activity` | Activity Diagram，推導頁面流程 |
| `${SPECS_HOME}/features/**/*.feature` | Feature Files，推導頁面功能細節 |
| `${SPECS_HOME}/activities/*.testplan.md` | 測試計畫（Optional），供驗證參考 |
| `${PROJECT_ROOT}/layout.html` 或 `${SPECS_HOME}/*.layout.html` | UI/UX 靜態原型 |

## Phase 1：規格校驗

**必要條件**：`activities/` 或 `features/` 至少擇一存在。

```
掃描 ${SPECS_HOME}/activities/*.activity
掃描 ${SPECS_HOME}/features/**/*.feature

存在任一？
  ├─ 是 → 繼續 Phase 2
  └─ 否 → 中斷
         ├─ 預設：輸出錯誤訊息，請使用者提供 .activity 或 .feature 檔案
         └─ 使用者強行要求 → 根據 layout.html 的頁面結構腦補基礎規格
```

校驗細節見 [references/spec-validation.md](references/spec-validation.md)。

## Phase 2：盤點頁面

從規格文件推導需要實作的頁面清單。

### 從 Activity Diagram 推導

每個 `[STEP]` 綁定的 `.feature` 暗示一個使用者操作場景。
將相關操作歸類為頁面：

```
[STEP:1] {specs/features/exam/建立考試.feature}   → /exam/setup 頁面
[STEP:2] {specs/features/exam/作答考試.feature}   → /exam/workspace 頁面
[STEP:3] {specs/features/exam/查看成績.feature}   → /exam/results 頁面
```

### 從 Feature Files 推導

每個 `Feature:` 對應一個功能模組。按 CRUD 語意歸類：
- `查詢/清單` → List 頁面
- `新增/建立` → Create 表單（或 Modal）
- `編輯/更新` → Edit 表單
- `刪除` → Delete 確認（Modal 或 Popconfirm）
- `詳情/檢視` → Detail 頁面

### 產出：頁面清單

```
盤點結果：
1. /dashboard          — 學習總覽（每日任務、學習進度、成就）
2. /exam/setup         — 考試設定（科目、題型、題數選擇）
3. /exam/workspace     — 考試作答頁
4. /exam/results       — 考試成績頁（分析、錯題回顧）
5. /knowledge          — 知識圖譜（Mind Map）
6. /review             — 複習排程（間隔重複）
```

## Phase 3：元件拆解

將 `layout.html` 拆解為 React 元件樹。詳細策略見 [references/component-decomposition.md](references/component-decomposition.md)。

核心原則：

1. **視覺保真**：拆解後的元件渲染結果必須與原始 `layout.html` 視覺一致。不能「變醜」。
2. **CSS 遷移**：使用 TailwindCSS 4 classes + `cn()` 工具函式。
3. **語意化拆解**：按 UI 職責拆分（Navbar、Content、Card、Form、Modal）。
4. **共用元件提取**：多頁面重複出現的 UI 區塊提取為 `components/` 下的共用元件。

### 元件目錄結構

```
app/
├── layout.tsx                    ← Root Layout：AuthProvider + NavbarWrapper
├── page.tsx                      ← Landing Page
├── globals.css                   ← @import "tailwindcss"
├── error.tsx                     ← Error boundary
├── not-found.tsx                 ← 404 page
├── login/page.tsx
├── signup/page.tsx
├── dashboard/page.tsx
├── exam/
│   ├── setup/page.tsx
│   ├── workspace/page.tsx
│   └── results/page.tsx
├── knowledge/page.tsx
├── review/page.tsx
├── account/page.tsx
├── admin/page.tsx                ← B2B 機構管理
└── super-admin/                  ← 平台管理
    ├── page.tsx
    └── [子頁面]/page.tsx
components/
├── Navbar.tsx                    ← 主導航列
├── NavbarWrapper.tsx             ← 條件渲染 Navbar 的 wrapper
├── AchievementBadge.tsx          ← 成就徽章
├── AchievementGrid.tsx           ← 成就展示網格
├── Confetti.tsx                  ← 慶祝動畫
├── DailyQuestCard.tsx            ← 每日任務卡片
├── ExamLoadingOverlay.tsx        ← 考試載入遮罩
├── GrowthTimeline.tsx            ← 成長時間軸
├── StreakCounter.tsx              ← 學習連續天數
├── SubjectPickerModal.tsx         ← 科目選擇 Modal
├── SubjectSwitcher.tsx            ← 科目切換器
└── onboarding/                   ← Onboarding 流程元件
    ├── StepWelcome.tsx
    ├── StepPreferences.tsx
    └── StepConfirmation.tsx
```

## Phase 4：逐頁實作

對每個頁面，執行以下步驟。詳細模式見 [references/spec-driven-patterns.md](references/spec-driven-patterns.md)。

### 步驟 4A：讀取頁面規格

1. 找到該頁面對應的 `.feature` 檔案
2. 從 `Background:` data table 提取資料結構（→ 表格欄位、表單欄位）
3. 從 `When` 步驟提取使用者操作（→ 按鈕、表單提交、導航）
4. 從 `Then` 步驟提取預期回饋（→ Toast、redirect、UI 狀態變化）
5. 從 `Rule:` 提取驗證規則（→ 表單驗證、條件渲染）

### 步驟 4B：對接 API services

從 `lib/api/services.ts` 引入已有的 service 函式：

```typescript
// 已由 msw-api-layer 產生
import { getDashboard, getExamResults, createExam } from '@/lib/api/services'
import type { CreateExamRequest, GetDashboardResponse } from '@/types'
```

- **不要重新實作 API 呼叫**。直接使用 `services.ts` 中已有的函式。
- **不要重新定義型別**。直接使用 `types/` 下的 TypeScript interface。

### 步驟 4C：實作頁面元件

1. **所有頁面使用 `'use client'`**（因為 static export 模式，無 Server Components）
2. 從 `layout.html` 對應區塊提取 HTML 結構
3. 將靜態 HTML 轉為 React JSX
4. 用 `useState` / `useEffect` 實現動態行為
5. 從 service 函式獲取資料
6. 實作使用者操作的 handler（form submit、button click）
7. 加入 Loading / Empty / Error 狀態處理

### 步驟 4D：樣式實作

使用 TailwindCSS 4 classes，搭配專案已有的工具：

```typescript
import { cn } from '@/lib/utils'            // clsx + tailwind-merge
import { cva } from 'class-variance-authority' // 元件 variants
```

**樣式優先順序**：
1. **TailwindCSS classes**（主要）
2. **`cn()` 合併條件 class**（動態樣式）
3. **`cva()` 定義元件 variants**（Button、Badge 等多狀態元件）
4. **CSS 變數**（`globals.css` 中的 design tokens）

**禁止**：
- 不使用 `styled-components` 或 `emotion`
- 不使用固定的 inline style objects（除非是動態計算值如 `width: ${progress}%`）
- 不使用 CSS Modules

**圖示**：使用 `lucide-react`

```typescript
import { Search, Plus, Trash2 } from 'lucide-react'
```

**動畫**：使用 `motion` 函式庫

```typescript
import { motion, AnimatePresence } from 'motion/react'
```

**表單**：使用 `react-hook-form`

```typescript
import { useForm } from 'react-hook-form'
import type { CreateExamRequest } from '@/types'

const { register, handleSubmit, formState: { errors } } = useForm<CreateExamRequest>()
```

## Phase 5：整合驗證

完成所有頁面後，驗證整體：

1. **導航連貫性**：從 Activity Diagram 的 STEP 序列驗證頁面間跳轉
2. **資料流一致性**：頁面 A 建立的資料能在頁面 B 正確顯示
3. **狀態同步**：操作後清單即時更新
4. **錯誤處理**：API 錯誤正確顯示
5. **Auth 保護**：需登入頁面有 `useAuth()` guard
6. **Test Plan 對照**（若有）：每個測試步驟的預期結果可達成

## 注意事項

- **Mock Services 已就位**：開發階段所有 API 呼叫透過 `services.ts` 返回 mock 資料。不需要真實後端。
- **不修改 services 層**：不要修改 `lib/api/services.ts`。如需新 endpoint，回報給使用者或呼叫 `/aibdd.auto.frontend.msw-api-layer`。
- **視覺品質不能退化**：拆解後的 React 元件渲染結果必須與 layout.html 視覺一致或更好。
- **繁體中文產出**：所有 TODO 註解和文件使用繁體中文，但程式碼中的變數名和函式名使用英文。
- **靜態匯出**：因為 `output: 'export'`，不可使用 `getServerSideProps`、`next/headers`、`cookies()` 等 server-only API。
