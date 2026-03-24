---
name: aibdd.auto.frontend.apifirst.msw.starter
description: Frontend Walking Skeleton 初始化。從 templates/ 讀取所有樣板檔案，填入專案參數後輸出到專案目錄，建立 Next.js 15 + Firebase + Mock Services 的前端骨架。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[project-root]"
input: 專案根目錄路徑 + arguments.yml 參數
output: 完整的 Frontend Walking Skeleton（可直接 npm install + npm run dev 執行）
---

# 角色

Walking Skeleton 建構器。你從 templates/ 讀取樣板，替換 placeholder，寫入專案目錄。

---

# Placeholder 說明

| Placeholder | 來源 | 說明 | 範例 |
|-------------|------|------|------|
| `{{PROJECT_NAME}}` | 詢問使用者 | 專案顯示名稱 | `CertiMate` |
| `{{PROJECT_SLUG}}` | 從 PROJECT_NAME 推導 | URL-safe slug | `certimate` |
| `{{TYPES_DIR}}` | arguments.yml | TypeScript 型別目錄 | `types` |
| `{{API_DIR}}` | arguments.yml | API 服務層目錄 | `lib/api` |
| `{{FRONTEND_FEATURES_DIR}}` | arguments.yml | BDD features 目錄 | `features` |

---

# 執行流程

## Step 1：收集參數

1. 讀取 `${PROJECT_ROOT}/specs/arguments.yml`（若不存在，讀取上層目錄的 `specs/arguments.yml`）
2. 詢問使用者：PROJECT_NAME
3. 推導：PROJECT_SLUG（kebab-case）

## Step 2：建立目錄結構

```
${PROJECT_ROOT}/
├── app/                               # Next.js App Router 頁面
│   ├── layout.tsx                     # Root Layout（AuthProvider + Navbar）
│   ├── page.tsx                       # Landing Page
│   ├── globals.css                    # TailwindCSS 4 import
│   ├── error.tsx                      # Error boundary
│   ├── not-found.tsx                  # 404 page
│   ├── login/
│   ├── signup/
│   └── dashboard/
├── components/                        # 可重用 React 元件
│   └── onboarding/                    # 功能分組子目錄
├── lib/                               # 核心邏輯
│   ├── api/
│   │   ├── client.ts                  # apiClient（Firebase Auth Bearer token）
│   │   └── services.ts                # API 服務層（mock data，函式簽名即 API 契約）
│   ├── auth-context.tsx               # Firebase Auth 狀態管理
│   └── utils.ts                       # cn() 工具函式（clsx + tailwind-merge）
├── hooks/                             # Custom React hooks
├── types/                             # TypeScript 型別定義
│   ├── models.ts                      # Domain models（鏡像 DB Schema）
│   ├── api.ts                         # API request/response 契約
│   └── index.ts                       # Barrel re-export
├── firebase.ts                        # Firebase 初始化（Auth + Firestore）
├── firestore.rules                    # Firestore 安全規則
├── firebase.json                      # Firebase Hosting 設定
├── next.config.ts                     # Next.js 設定（static export）
├── tsconfig.json                      # TypeScript 設定（@/* 路徑別名）
├── postcss.config.mjs                 # PostCSS + TailwindCSS 4
├── eslint.config.mjs                  # ESLint 9 flat config
├── package.json
└── .env.example
```

## Step 3：讀取 templates，替換 placeholder，寫入專案

依據 templates/ 中的樣板檔案，替換 placeholder 後寫入專案目錄。

## Step 4：建立空 .gitkeep

- `hooks/.gitkeep`
- `components/.gitkeep`

## Step 5：驗證

確認所有檔案已寫入、無殘留 `{{PLACEHOLDER}}`。

---

# 技術棧說明

| 項目 | 技術 | 版本 |
|------|------|------|
| Framework | Next.js (App Router) | 15.x |
| Runtime | React | 19.x |
| Language | TypeScript (strict) | 5.x |
| Styling | TailwindCSS | 4.x |
| CSS Utility | clsx + tailwind-merge | `cn()` |
| Component Variants | class-variance-authority (cva) | latest |
| Auth / DB | Firebase (Auth + Firestore) | 12.x |
| AI | Google Gemini (@google/genai) | latest |
| Forms | react-hook-form + @hookform/resolvers | 7.x |
| Icons | lucide-react | latest |
| Animation | motion | 12.x |
| Charts | recharts | 3.x |
| Date | date-fns | 4.x |
| Deployment | Firebase Hosting (static export) | — |
| Node.js | | 20+ |

---

# 專案慣例

| 慣例 | 說明 |
|------|------|
| 路徑別名 | `@/*` → 專案根目錄（如 `@/lib/api/services`、`@/types`） |
| 所有頁面 | 使用 `'use client'`（因 static export，無 Server Components） |
| API 服務層 | `lib/api/services.ts` 為單一入口，目前返回 mock data，函式簽名即 API 契約 |
| API Client | `lib/api/client.ts` 提供 `apiClient.get/post/put/delete/upload`，自動注入 Firebase Auth token |
| 型別定義 | `types/models.ts`（Domain Models）+ `types/api.ts`（Request/Response），使用純 TypeScript interface（無 Zod） |
| Auth | `lib/auth-context.tsx` 提供 `AuthProvider` + `useAuth()` hook，支援 Firebase Auth 與 Demo 模式 |
| 樣式 | TailwindCSS 4 classes + `cn()` 工具函式合併 class |
| Dev build | `.next-dev/` 目錄（與 production `.next/` 分開） |
| HMR | 可透過 `DISABLE_HMR=true` 環境變數關閉 |

---

# 安全規則

- **不覆蓋已存在的檔案**。
- **不建立 feature-specific 的程式碼**（如具體頁面、具體 API 函式）。
- **不執行 npm install**（僅提示使用者）。
- **不產生任何具體的 mock data**（那是 `api-layer` worker 的工作）。

---

# 完成後引導

```
Walking skeleton 已建立完成。

產出的檔案：（列出所有檔案）

下一步：
1. cd {{PROJECT_ROOT}} && npm install
2. 設定 .env.local（GEMINI_API_KEY、NEXT_PUBLIC_FIREBASE_API_KEY）
3. /aibdd.discovery — 開始需求探索
4. /aibdd.auto.frontend.msw-api-layer — 從 api.yml 產出型別定義與 mock services
```
