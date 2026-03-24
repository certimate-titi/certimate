---
name: aibdd.auto.frontend.msw-api-layer
description: 前端 Stage 1：從 api.yml + discovery features 產出 TypeScript 型別定義（types/models.ts、types/api.ts）與 mock services（lib/api/services.ts）。
user-invocable: true
argument-hint: "[specs-root-dir] [project-root]"
---

# 角色

資料層建構者。從規格產出型別安全的 API 層，讓後續的頁面元件實作都能直接引用。

---

# Entry 條件

先詢問：
- `SPECS_ROOT_DIR`（discovery 產出的規格根目錄）
- `PROJECT_ROOT`（前端專案根目錄）

---

# 輸入

| 來源 | 用途 |
|------|------|
| `${SPECS_ROOT_DIR}/api/api.yml` | endpoints → service 函式、schemas → TypeScript interfaces、error codes → 錯誤模擬 |
| `${SPECS_ROOT_DIR}/features/**/*.feature` | Given 步驟中的具體實體資料 → 寫實的 mock data |
| `${SPECS_ROOT_DIR}/erm.dbml` | 實體關聯 → Domain Models 的欄位與型別 |

---

# 已有基礎建設（勿覆寫）

以下檔案已存在，本階段只在標記處補充，不重建：

- `lib/api/client.ts` — `apiClient` 物件（get/post/put/delete/upload），自動注入 Firebase Auth Bearer token
- `lib/utils.ts` — `cn()` 工具函式（clsx + tailwind-merge）
- `firebase.ts` — Firebase 初始化（Auth + Firestore）
- `lib/auth-context.tsx` — AuthProvider + useAuth() hook

---

# 產出物

## 1. Domain Models（`types/models.ts`）

對 `api.yml` 中每個 `components/schemas` 及 `erm.dbml` 中的實體：

- 使用純 TypeScript `type` 或 `interface`（**不使用 Zod**）
- Enum 使用 `type X = 'A' | 'B' | 'C'` 語法
- 欄位命名使用 camelCase
- 日期/時間欄位使用 `string`（ISO timestamp），加上 `// ISO timestamp` 註解
- 在 `types/index.ts` 補上 re-export

```typescript
// types/models.ts 範例
export type SubscriptionTier = 'FREE' | 'PRO_199' | 'PRO_PLUS_399' | 'ULTRA_1599';

export interface User {
  id: string;
  email: string;
  displayName: string;
  subscriptionTier: SubscriptionTier;
  createdAt: string; // ISO timestamp
}
```

## 2. API 契約型別（`types/api.ts`）

對 `api.yml` 中每個 endpoint 的 request/response：

- 產生 `{Action}Request` 和 `{Action}Response` interface
- Request type import 必要的 Domain Model type
- Response type 封裝 Domain Model（如 `{ user: User; token: string }`）
- 在 `types/index.ts` 補上 re-export

```typescript
// types/api.ts 範例
import type { User, Document } from './models';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface GetDocumentsResponse {
  documents: Document[];
  totalCount: number;
}
```

## 3. Mock Services（`lib/api/services.ts`）

**單一檔案**，為所有 API 操作的統一入口。對 `api.yml` 中每個 endpoint：

- 產生一個 async 函式（命名依語意：`login`、`getDocuments`、`createExam` 等）
- 目前返回 mock 資料，**函式簽名即 API 契約**——後端就緒後改為呼叫 `apiClient`
- Mock 資料使用**來自 features 的具體資料**（不隨意編造）
- 頂部加上 JSDoc 說明此檔案的設計意圖

```typescript
/**
 * API Service Layer
 *
 * 每個函式目前返回 mock 資料，後端就緒後改為呼叫 apiClient。
 * 函式簽名即 API 契約——後端實作時不應改變。
 */

import type { LoginRequest, AuthResponse, GetDocumentsResponse } from '@/types';

// ===========================
// Auth API
// ===========================

export async function login(data: LoginRequest): Promise<AuthResponse> {
  // TODO: 改為 apiClient.post<AuthResponse>('/auth/login', data)
  return {
    user: { id: '1', email: data.email, displayName: '測試使用者', ... },
    token: 'mock-jwt-token',
  };
}
```

### Mock 資料規則

- mock 資料內嵌在每個函式中（不抽出獨立 fixtures 檔案）
- 資料必須來自 `${SPECS_ROOT_DIR}/features/` 的具體 Given 步驟範例
- 每個 enum 至少覆蓋 2 個以上的值
- 關聯資料的 ID 必須對得上（如 `document.userId` 對應到某個 mock user 的 id）

---

# 輸出結構

```
types/
├── models.ts              ← Domain Models（type aliases + interfaces）
├── api.ts                 ← API Request/Response 契約
└── index.ts               ← Barrel re-export（已有，補充新 export）
lib/
└── api/
    ├── client.ts           ← 已有，不動
    └── services.ts         ← Mock services（單一檔案，所有 API 函式）
```

---

# 規則

- Mock 資料**必須來自** `${SPECS_ROOT_DIR}/features/` 的具體範例，不得憑空編造
- 每個 `api.yml` endpoint **必須**有對應的 service 函式
- 型別使用純 TypeScript interface/type，**不使用 Zod**
- `services.ts` 為**單一檔案**，不按 resource 拆分（保持專案現有慣例）
- 函式簽名（參數型別 + 回傳型別）即為 API 契約，後端實作時不應改變
- 不覆寫「已有基礎建設」中的檔案
- 不產生任何 UI 元件，此階段只處理型別與資料層

---

# 完成條件

- 所有 `api.yml` schemas 均有對應的 TypeScript type/interface
- 所有 `api.yml` endpoints 均有對應的 service 函式
- `services.ts` 的 mock 資料可追溯至 `features/` 的具體 Given 步驟
- `types/index.ts` 正確 re-export 所有型別
- TypeScript 編譯無錯誤（`npx tsc --noEmit`）
