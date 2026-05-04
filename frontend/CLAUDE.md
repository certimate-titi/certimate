# CLAUDE.md — Frontend

## 快速啟動

```bash
cd frontend
npm install
npm run dev    # http://localhost:3005
```

需要後端運行於 `http://localhost:8000/api/v1`。demo 登入：`admin@certimate.com` / `admin123`。

## 現況數字（2026-04-23）

| 項目 | 數量 |
|------|------|
| 頁面（`page.tsx`） | 49 |
| 客戶端元件（`client.tsx`） | 5 |
| 根級元件（`components/`） | 24 |
| API Service 物件 | 32 |
| Custom Hooks | 3 |
| 型別定義檔 | `types/models.ts`, `types/api.ts` |

## 技術棧

| 層級 | 技術 |
|------|------|
| 框架 | Next.js 15.4.9 + React 19.2.1 + TypeScript 5.9.3 |
| 樣式 | TailwindCSS 4.1 + PostCSS |
| 認證 | Firebase Google OAuth + JWT Bearer |
| AI | `@google/genai` 1.17 |
| 圖表 | Recharts 3.8 |
| 動畫 | Motion 12.23 |
| 圖示 | Lucide React |
| 表單 | React Hook Form + Zod |
| 圖譜 | ForceGraph |

## 重要路徑

| 路徑 | 說明 |
|------|------|
| `app/layout.tsx` | Root layout（AuthProvider + NavbarWrapper） |
| `app/login/` | 登入（credentials + Google SSO + demo 快登） |
| `lib/api/client.ts` | HTTP client（自動注入 Bearer token） |
| `lib/api/services.ts` | **API 服務層 SSOT** — 所有 API 呼叫 |
| `lib/auth-context.tsx` | 認證狀態 |
| `lib/onboarding-context.tsx` | 引導流程狀態 |
| `types/models.ts` | 領域模型型別 |
| `types/api.ts` | API 請求 / 回應型別 |
| `components/` | 可重用 UI 元件 |
| `hooks/` | Custom hooks |
| `firebase.ts` | Firebase 初始化 |

## 頁面路由

### 公開
`/`, `/login`, `/signup`, `/forgot-password`, `/verify-email`, `/verify-email/sent`, `/pricing`

### 使用者
`/dashboard`, `/onboarding`, `/account`, `/knowledge`, `/review`, `/feedback`

### 考試流程
`/exam/setup`, `/exam/workspace`, `/exam/results`, `/practice`

### 資源 / 學習庫
- `/account/resource-library` — 學習庫總覽（素材 + 知識地圖 Tab）
- `/resources/[id]/` — 資源詳情
- `/resources/[id]/candidates/` — 題目抽取確認（T2/T3）
- 學習鷹架（解析內容）整合於 `/knowledge?resourceId=...` — 知識地圖右側欄

### B2B
`/edu-console`

### 平台管理（super-admin）
`/super-admin/dashboard`、`/users`、`/users/[userId]`、`/settings`、`/audit-logs`、`/finance`、`/moderation`、`/platform-subjects`、`/platform-subjects/[id]`

## API Service 清單（32 個）

| 類別 | Services |
|------|----------|
| 核心 | authService, accountService, subjectService, subscriptionService |
| 學習資源 | documentService, resourceLibraryService, resourceShareService, resourceParseService, questionCandidateService, scaffoldService, blindInferenceService |
| 考試題庫 | examService, practiceService, reviewService, difficultyProgressionService, retirementService |
| 知識圖譜 | knowledgeService, learningJourneyService |
| 儀表板 / 社群 | dashboardService, announcementService, communityService, feedbackService, anomalyService, onboardingService |
| B2B / 機構 | adminService |
| 平台管理 | superAdminService, adminDefaultResourceService, promptTemplateService, importService, platformSubjectAdminService, subjectForkService |
| 成本 | costMonitorService |

## Custom Hooks

- `use-mobile.ts` — 行動裝置偵測
- `use-import-task-polling.ts` — 考古題匯入任務輪詢
- `use-progress-worker.ts` — Web Worker 進度管理

## Auth 狀態（useAuth hook）

```typescript
{
  user: User | null
  loading: boolean
  isAuthenticated: boolean
  isPro / isProPlus / isUltra: boolean
  isAdmin: boolean         // ADMIN / SUPER_ADMIN
  isStudent: boolean       // STUDENT role (EDU)
  isEdu: boolean           // EDU tier
  isTrial: boolean
  subscriptionTier: 'FREE' | 'PRO_199' | 'PRO_PLUS_399' | 'ULTRA_1599' | 'EDU'
  onboardingCompleted: boolean
  loginWithCredentials(email, password, rememberMe)
  loginWithGoogle()
  signOut()
}
```

## 元件清單

**通用**：Navbar, NavbarWrapper, TiTiLogo, SubjectSwitcher, SubjectPickerModal, AnnouncementBanner, TrialBanner, PendingJourneysBanner, MindMapTree, ForceGraph, DomainRadarChart, StreakCounter, DailyQuestCard, AchievementBadge, AchievementGrid, GrowthTimeline, Confetti, ExamLoadingOverlay, ExamSettlementScreen

**考古題匯入**：ExamImportForm, ImportDashboardStats, ImportJobsList, ImportTaskProgressCard

## 環境變數

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_API_MODE=real
NEXT_PUBLIC_GOOGLE_CLIENT_ID=
NEXT_PUBLIC_BUILD_COMMIT=     # CI 注入
NEXT_PUBLIC_BUILD_TIME=       # CI 注入
APP_URL=http://localhost:3005
GEMINI_API_KEY=
```

## 重要模式

- **全部客戶端渲染**：所有頁面 `'use client'`，`output: 'export'`
- **API SSOT**：`lib/api/services.ts` 是所有 API 呼叫的唯一來源
- **Token 儲存**：`certimate_jwt_token`（Remember Me → localStorage，否則 sessionStorage）
- **路徑別名**：`@/*` → `frontend/` 根
- **Onboarding 草稿**：存 `localStorage.certimate_onboarding_draft`
- **建置忽略 ESLint**：`ignoreDuringBuilds: true`
- **HMR 停用**：`DISABLE_HMR=true`

## 動態路由 + 靜態匯出陷阱

**不可用 `useParams()` 讀動態路由的 param**。靜態匯出時 `generateStaticParams()` 產出單一 stub 檔（例：`/resources/[id]/candidates/`），Firebase rewrite 把所有 UUID 都指到該 stub 的 `index.html`，`useParams()` 只會讀到 stub 檔名字面值（例如 `"detail"`），不是實際 URL 的 UUID。

**正確做法**：從 `window.location.pathname` regex 解析：

```typescript
function useResourceIdFromPath(): string {
  const [id, setId] = useState('');
  useEffect(() => {
    const m = window.location.pathname.match(/\/resources\/([^/]+)\/parsed/);
    if (m) setId(m[1]);
  }, []);
  return id;
}
```

## Firebase Rewrite 注意事項

- `<Link href="/resources/x/candidates">` 會產生**無尾斜線** URL；Firebase rewrite 必須同時設有尾 / 無尾兩版
- 驗證導航必須**實際 click `<Link>`**，禁用 `window.location` 或直接輸網址（會繞過 Link 與 rewrite）

## 訂閱方案 Enum

```typescript
SubscriptionTier: 'FREE' | 'PRO_199' | 'PRO_PLUS_399' | 'ULTRA_1599' | 'EDU'
SubscriptionStatus: 'ACTIVE' | 'CANCELED' | 'PAST_DUE' | 'TRIAL'
UserRole: 'USER' | 'ADMIN' | 'STUDENT'
```

後端回傳的 `subscription_plan` 為 `FREE` / `PRO` / `PRO_PLUS` / `ULTRA`，auth-context 會轉換為帶價格後綴的 Tier。

## 注意事項

- Super Admin 頁面需要 `role: ADMIN` 或 `SUPER_ADMIN`
- 無 mock server / MSW — 前端測試需真實後端 API
- Build commit / time 由 CI 注入環境變數並顯示在 footer / about
