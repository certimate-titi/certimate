# 平台管理後台 (Super Admin Dashboard)

## 📌 頁面定位與目標

這是一個專屬於 **平台營運團隊** 的最高權限管理介面，與一般用戶及 B2B 機構管理後台完全獨立。目標是讓平台擁有者能即時監控系統健康度、管理所有用戶生命週期、追蹤財務營收，並處理內容安全與系統設定，確保 CertiMate 平台穩定運營與商業成長。

**存取路徑**：`/super-admin/...`（獨立路由，需 `super_admin` 或 `admin` 角色方可進入）

---

## 🔐 角色權限架構 (RBAC)

平台管理後台採用分層權限設計，與現有 B2B 機構管理員 (`org_admin`) 及一般用戶完全隔離：

| 角色 | 代碼 | 權限範圍 |
|------|------|---------|
| **超級管理者** | `super_admin` | 所有權限，包含管理員帳號 CRUD、系統設定、Feature Flags |
| **營運管理員** | `admin` | 用戶管理、內容審核、財務檢視（唯讀）、公告發布 |
| **B2B 機構管理員** | `org_admin` | 僅限自己機構的學生管理與派卷分析（已於 B2B Dashboard 規劃） |
| **一般用戶** | `user` | 個人學習功能（Free / Pro / Ultra） |

### 權限驗證流程

1. 使用者登入後，Firebase Auth 回傳 ID Token (JWT)。
2. Main API 從 Cloud SQL 查詢 `admin_roles` 表，確認該用戶角色。
3. 中介層 (Middleware) 攔截所有 `/super-admin/*` 路由，驗證角色為 `super_admin` 或 `admin`。
4. 所有管理操作自動寫入 `admin_audit_logs` 審計日誌。

---

## 🧩 核心功能模組

### 模組一：營運儀表板 (Operations Dashboard)

**路由**：`/super-admin/dashboard`
**功能目的**：一眼掌握平台整體健康度與商業指標。

#### 1.1 核心指標卡片 (KPI Cards)

| 指標 | 資料來源 | 更新頻率 |
|------|---------|---------|
| DAU / MAU（每日/月活躍用戶） | Cloud SQL `users` + `user_usage_logs` | 即時 |
| 新註冊用戶數（今日/本週/本月） | Cloud SQL `users.created_at` | 即時 |
| 訂閱轉換率（Free → Pro → Ultra） | Cloud SQL `users.subscription_tier` | 每小時 |
| MRR（每月經常性收入） | Stripe API / 綠界交易紀錄 | 每日 |
| AI Token 今日消耗金額 | OpenRouter Usage API | 每 15 分鐘 |
| 任務佇列深度 | Pub/Sub Monitoring API | 即時 |

#### 1.2 趨勢圖表區

- **用戶成長曲線**：過去 30 天的 DAU/MAU 折線圖，可切換至 90 天或年度檢視。
- **營收趨勢**：MRR、ARPU (平均每用戶收入)、Churn Rate (流失率) 的多軸折線圖。
- **AI 成本分析**：各 LLM 模型（Gemini Flash / Claude Sonnet / GPT-4o）的每日 Token 消耗堆疊柱狀圖。
- **系統負載儀表**：Cloud Run CPU/Memory 使用率、Cloud SQL 連線數、Redis 快取命中率的即時儀表板。

#### 1.3 近期異常警報 (Alert Feed)

- Worker 任務失敗率超過 5%。
- 單一用戶觸發 Rate Limit 冷卻機制。
- Cloud SQL 連線數超過 80% 上限。
- OpenRouter 單日費用超出預算閾值。

---

### 模組二：用戶管理 (User Management)

**路由**：`/super-admin/users`
**功能目的**：管理所有用戶的完整生命週期。

#### 2.1 用戶列表頁

- **搜尋與篩選**：
  - 關鍵字搜尋（Email、姓名、User ID）。
  - 篩選條件：訂閱方案（Free / Pro / Ultra）、註冊日期區間、最後登入日期、帳號狀態（正常 / 停權 / 冷卻中）。
- **排序**：依註冊時間、最後活躍時間、Token 消耗量排序。
- **批量操作**：
  - 匯出篩選結果為 CSV。
  - 批量發送系統公告信。

#### 2.2 用戶詳情頁

**路由**：`/super-admin/users/:userId`

| 區塊 | 內容 |
|------|------|
| **基本資料** | 姓名、Email、註冊方式（Email/Google SSO）、註冊日期 |
| **訂閱狀態** | 當前方案、到期日、Stripe Customer ID、付款歷程 |
| **使用行為** | 上傳次數、考試完成次數、AI 問答次數、Vision OCR 使用頁數 |
| **Token 消耗明細** | 今日/本月 Token 用量、各模型呼叫次數分布 |
| **登入紀錄** | 最近 20 次登入的時間、IP、裝置資訊 |
| **異常紀錄** | Rate Limit 觸發次數、冷卻歷程、內容檢舉紀錄 |

#### 2.3 管理操作

| 操作 | 權限需求 | 說明 |
|------|---------|------|
| 調整訂閱等級 | `super_admin` | 手動升級/降級/延長試用期 |
| 停權帳號 | `admin` | 暫停用戶所有功能，需填寫停權原因 |
| 解除停權 | `admin` | 恢復帳號功能 |
| 重置密碼 | `admin` | 觸發 Firebase Auth 密碼重置信 |
| 發送個別通知 | `admin` | 透過 Email 或站內通知聯繫用戶 |
| 刪除帳號 | `super_admin` | GDPR 合規：觸發級聯刪除（Cascading Delete） |

---

### 模組三：財務與訂閱管理 (Finance & Billing)

**路由**：`/super-admin/finance`
**功能目的**：掌握金流狀況與訂閱轉換指標。

#### 3.1 訂閱總覽

- **方案分布圓餅圖**：Free / Pro / Ultra 各佔比。
- **MRR 趨勢折線圖**：附帶 New MRR、Expansion MRR、Churn MRR 的拆解。
- **LTV (客戶終身價值)**：依方案計算平均 LTV。

#### 3.2 交易紀錄

- 整合 Stripe Dashboard / 綠界後台的交易明細。
- 欄位：交易 ID、用戶、金額、方案、狀態（成功/失敗/退款）、時間。
- 支援依日期區間、金額區間、交易狀態篩選。

#### 3.3 退款審核

- 退款申請佇列（待審核 / 已處理）。
- 審核操作：核准退款（觸發 Stripe Refund API）或駁回（需填寫理由）。
- 退款後自動降級用戶訂閱方案至 Free。

#### 3.4 優惠碼管理

| 欄位 | 說明 |
|------|------|
| 優惠碼 | 自訂代碼（如 `LAUNCH2026`） |
| 折扣類型 | 百分比折扣 / 固定金額折抵 / 免費試用天數 |
| 適用方案 | Pro / Ultra / 全部 |
| 使用上限 | 總次數上限 / 每人限用次數 |
| 有效期間 | 起訖日期 |
| 使用統計 | 已使用次數、帶來的營收 |

#### 3.5 成本分析

- **AI Token 費用 vs 訂閱營收**：計算毛利率。
- **每用戶平均成本 (Cost per User)**：依方案拆分。
- **成本預警**：當單日 Token 費用超過設定閾值時發出警報。

---

### 模組四：內容與安全審核 (Content & Safety)

**路由**：`/super-admin/moderation`
**功能目的**：防止平台被濫用，維護內容品質與合規。

#### 4.1 上傳內容審查

- **自動標記佇列**：系統自動偵測並標記可疑上傳內容（過大檔案、異常格式、關鍵字觸發）。
- **人工審核操作**：通過 / 標記警告 / 刪除並通知用戶。
- 審核紀錄留存於 `admin_audit_logs`。

#### 4.2 AI 濫用監控

| 監控項目 | 觸發條件 | 處置 |
|---------|---------|------|
| 超綱問答轟炸 | 10 分鐘內 5 次觸發「超出題庫範圍」 | 自動冷卻 30 分鐘 |
| Token 異常消耗 | 單一用戶單日 Token 消耗超過 P99 | 標記並通知管理員 |
| 爬蟲/腳本偵測 | 異常高頻 API 呼叫 | 自動封鎖 IP + 停權帳號 |

- **冷卻中用戶列表**：顯示目前被冷卻的用戶，支援手動解除。
- **異常問答紀錄**：查看觸發防護機制的具體問答內容。

#### 4.3 檢舉管理

- 用戶檢舉佇列（待處理 / 已處理）。
- 檢舉類型：不當內容、版權疑慮、系統錯誤回報。
- 處理流程：查看檢舉內容 → 判定 → 處置（刪除內容 / 警告用戶 / 標記為誤報）。

---

### 模組五：系統設定 (System Configuration)

**路由**：`/super-admin/settings`
**功能目的**：免改 code 即時調整系統行為參數。
**權限**：僅限 `super_admin`。

#### 5.1 AI 模型路由設定

| 設定項 | 說明 | 預設值 |
|--------|------|--------|
| Free 用戶 - 基本任務模型 | 簡單考題生成 | `gemini-1.5-flash` |
| Free 用戶 - 備援模型 | Fallback 選擇 | `llama-3-8b` |
| Pro 用戶 - 進階任務模型 | 數學 OCR / AI 教練 | `claude-3.5-sonnet` |
| Pro 用戶 - 備援模型 | Fallback 選擇 | `gpt-4o` |
| Fallback 觸發條件 | Timeout 閾值 | 3000 ms |

#### 5.2 方案限額調整

| 參數 | Free | Pro | Ultra |
|------|------|-----|-------|
| 每月上傳文件數 | 5 | 50 | 無限 |
| 每月考試生成次數 | 3 | 30 | 無限 |
| AI 問答次數/日 | 10 | 100 | 無限 |
| Vision OCR 頁數/月 | 5 | 100 | 500 |
| 單檔大小上限 | 10 MB | 50 MB | 200 MB |

#### 5.3 公告管理

- 建立 / 編輯 / 排程系統公告。
- 公告類型：一般通知、系統維護預告、新功能上線、緊急警告。
- 顯示方式：全站橫幅 (Banner) / 站內通知中心 / Email 推播。

#### 5.4 Feature Flags

- 功能開關管理，支援漸進式上線與 A/B 測試。
- 範例 Flags：
  - `enable_notion_sync`：是否開放 Notion 同步功能。
  - `enable_socratic_tutor_v2`：新版 AI 教練是否上線。
  - `enable_b2b_dashboard`：B2B 管理後台是否可見。
- 支援依用戶比例 (%) 或特定用戶群組啟用。

#### 5.5 管理員帳號管理

- 新增 / 停用管理員帳號。
- 設定管理員角色（`super_admin` / `admin`）。
- 檢視管理員操作日誌（何時、誰、做了什麼操作）。

---

## 💾 資料庫 Schema 新增

```sql
-- 管理員角色表
CREATE TABLE admin_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('super_admin', 'admin')),
    permissions JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 管理操作審計日誌
CREATE TABLE admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 系統公告
CREATE TABLE system_announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(20) CHECK (type IN ('info', 'maintenance', 'feature', 'warning')),
    display_mode VARCHAR(20) CHECK (display_mode IN ('banner', 'notification', 'email')),
    is_active BOOLEAN DEFAULT true,
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feature Flags
CREATE TABLE feature_flags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_key VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT false,
    rollout_percentage INTEGER DEFAULT 0 CHECK (rollout_percentage BETWEEN 0 AND 100),
    target_user_ids UUID[] DEFAULT '{}',
    updated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 優惠碼
CREATE TABLE promo_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    discount_type VARCHAR(20) CHECK (discount_type IN ('percentage', 'fixed_amount', 'free_trial_days')),
    discount_value NUMERIC NOT NULL,
    applicable_plans VARCHAR(20)[] DEFAULT '{pro, ultra}',
    max_uses INTEGER,
    max_uses_per_user INTEGER DEFAULT 1,
    current_uses INTEGER DEFAULT 0,
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 退款申請
CREATE TABLE refund_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    transaction_id VARCHAR(200) NOT NULL,
    amount NUMERIC NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by UUID REFERENCES users(id),
    review_note TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 內容檢舉
CREATE TABLE content_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id UUID NOT NULL REFERENCES users(id),
    report_type VARCHAR(30) CHECK (report_type IN ('inappropriate', 'copyright', 'bug_report', 'other')),
    target_type VARCHAR(30) NOT NULL,
    target_id UUID NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'resolved', 'dismissed')),
    resolved_by UUID REFERENCES users(id),
    resolution_note TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引建議
CREATE INDEX idx_admin_audit_logs_admin_id ON admin_audit_logs(admin_id);
CREATE INDEX idx_admin_audit_logs_created_at ON admin_audit_logs(created_at DESC);
CREATE INDEX idx_admin_audit_logs_action ON admin_audit_logs(action);
CREATE INDEX idx_system_announcements_active ON system_announcements(is_active, starts_at, ends_at);
CREATE INDEX idx_feature_flags_key ON feature_flags(flag_key);
CREATE INDEX idx_refund_requests_status ON refund_requests(status);
CREATE INDEX idx_content_reports_status ON content_reports(status);
```

---

## 💻 技術面/實作建議

- **獨立路由群組**：所有 `/super-admin/*` 路由應在 Next.js 中使用獨立的 Layout，與用戶端完全隔離，避免被 Crawler 或一般用戶意外發現。
- **中介層權限驗證**：在 API Gateway 或 Express/NestJS Middleware 中統一攔截，驗證 JWT 內的 `role` 欄位，非 `super_admin` / `admin` 一律回傳 `403 Forbidden`。
- **審計日誌不可刪除**：`admin_audit_logs` 表應設定為 append-only，任何管理操作（包含查看敏感資料）都必須留下紀錄。
- **敏感操作二次驗證**：刪除帳號、調整訂閱、核准退款等高風險操作，應要求管理員再次輸入密碼或 OTP 確認。
- **圖表元件**：建議採用 Recharts 或 Chart.js 繪製營運儀表板圖表，搭配 SWR / React Query 做資料快取與即時更新。
- **Feature Flags 快取**：Flag 狀態應快取於 Redis (Memorystore)，避免每次 API 請求都查詢資料庫。讀取路徑：Redis → Cloud SQL (Fallback)。

---

## 📅 開發優先級與對應里程碑

| 優先級 | 模組 | 建議里程碑 | 原因 |
|:---:|------|:---:|------|
| 🔴 P0 | RBAC 權限架構 + 管理員登入 | M6 (9月) | 與 Firebase Auth 整合一起建置，打好權限基礎 |
| 🔴 P0 | 營運儀表板（基礎版） | M7 (10月) | 上線前必須具備系統監控能力 |
| 🟡 P1 | 用戶管理 + 停權機制 | M7 (10月) | 上線後立即需要處理用戶問題的能力 |
| 🟡 P1 | 財務看板 + 退款審核 | M8 (11月) | 營收追蹤是商業模式優化的核心基礎 |
| 🟢 P2 | 內容審核 + AI 濫用監控 | M8 (11月) | 用戶量成長後的安全防線 |
| 🟢 P2 | 系統設定 + Feature Flags | M9 (12月) | 進入 B2B 階段前完善動態控制能力 |
| 🟢 P2 | 優惠碼 + 公告管理 | M9 (12月) | 配合行銷活動與營運需求 |
