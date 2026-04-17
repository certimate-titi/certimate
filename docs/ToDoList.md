# 代辦項目及處理程序紀錄

## 待辦事項

### 用戶管理前端修復（P1）
- [ ] 用戶詳情頁載入驗證 — 前端頁面已實作，需端到端測試確認 API 回應格式是否正確
- [ ] 新增「發送通知」按鈕至 `users/[userId]/client.tsx` — 後端 API `POST /admin/users/{userId}/notify` 已存在
- [ ] 停權後自動發送通知信 + 按鈕動態切換（active 顯示「停權」、suspended 顯示「恢復」）

### Prompt 模板前端修復（P1）
- [ ] 編輯表單新增 model 下拉選單（gemini-2.5-flash / claude-3.5-sonnet / gpt-4o 等）— 後端 PATCH API 已支援 model 欄位
- ~~prompt無法編輯~~ → ✅ 已確認可編輯（system_prompt / user_prompt / temperature）

### RAG 物理級跳轉完善（P2）
- [ ] resource_chunks metadata 加入 anchor_id 欄位
- [ ] knowledge_map source API 返回 highlight_line / highlight_chars

### 向量快取機制（P2）
- [ ] Redis 快取最近 1000 個查詢向量（TTL 24h），節省 Voyage 配額 15-20%

### 系統設定頁面重組（P3）
- [ ] 將過於龐雜的 6 Tab 設定頁拆分（AI 配置 / 營運管理 / 開發配置 / 帳號管理）

---

## 完成事項

### ✅ 12. RAG 資料流程差異分析 + 平台管理功能審查 — 完成於 2026-04-17

**RAG 資料流程_修正版 vs 實作差異**（整體完成度 85-90%）：
- ✅ 結構化提煉（6 章心智圖）、動態增刪、權威優先、二階段檢索、Mastery 引擎、配額控制 — 完全實現
- ⚠️ 物理級跳轉（anchor_id 缺失）、向量快取（未實作）— 需補強

**平台管理功能審查結果**：
- ✅ 儀表板、財務、內容審核、審計日誌、成本監控 — 功能完整
- ⚠️ 用戶管理：詳情頁已實作但需驗證、缺「發送通知」按鈕、停權未自動寄信
- ⚠️ Prompt 模板：編輯功能已可用（非「無法編輯」）、缺 model 下拉選單
- ⚠️ 系統設定頁面 6 Tab 過於龐雜，建議拆分

*詳細處理紀錄：`docs/todo-processing-2026-04-17T14-34-13.md`*

### ✅ 11. Feature 32 節點練習模式 + Feature 33 成本監控中心 — 完成於 2026-04-15

**完成範圍**（Feature 32 全部、Feature 33 全部）：

**Feature 32 — 節點練習模式（`32-節點練習模式.feature`）**：
- `backend/app/api/practice.py`：練習題查詢 + 作答 + 進度傳播 3 支 API
- `backend/tests/features/steps/practice/`：完整 step definitions（Given/When/Then）
- `frontend/lib/api/services.ts`：新增 `getNodePracticeQuestions` / `submitPracticeAnswer` 前端 API

**Feature 33 — 成本監控中心（`33-成本監控中心.feature`）**：
- `backend/app/models/ai_usage_ledger.py`：AI 呼叫 token 級用量明細
- `backend/app/models/budget_config.py`：預算設定（四個 scope：AI_ANTHROPIC / AI_GEMINI / AI_VOYAGE / GCP_TOTAL）
- `backend/app/models/budget_alert_log.py`：預算告警日誌
- `backend/alembic/versions/048_add_cost_monitor_tables.py`：Migration 048
- `backend/alembic/versions/049_add_embedding_provider_metadata.py`：Migration 049（Voyage 多 provider 支援）
- `backend/alembic/versions/050_add_gcp_budget_sync_fields.py`：Migration 050（GCP Native Budget 同步欄位）
- `backend/app/repositories/ai_usage_repository.py`
- `backend/app/repositories/budget_config_repository.py`
- `backend/app/repositories/budget_alert_log_repository.py`
- `backend/app/services/cost_monitor_service.py`：成本總覽 + 趨勢圖
- `backend/app/services/budget_service.py`：預算告警觸發 + 功能降級 + 解除停用
- `backend/app/services/gcp_billing_service.py`：GCP BigQuery Billing Export 查詢
- `backend/app/services/gcp_budget_sync_service.py`：GCP Native Budget API 單向同步
- `backend/app/services/voyage_quota_service.py`：Voyage embedding 配額鎖 + 等待佇列
- `backend/app/api/cost_monitor.py`：成本監控 REST API（super_admin 限定）
- `backend/app/core/permissions.py`：`require_super_admin` 依賴注入
- `backend/app/middleware/`：AI Budget 降級 Middleware
- `backend/tests/features/steps/cost_monitor/`：完整 step definitions（Given/When/Then）
- `frontend/app/super-admin/cost-monitor/`：成本監控前端頁面
- `frontend/types/cost-monitor.ts`：前端型別定義
- `project/specs/entity/erm.dbml`：新增 ai_usage_ledger / budget_config / budget_alert_log 三張表 + PENDING_BUDGET_RECOVERY enum + embedding_provider / embedding_model 欄位

**待手動執行：**
- `alembic upgrade head`（migration 048 / 049 / 050）
- 設定 `GCP_BILLING_PROJECT_ID`、`GCP_BILLING_DATASET`、`GCP_BILLING_EXPORT_TABLE`（GCP BigQuery）
- 設定 `GCP_BUDGET_PARENT`（billingbudgets.googleapis.com 同步用）
- BDD 測試驗收（Feature 32 + Feature 33）

*詳細處理紀錄：`docs/todo-processing-2026-04-15T09-00-00.md`*

---

### ✅ 10. LLM 防火牆 + 任務佇列隔離 — 完成於 2026-04-11

**完成範圍**（階段二 1/1、階段三 1/1 剩餘項目）：

**新增/修改檔案：**
- `backend/app/core/llm_firewall.py`：LLM 防火牆（雙層防護：規則引擎 + Llama Guard 客戶端；多租戶感知；OTel 整合；FastAPI exception handler）
- `backend/app/worker.py`：Celery 優先權佇列配置（paid_priority / standard / background / celery 四佇列；task_routes 路由規則；kombu Queue 定義）
- `backend/app/tasks/document_processing.py`：文件解析非同步任務（parse_document_task / ocr_image_task / transcribe_audio_task；方案 → 佇列映射 helper）
- `backend/app/tasks/__init__.py`：新增 document_processing 模組 import
- `backend/app/main.py`：註冊 PromptInjectionError 例外處理器

**待手動執行：**
- LLM 防火牆：設定環境變數 `LLAMA_GUARD_URL`（Llama Guard 推理服務）、`LLAMA_GUARD_API_KEY`
- 佇列隔離：啟動各佇列專屬 Worker（`celery -A app.worker worker -Q paid_priority -c 4`）

**功能說明：**
- LLM 防火牆：規則引擎（即時，零延遲）偵測 Prompt Injection / Jailbreak / 跨租戶攻擊 / PII 萃取；Llama Guard（語意層）可選接入；熔斷器防止服務不穩定；OTel span 記錄威脅事件
- 佇列隔離：B2B + ULTRA_1599 → `paid_priority`；PRO → `standard`；FREE → `background`；方案 → 佇列映射由 `dispatch_*()` helper 自動處理

*詳細處理紀錄：`docs/todo-processing-2026-04-11T09-00-00.md`*

---

### ✅ 9. 基礎設施安全層：欄位加密 + OTel + 限流 + 語意快取 — 完成於 2026-04-09

**完成範圍**（階段二 1/2、階段三 2/3、階段四 1/1）：

**新增/修改檔案：**
- `backend/app/core/field_encryption.py`：Fernet 對稱加密服務（欄位加密、金鑰輪替）
- `backend/app/models/answer.py`：Answer 模型新增 `is_answer_encrypted`、`encrypted_at`、便利方法
- `backend/alembic/versions/041_add_answer_encryption_flag.py`：Migration 041
- `backend/app/core/telemetry.py`：OpenTelemetry 初始化（FastAPI + SQLAlchemy instrument）
- `backend/app/core/rate_limit.py`：多租戶 Token Bucket Middleware（Redis + 記憶體 Fallback）
- `backend/app/services/semantic_cache_service.py`：語意快取服務（Redis + 記憶體 Fallback）
- `backend/app/main.py`：整合 OTel setup + RateLimitMiddleware

**待手動執行：** `alembic upgrade head`（migration 041）；設定 `FIELD_ENCRYPTION_KEY`、`REDIS_URL`、`OTEL_ENABLED=true`

**未完成項目**（需外部基礎設施）：
- 階段二：LLM 防火牆（Llama Guard）
- 階段三：Celery 任務佇列隔離

*詳細處理紀錄：`docs/todo-processing-2026-04-09T09-00-00.md`*

---

### ✅ 8. 資料庫保護與管理（階段一/二部分/四）— 完成於 2026-04-08

**完成範圍**（階段一 4/5、階段二 2/4、階段四 3/3、Feature 檢查）：

**新增/修改檔案：**
- `backend/alembic/versions/038_add_tenants_and_tenant_id.py`：tenants 表 + 7 張業務表 tenant_id + RLS
- `backend/alembic/versions/039_add_hnsw_index_on_embedding.py`：HNSW 向量索引（取代 IVFFlat）
- `backend/app/core/deps.py`：JWT tenant_id DI + `get_tenant_id()`、`get_current_user_with_tenant()`、`set_rls_tenant()`
- `backend/app/core/security.py`：SSRF 防護 utility（黑名單 IP + 白名單域名 + YouTube 專用驗證）
- `backend/app/scripts/purge_tenant_data.py`：租戶資料退場清除腳本（dry-run + GCS 支援）
- `backend/tests/features/environment.py`：BDD 測試環境隔離（TEST_TENANT_ID + _seed_base_data）
- `project/features/31-多租戶安全與資料隔離.feature`：新增 Feature 規格（6 Rules）
- `backend/tests/features/31-多租戶安全與資料隔離.feature`：同步 Feature 測試
- `project/specs/entity/erm.dbml`：新增 tenants 表、tenant_id 欄位、HNSW 索引

**待手動執行：** `alembic upgrade head`（migration 038、039）

**未完成項目**（需外部基礎設施）：
- 階段二：LLM 防火牆（Llama Guard）、欄位級加密
- 階段三：Redis 語意快取、限流、Celery 佇列
- 階段四：OpenTelemetry 全鏈路追蹤

*詳細處理紀錄：`docs/todo-processing-2026-04-08T09-00-00.md`*

---

### ✅ 1. 題目分類 — 完成於 2026-04-02
考古題分析時需進行該科目的題目分類佔比讓模擬考試能有不同難度以及更符合考試趨勢
- 記憶類別 / 理解類別 / 應用類別 / 分析類別 / 評估類別 / 創造類別（Bloom's Taxonomy）

**處理結果**：
- 更新 `project/specs/entity/erm.dbml`：新增 `bloom_category` enum、`questions.bloom_category`、`exams.bloom_distribution`
- 新增 `project/features/18-題目分類與考試趨勢分析.feature`

**待手動執行**：Alembic migration 017、ORM 模型更新、前端圖表

---

### ✅ 2. 考古題爬蟲 — 完成於 2026-04-02
依照台灣證照市場概況與題庫公開程度建立爬蟲 SKILL，優先級：金融 🏆A > 不動產 🏆A > iPAS 🥈B

**處理結果**：
- 新增 `.claude/skills/exam-crawler/SKILL.md`（包含爬蟲策略、Bloom 分類 Prompt、標準輸出 JSON schema）

**待手動執行**：實作 `backend/scripts/crawlers/` 爬蟲腳本、管理後台匯入 API

---

*詳細處理紀錄：`docs/todo-processing-2026-04-02T10-00-00.md`*

---

### ✅ 7. Prompt 模板管理 — BDD 測試與前後端實作 — 完成於 2026-04-07

**處理結果：**
- 更新 `backend/app/models/prompt_template.py`：新增 `PromptTemplateV2`、`PromptTemplateVersion`、`PromptAbTest`
- 新增 `backend/alembic/versions/037_create_prompt_templates_v2.py`：建立三張新表
- 新增 `backend/app/repositories/prompt_template_repository.py`
- 新增 `backend/app/services/prompt_template_service.py`（含 A/B 分流邏輯）
- 新增 `backend/app/api/prompt_template.py`（admin + internal 路由）
- 新增 `backend/tests/features/steps/prompt_template/`（完整 step definitions）
- 移除 Feature 30 的 `@ignore @command` 標籤（進入 Green 階段）
- 新增 `backend/app/scripts/seed_prompts.py`（YAML frontmatter 解析 + 同步）
- 新增前端頁面：`/super-admin/prompt-templates/`（列表 + 編輯 + 版本歷史 + A/B 測試）

**待手動執行**：`alembic upgrade head`、BDD 測試驗收、首次 seed 執行

*詳細處理紀錄：`docs/todo-processing-2026-04-07T22-14-10.md`*

---

### ✅ 3. Edu 學生訂閱衝突處置 — 完成於 2026-04-06

Edu 學生若已有個人訂閱方案（PRO_199/PRO_PLUS_399），被機構指派 EDU 後的處置方式。

**決議：** 個人訂閱自動「暫停計費」（suspended），EDU 期間以 EDU 方案權益為主；EDU 結束後個人訂閱自動恢復，下次扣款日從恢復日重算。

**處理結果：**
- 更新 `project/features/08-訂閱管理.feature`：新增「EDU 學生既有訂閱衝突處置」章節（4 個 scenarios）

---

### ✅ 4. Edu 學生邀請信密碼設定流程 — 完成於 2026-04-06

Edu 學生收到邀請信點擊連結後，應先進入密碼設定頁，再完成帳號啟用。

**決議：** 邀請連結導向 `/invite/setup-password?token={token}`，密碼設定完成後帳號啟用並導向儀表板。Token 有效期 72 小時。

**處理結果：**
- 更新 `project/features/01-身分驗證.feature`：新增「EDU 學生邀請啟用流程」章節（5 個 scenarios）

---

### ✅ 6. Prompt 模板管理 — DBML + Feature 規格 — 完成於 2026-04-06

將 17 個 LLM Prompt 模板納入 DB 管理，支援版本控制、回滾、A/B 測試、Seed 同步。

**處理結果：**
- 更新 `project/specs/entity/erm.dbml`：新增 `prompt_category`、`ab_test_status` enum + `prompt_templates`、`prompt_template_versions`、`prompt_ab_tests` 3 張表
- 新增 `project/features/30-Prompt模板管理.feature`：10 個 Rule、20+ 個 Example（權限、CRUD、版本管理、回滾、A/B 測試、Seed 同步、by-plan 支援）
- 同步至 `backend/tests/features/30-Prompt模板管理.feature`

**前置完成項：**
- `project/03_Research_and_Development/03_Prompt_Templates/` 資料夾（17 個模板 .md 檔 + README）

**待手動執行：** Alembic migration、ORM 模型、seed 腳本 (`app.scripts.seed_prompts`)、管理後台 UI

---

### ✅ 5. feature_conflicts.md 決議事項處理 — 完成於 2026-04-06

feature_conflicts.md 中標註需 /titi-commander 評估的衝突項目（衝突1次數限制、衝突4更新時機、衝突7功能確認、問題8雙條件、問題9術語、問題10作答觸發）。

**處理結果：**
- 更新 `docs/feature_conflicts.md`：補全 6 個 CEO 決議
- 詳見 `docs/todo-processing-2026-04-06T01-08-22.md`
