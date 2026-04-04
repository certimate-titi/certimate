# CLAUDE.md — Frontend

## 快速啟動

```bash
cd frontend
npm install
npm run dev    # http://localhost:3005
```

需要後端 API 運行於 `http://localhost:8000/api/v1`。

快速登入（開發模式）：`admin@certimate.com` / `admin123`

## 現況數字（2026-04-01）

| 項目 | 數量 |
|------|------|
| 頁面路由 | 23 |
| 元件 | 20（14 通用 + 6 Onboarding） |
| API Service 物件 | 13 |
| API Service 函式 | 68+ |
| Custom Hooks | 1 |
| 型別定義檔 | 3 |

## 技術棧

| 層級 | 技術 |
|------|------|
| 框架 | Next.js 15.4 (App Router) + React 19 + TypeScript 5.9 |
| 樣式 | TailwindCSS 4.1 + PostCSS |
| 認證 | Firebase Google OAuth + JWT Bearer Token |
| 表單 | React Hook Form + Zod |
| 圖表 | Recharts |
| 動畫 | Motion (Framer Motion) |
| 圖示 | Lucide React |
| AI | Google Gemini (`@google/genai`) |

## 重要路徑

| 路徑 | 說明 |
|------|------|
| `app/layout.tsx` | Root layout（AuthProvider + NavbarWrapper） |
| `app/login/page.tsx` | 登入頁（credentials + Google SSO + demo 快登） |
| `lib/api/client.ts` | HTTP client（自動注入 Bearer token） |
| `lib/api/services.ts` | **API 服務層 SSOT** — 所有 API 呼叫由此發出 |
| `lib/auth-context.tsx` | 認證狀態（user, loading, isPro, isAdmin...） |
| `lib/onboarding-context.tsx` | 4 步引導流程狀態 |
| `types/models.ts` | 領域模型型別 |
| `types/api.ts` | API 請求/回應型別 |
| `components/` | 可重用 UI 元件 |
| `hooks/use-mobile.ts` | 行動裝置偵測 hook |

## 頁面路由總覽

### 公開頁面
- `/` — 首頁
- `/login` — 登入
- `/signup` — 註冊
- `/forgot-password` — 忘記密碼
- `/verify-email` — Email 驗證
- `/verify-email/sent` — 驗證信已寄出

### 使用者頁面
- `/dashboard` — 個人儀表板
- `/onboarding` — 首次登入引導（4 步驟）
- `/account` — 帳號設定
- `/knowledge` — 知識心智圖
- `/review` — 錯題複習
- `/feedback` — 意見反饋

### 考試流程
- `/exam/setup` — 測驗設定
- `/exam/workspace` — 考試作答
- `/exam/results` — 測驗結果

### B2B
- `/edu-console` — 教育機構管理

### 平台管理後台（super-admin）
- `/super-admin/dashboard` — 管理儀表板
- `/super-admin/users` — 使用者管理
- `/super-admin/users/[userId]` — 使用者詳情
- `/super-admin/settings` — 系統設定
- `/super-admin/audit-logs` — 稽核日誌
- `/super-admin/finance` — 財務管理
- `/super-admin/moderation` — 內容審核

## API Service 物件清單

| Service | 主要函式 |
|---------|----------|
| `authService` | login, signup, verifyEmail, googleSSO, getCurrentUser |
| `documentService` | upload, list, getById, delete |
| `examService` | create, getExam, submit, getResults |
| `reviewService` | getWrongQuestions, getChatHistory, sendMessage |
| `dashboardService` | get, completeDailyQuest |
| `knowledgeService` | getMap, getNodeDetail |
| `accountService` | updateProfile, uploadAvatar, getUsage, getAchievements, deleteAccount |
| `subscriptionService` | upgrade, cancel |
| `adminService` | getStudentList |
| `superAdminService` | 30+ 函式（users, settings, finance, moderation, audit） |
| `onboardingService` | getSubjectCatalog, submit |
| `subjectService` | getUserSubjects, addSubject |
| `announcementService` | getActive |

## Auth 狀態（useAuth hook）

```typescript
{
  user: User | null           // 完整使用者資料
  loading: boolean            // 初始載入中
  isAuthenticated: boolean
  isPro: boolean              // PRO_199+
  isProPlus: boolean          // PRO_PLUS_399+
  isUltra: boolean            // ULTRA_1599
  isAdmin: boolean            // ADMIN / SUPER_ADMIN
  isStudent: boolean          // STUDENT role (EDU plan)
  isEdu: boolean              // EDU tier
  isTrial: boolean            // 14-day trial active
  subscriptionTier: 'FREE' | 'PRO_199' | 'PRO_PLUS_399' | 'ULTRA_1599' | 'EDU'
  onboardingCompleted: boolean
  loginWithCredentials(email, password, rememberMe)
  loginWithGoogle()
  signOut()
}
```

## 元件清單

### 通用元件
Navbar, NavbarWrapper, TiTiLogo, SubjectSwitcher, SubjectPickerModal, AnnouncementBanner, MindMapTree, StreakCounter, DailyQuestCard, AchievementBadge, AchievementGrid, GrowthTimeline, Confetti, ExamLoadingOverlay

### Onboarding 元件
StepWelcome, SubjectPicker, SelectedSubjectCard, StepPreferences, StepConfirmation, OnboardingProgress

## 環境變數

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_FIREBASE_API_KEY=           # Google OAuth（選填）
GEMINI_API_KEY=                         # Gemini AI
APP_URL=http://localhost:3005
```

## 重要模式

- **全部客戶端渲染**：所有頁面 `'use client'` — 靜態匯出模式 (`output: 'export'`)
- **API 服務層 SSOT**：`lib/api/services.ts` 是所有 API 呼叫的唯一來源
- **Token 儲存**：Remember Me → localStorage；否則 → sessionStorage
- **路徑別名**：`@/*` → `frontend/` 根目錄
- **Onboarding 草稿**：存在 localStorage (`certimate_onboarding_draft`)
- **建置忽略 ESLint**：`next.config.ts` 中 `ignoreDuringBuilds: true`
- **HMR 可停用**：`DISABLE_HMR=true`

## 訂閱方案 Enum

```typescript
// types/models.ts
SubscriptionTier: 'FREE' | 'PRO_199' | 'PRO_PLUS_399' | 'ULTRA_1599' | 'EDU'
SubscriptionStatus: 'ACTIVE' | 'CANCELED' | 'PAST_DUE' | 'TRIAL'
UserRole: 'USER' | 'ADMIN' | 'STUDENT'
```

## 注意事項

- 後端回傳的 `subscription_plan` 為 `FREE`/`PRO`/`PRO_PLUS`/`ULTRA`，前端 auth-context 會轉換為帶價格後綴的 Tier
- Google SSO 需要 Firebase 設定，本地開發可用 credentials 登入替代
- Super Admin 頁面需要 `role: ADMIN` 或 `SUPER_ADMIN`
- 無 mock server/MSW — 前端測試需真實後端 API
