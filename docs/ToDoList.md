# 代辦項目及處理程序紀錄

## 待辦事項

幫我檢查目前的資料庫和後端是否有類似以下的資料庫保護和管理，若有缺失則幫我優化系統。
同時檢查feature file。
### 階段一：資料庫底層與安全性（基礎設施）
* **[ ] 資料表 Schema 埋點：** 在所有業務相關資料表（Documents, Chunks, Quizzes 等）新增 `tenant_id` 欄位（UUID, 可為 Null）。
* **[ ] 預設租戶設定：** 建立第一個預設租戶 `public_b2c`，並確保現有散客資料皆歸屬此 ID。
* **[ ] 實作 RLS (Row Level Security)：** 在 PostgreSQL 針對 `personal_vectors` 等敏感資料表啟用 RLS，強制執行 `tenant_id` 物理隔離。
* **[ ] 向量索引優化：** 針對 `embedding` 欄位建立 HNSW 索引，並確保查詢時包含 `tenant_id` 作為過濾條件（Pre-filtering）。
* **[ ] SSRF 安全防護：** 實作 Egress Proxy，針對用戶輸入的 URL 進行出站流量隔離，防止內網探測攻擊。

### 階段二：後端邏輯與認證（核心機制）
* **[ ] JWT Token 擴充：** 在 JWT Payload 中新增 `tenant_id` 宣告（Claims）。
* **[ ] 依賴注入 (DI) 實作：** 在 FastAPI 撰寫全域 Dependency，自動從 Token 提取 `tenant_id` 並注入資料庫 Session。
* **[ ] LLM 防火牆配置：** 導入意圖過濾器（如 Llama Guard），防止針對特定租戶題庫的 Prompt Injection 攻擊。
* **[ ] 欄位級加密：** 針對 `Student_Answers` 表中的成績與個資實作應用層加密。

### 階段三：效能與資源管理（商業營運）
* **[ ] 語意快取 (Semantic Cache)：** 建立以 `tenant_id + semantic_hash` 為鍵值的 Redis 快取，降低重複生成考題的 API 成本。
* **[ ] 多租戶限流 (Rate Limiting)：** 實作 Redis Token Bucket，依據租戶等級（B2C/B2B）設定不同的 QPS 限制。
* **[ ] 任務佇列隔離 (Queue Prioritization)：** 設定 Celery 優先權佇列，確保付費租戶的解析任務（OCR/STT）優先執行。

### 階段四：可觀測性與退場機制（維護與合規）
* **[ ] 全鏈路追蹤：** 導入 OpenTelemetry，確保每個請求的 `Trace_ID` 能追蹤跨服務的 `tenant_id` 資源消耗。
* **[ ] 租戶資料抹除腳本 (Data Purge)：** 撰寫自動化清理程式，當企業租戶解約時，能物理性刪除該 `tenant_id` 關聯的向量與 S3 檔案。
* **[ ] BDD 測試環境隔離：** 配置 `is_test` 標籤與自動化 Teardown 邏輯，防止測試資料污染正式環境。

這份清單特別強調了 **RLS** 與 **HNSW 索引** 的結合，這是解決大規模多租戶向量檢索效能的標準做法。完成前兩個階段後，系統就具備了最基礎的商用安全性。

---

## 完成事項

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
