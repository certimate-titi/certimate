# 權限模型 SSOT

最後更新：2026-05-03（TiTi Commander）

本文件為 CertiMate 帳號類型與權限守衛的**唯一真實來源**。前後端任何權限相關改動都必須先對照此文件。

---

## 1. 帳號類型總覽

### 1.1 管理者帳號（內部，不是用戶）

| Role | 權限定位 | DB 值 |
|------|---------|------|
| `ADMIN` | 後台基本權限：用戶問題協助排除、客服級操作。**自動含所有 user-facing tier 功能（含 ULTRA）** | `admin` |
| `SUPER_ADMIN` | 含所有 ADMIN 權限 + **高等設定**：Prompt 模板、金額/預算上限、Feature Flag、系統設定、AI 模型路由、API Keys、成本監控 | `super_admin` |

> 兩者皆 bypass 用戶 tier 的付費 gate；SUPER_ADMIN 在管理者範圍內權限更高。

### 1.2 用戶 tier（B2C 自費）

| Tier | 限制 / 權限 | 月費（NT$） |
|------|-----------|-----------|
| `FREE` | 10 題/次、3 次免費 AI chat、詳解 select-none | 0 |
| `PRO_199` | 50 題/次、無限文件 / YouTube 解析、基礎 AI（不含 PRO_PLUS-only chat） | 199 |
| `PRO_PLUS_399` | 100 題/次、Vision OCR、對話式 AI 教練、動態弱點出題 | 399 |
| `ULTRA_1599` | 無題數上限、完整 AI 教練、教育管理（建立 EDU 學生帳號最多 30 名）、進階出題配方 | 1,599 |

### 1.3 附屬帳號（B2B 機構）

| Tier | 說明 |
|------|------|
| `EDU` | 附屬於 ULTRA 機構底下的學生帳號。50 題/次、共用機構配額池、基礎 AI chat、無限文件解析、無 Vision OCR；不可自行訂閱（僅機構管理員透過 CSV 匯入或邀請建立）；被指派時若已有個人付費訂閱會自動暫停計費（依 Feature 08）|

### 1.4 其他角色（B2B / 內部）

| Role | 用途 |
|------|------|
| `STUDENT` | EDU 學生帳號的 user role |
| `ORG_ADMIN` | 機構管理員（B2B）|
| `USER` | 一般用戶 role（FREE/PRO/PRO_PLUS/ULTRA tier 的預設）|

---

## 2. 前端 useAuth() flag 對照

| Flag | 規則 |
|------|------|
| `isAuthenticated` | 已登入 |
| `isPro` | tier ∈ {PRO_199, PRO_PLUS_399, ULTRA_1599} |
| `isProPlus` | tier ∈ {PRO_PLUS_399, ULTRA_1599} |
| `isUltra` | tier === 'ULTRA_1599' |
| `isEdu` | tier === 'EDU' |
| `isStudent` | role === 'STUDENT' |
| `isAdmin` | role ∈ {'ADMIN', 'SUPER_ADMIN'} |
| `isSuperAdmin` | role === 'SUPER_ADMIN' |
| `isTrial` | subscriptionStatus === 'TRIAL' |

---

## 3. 守衛規則（前端）

### 3.1 標準守衛模式

| 用途 | 守衛條件 |
|------|---------|
| user-facing tier 功能（管理者皆 bypass） | `(isUltra \|\| isAdmin)` |
| ULTRA-only 功能（含管理者 bypass） | 同上 `(isUltra \|\| isAdmin)` |
| 一般管理者後台（ADMIN+SUPER_ADMIN 皆可進） | `isAdmin` |
| **高等設定**（僅 SUPER_ADMIN） | `isSuperAdmin` |
| EDU 學生限定操作 | `isEdu` |

### 3.2 守衛實作清單（已稽核）

#### user-facing tier 守衛（`isUltra \|\| isAdmin`）

| 檔案 | 守衛 | 用途 |
|------|------|------|
| `frontend/components/Navbar.tsx:31` | `(isUltra \|\| isAdmin)` | 教育管理 nav 連結 |
| `frontend/app/exam/setup/page.tsx:699` | `(isUltra \|\| isAdmin)` | 進階出題配方面板（Bloom 比例自訂）|
| `frontend/app/review/page.tsx:48` | `!isAdmin` | isFreeUser 判定 |
| `frontend/app/review/page.tsx:49` | `!isAdmin` | isPro199Only 判定 |
| `frontend/app/review/page.tsx:50` | `\|\| isAdmin` | canChat（chat 功能開放）|

#### 一般管理者守衛（`isAdmin`）

| 檔案 | 用途 |
|------|------|
| `frontend/components/Navbar.tsx:32` | 平台管理 nav 連結 |
| `frontend/app/super-admin/layout.tsx` | 整個 /super-admin 子樹進入閘 |
| `frontend/app/super-admin/platform-subjects/page.tsx` | 平台科目管理 |
| `frontend/app/super-admin/default-resources/page.tsx` | 預設資源管理 |

#### 高等設定守衛（`isSuperAdmin`）— 2026-05-03 稽核新增

| 檔案 | 用途 |
|------|------|
| `frontend/app/super-admin/settings/layout.tsx` | 整個 settings 子樹（AI 模型路由 / API Keys / 方案限額 / 公告管理 / Feature Flags / 管理員帳號 / 版本資訊）|
| `frontend/app/super-admin/cost-monitor/page.tsx` | 成本監控中心（預算/AI 用量）|
| `frontend/app/super-admin/prompt-templates/page.tsx` | Prompt 模板列表 |
| `frontend/app/super-admin/prompt-templates/new/page.tsx` | 新增 Prompt 模板 |
| `frontend/app/super-admin/prompt-templates/[templateId]/client.tsx` | Prompt 模板詳情編輯 |

---

## 4. 後端 endpoint 守衛

### 4.1 Permission Dependency（`backend/app/core/permissions.py`）

| Dependency | 允許角色 |
|-----------|---------|
| `require_super_admin` | 僅 `SUPER_ADMIN` |
| `require_admin_or_super_admin` | `ADMIN` ∪ `SUPER_ADMIN` |

### 4.2 已驗證對齊清單

| 模組 | Endpoint | Backend 守衛 | Frontend 守衛 | 對齊 |
|------|----------|-------------|--------------|------|
| 成本監控 | `app/api/cost_monitor.py` | `require_super_admin`（全部）| `isSuperAdmin` | ✅ |
| Prompt 模板（promote / 高等操作）| `app/api/prompt_template.py:66` | `UserRole.SUPER_ADMIN` | `isSuperAdmin` | ✅ |
| Admin 一般 | `app/api/admin.py:106/125/175/202` | `(ADMIN, SUPER_ADMIN)` | `isAdmin` | ✅ |
| 升等為 SUPER_ADMIN | `app/api/admin.py:152` | `UserRole.SUPER_ADMIN` | （對應 `/super-admin/settings/admins`，由 settings layout 守住）| ✅ |
| 系統設定 | `app/services/admin_settings_service.py:26` | `UserRole.SUPER_ADMIN` | `isSuperAdmin`（settings layout）| ✅ |
| 財務 | `app/services/admin_finance_service._require_admin` | `(ADMIN, SUPER_ADMIN)` | `isAdmin` | ✅ |

---

## 5. Nav 顯示規則

| Nav 連結 | 顯示條件 |
|---------|---------|
| 儀表板 / 學習庫 / 測驗 / 練習 / 排程 / AI 教練 | 已登入 |
| 教育管理 | `(isUltra \|\| isAdmin)` |
| 平台管理 | `isAdmin` |

### Nav badge（`Navbar.tsx:66-78`）

| 顯示 | 條件 |
|------|------|
| 🛡️ Admin badge | `isAdmin` |
| ⭐ Ultra badge | `isUltra && !isAdmin` |
| 💎 Pro badge | `isPro && !isUltra && !isAdmin` |

---

## 6. 測試帳號

完整權限矩陣測試帳號（密碼統一 `test1234`）：

| Email | role | tier | 備註 |
|-------|------|------|------|
| `super-admin@certimate.test` | SUPER_ADMIN | ULTRA | 萬能；對齊 admin@certimate.com |
| `admin@certimate.test` | ADMIN | FREE | 純 ADMIN 測試（非 SUPER_ADMIN）|
| `ultra@certimate.test` | USER | ULTRA | 純付費 ULTRA 用戶 |
| `pro-plus@certimate.test` | USER | PRO_PLUS | |
| `pro@certimate.test` | USER | PRO | |
| `free@certimate.test` | USER | FREE | 最受限 |
| `edu@certimate.test` | STUDENT | EDU | EDU 學生帳號 |
| `admin@certimate.com` | SUPER_ADMIN | ULTRA | 既有 demo 帳號（密碼 `admin123`）|

### 6.1 建立方式

**雲端後端**（部署後）：
```bash
curl -X POST https://<cloud-run-url>/api/v1/auth/seed-test-accounts
```

**本地後端**（CLI）：
```bash
cd backend && .venv/bin/python -m app.scripts.seed_test_accounts
```

兩者皆 idempotent（已存在則更新為標準狀態）。

### 6.2 端對端驗證結果（2026-05-03 本地驗證）

| 帳號 | 路徑 | 預期 | 實測 |
|------|------|------|------|
| ADMIN/FREE | `/super-admin/dashboard` | ✅ 進入 | ✅ |
| ADMIN/FREE | `/super-admin/cost-monitor` | ❌ redirect→dashboard | ✅ |
| ADMIN/FREE | `/super-admin/settings` | ❌ redirect→dashboard | ✅ |
| ADMIN/FREE | `/super-admin/prompt-templates` | ❌ redirect→dashboard | ✅ |
| ADMIN/FREE | `/exam/setup` 進階配方面板 | ✅ 顯示（isAdmin bypass tier）| ✅ |
| ADMIN/FREE | nav 教育管理 | ✅ 顯示（isAdmin bypass tier）| ✅ |
| USER/ULTRA | `/super-admin/dashboard` | ❌ redirect→/dashboard | ✅ |
| USER/ULTRA | `/exam/setup` 進階配方 | ✅ 顯示（isUltra）| ✅ |
| USER/ULTRA | nav 教育管理 | ✅ 顯示（isUltra）| ✅ |
| USER/ULTRA | nav 平台管理 | ❌ 不顯示 | ✅ |
| USER/FREE | `/exam/setup` 進階配方 | ❌ 不顯示 | ✅ |
| USER/FREE | nav 教育管理 | ❌ 不顯示 | ✅ |
| USER/FREE | nav 平台管理 | ❌ 不顯示 | ✅ |

---

## 7. 變更歷史

- **2026-05-03 v4** — 新增 `seed_test_accounts` CLI + `/auth/seed-test-accounts` endpoint；建立 7 個權限矩陣測試帳號；本地端對端驗證 13 條守衛規則全綠。
- **2026-05-03 v3** — `/super-admin/settings/*`、`cost-monitor`、`prompt-templates` 加 `isSuperAdmin` 守衛（SUPER_ADMIN-only 高等設定）。
- **2026-05-03 v2** — 確認 ADMIN 自動含 ULTRA 功能；3 處 user-facing tier 守衛回退至 `(isUltra || isAdmin)`。
- **2026-05-03 v1** — 引入 `isSuperAdmin` flag、`auth-context` 不再攤平 SUPER_ADMIN→ADMIN。

---

## 8. 修改本文件的流程

1. 任何權限模型變動必須**先改本文件**，再改 code
2. CTO Code Review 時對照此文件確認守衛一致性
3. 變更後在第 7 節追加版本記錄
