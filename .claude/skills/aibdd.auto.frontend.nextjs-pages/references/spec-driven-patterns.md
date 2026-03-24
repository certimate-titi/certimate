# 規格驅動開發模式

## 目標

從 Gherkin Feature Files 和 Activity Diagrams 中提取 UI 需求，
系統性地轉換為 React 頁面元件的具體實作。

## Feature File → UI 元素對照表

### Background Data Table → 資料結構

Feature 的 `Background:` 區塊定義了實體的資料欄位：

```gherkin
Background:
  Given 系統中存在以下考試:
    | exam_id | title       | type      | questionCount |
    | E001    | 證照模擬考   | MOCK_EXAM | 50            |
```

**轉換規則**：

| Data Table 欄位 | UI 元素 |
|----------------|---------|
| 所有欄位 | Table 的欄位定義 |
| 可編輯欄位（排除 id、系統自動生成欄位） | Form 的輸入欄位 |
| status / state / type 類欄位 | Badge 元件、篩選器選項 |
| 日期類欄位 | `date-fns` 格式化顯示 |

```typescript
// Data Table → Table columns 定義
import { format } from 'date-fns'

const columns = [
  { key: 'title', header: '考試名稱' },
  { key: 'type', header: '類型', render: (v: string) => <Badge>{v}</Badge> },
  { key: 'createdAt', header: '建立時間', render: (v: string) => format(new Date(v), 'yyyy/MM/dd') },
]
```

### When 步驟 → 使用者操作

Feature 的 `When` 步驟定義了使用者操作：

```gherkin
When 使用者以下列設定建立考試:
  | subject  | type      | questionCount |
  | 資訊安全  | MOCK_EXAM | 50            |
```

**轉換規則**：

| When 動詞 | UI 操作 | React 實作 |
|-----------|---------|-----------|
| 建立 / 新增 | 表單提交 | `react-hook-form` + `handleSubmit` |
| 查詢 / 搜尋 | 搜尋或篩選 | `useState` + filter |
| 編輯 / 更新 | 表單提交（預填值） | `useForm({ defaultValues })` |
| 刪除 | 確認刪除 | Modal 確認 + service 呼叫 |
| 上傳 | 檔案上傳 | `<input type="file">` + `apiClient.upload` |
| 激活 / 啟用 | 操作按鈕 | `<button onClick={handleActivate}>` |

### Then 步驟 → UI 回饋

Feature 的 `Then` 步驟定義了預期回饋：

```gherkin
Then 操作成功
And 回應中應包含以下考試資料:
  | title       | questionCount |
  | 證照模擬考   | 50            |
```

**轉換規則**：

| Then 描述 | UI 回饋 | React 實作 |
|-----------|---------|-----------|
| 操作成功 | 成功通知 / 頁面跳轉 | `router.push()` 或狀態更新 |
| 操作失敗 + 錯誤訊息 | 錯誤提示 | `try/catch` + 錯誤 state 顯示 |
| 回應中應包含 | 清單更新 / 資料展示 | 重新 fetch 或 optimistic update |
| 回應中不應包含 | 項目移除 | `setData(prev => prev.filter(...))` |

### Rule → 驗證邏輯

Feature 的 `Rule:` 區塊定義了業務規則：

```gherkin
Rule: 免費用戶每月最多建立 3 次模擬考
  Scenario: 超過用量限制
    When 使用者嘗試建立第 4 次模擬考
    Then 操作失敗
    And 錯誤訊息為「已達本月用量上限」
```

**轉換規則**：

| Rule 類型 | UI 實作 |
|-----------|---------|
| 必填欄位 | `react-hook-form` 的 `required` 規則 |
| 格式驗證 | `react-hook-form` 的 `pattern` 規則 |
| 用量限制 | 按鈕 disabled + Tooltip 說明 |
| 權限限制 | 條件渲染，隱藏或禁用元件 |
| 訂閱層級限制 | `useAuth()` 的 `isPro` / `isProPlus` 判斷 |

## Activity Diagram → 頁面導航

### STEP → 頁面路由

每個 `[STEP]` 對應一個使用者可見的頁面或操作：

```
[STEP:1] @使用者 {specs/features/exam/設定考試.feature}
→ /exam/setup 頁面

[STEP:2] @使用者 {specs/features/exam/作答考試.feature}
→ /exam/workspace 頁面
```

### DECISION → 條件渲染

Activity 的 `[DECISION]` 對應 UI 上的條件分支：

```
[DECISION:3a] 是否為 PRO 用戶
  [BRANCH:3a:是] → 顯示進階分析圖表
  [BRANCH:3a:否] → 顯示升級提示
```

**React 實作**：

```tsx
const { isPro } = useAuth()

{isPro ? (
  <AdvancedAnalytics data={examResults} />
) : (
  <UpgradePrompt feature="進階分析" />
)}
```

### STEP 序列 → 導航流程

Activity 的 STEP 順序暗示了頁面間的導航路徑：

```
STEP:1（設定考試）→ STEP:2（作答）→ STEP:3（查看成績）
```

**React 實作**：操作完成後自動導航到下一步：

```typescript
import { useRouter } from 'next/navigation'

async function handleCreateExam(data: CreateExamRequest) {
  const result = await createExam(data)
  router.push(`/exam/workspace?examId=${result.examId}`)
}
```

## 頁面類型模板

### 清單頁（List Page）

**觸發 Feature**：含「查詢」、「清單」語意的 Feature

```tsx
'use client'

import { useState, useEffect } from 'react'
import { getDashboard } from '@/lib/api/services'
import type { GetDashboardResponse } from '@/types'

export default function DashboardPage() {
  const [data, setData] = useState<GetDashboardResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    getDashboard().then(setData).finally(() => setIsLoading(false))
  }, [])

  if (isLoading) return <div className="flex items-center justify-center min-h-[50vh]">載入中...</div>
  if (!data) return <div className="text-center text-slate-500">無資料</div>

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      {/* 頁面內容 */}
    </div>
  )
}
```

### 表單頁（Form Page / Modal）

**觸發 Feature**：含「建立」、「設定」語意的 Feature

```tsx
'use client'

import { useForm } from 'react-hook-form'
import { useRouter } from 'next/navigation'
import { createExam } from '@/lib/api/services'
import type { CreateExamRequest } from '@/types'

export default function ExamSetupPage() {
  const router = useRouter()
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<CreateExamRequest>()

  async function onSubmit(data: CreateExamRequest) {
    try {
      const result = await createExam(data)
      router.push(`/exam/workspace?examId=${result.examId}`)
    } catch (error) {
      // 錯誤處理
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      {/* 表單欄位 */}
    </form>
  )
}
```

## 錯誤處理模式

### API 錯誤 → UI 回饋

```typescript
async function handleAction(data: SomeRequest) {
  try {
    await someService(data)
    // 成功：更新狀態或導航
  } catch (error) {
    if (error instanceof Error) {
      setErrorMessage(error.message)
    }
  }
}
```

### 狀態處理層級

每個頁面元件必須處理以下狀態：

| 狀態 | 觸發條件 | UI 顯示 |
|------|---------|---------|
| Loading | API 呼叫進行中 | 載入動畫或骨架屏 |
| Empty | API 返回空陣列 | 空狀態提示（文字 + 圖示） |
| Error | API 呼叫失敗 | 錯誤提示 + 重試按鈕 |
| Success | 資料正常載入 | 正常內容渲染 |

## 所有頁面皆為 Client Component

因為使用 `output: 'export'`（靜態匯出），所有頁面必須：

- 加上 `'use client'` 指令
- 使用 `useState` + `useEffect` 獲取資料（不能用 Server Components）
- 使用 `useRouter` from `next/navigation`（不是 `next/router`）
- 不使用 `getServerSideProps`、`next/headers`、`cookies()` 等 server-only API
