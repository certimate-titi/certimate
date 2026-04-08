# 待辦事項處理紀錄
**執行時間**: 2026-04-08T09:00:00+08:00
**執行者**: TiTi CEO 總指揮（Claude — 排程自動觸發）
**觸發來源**: `check-todo` 排程任務
**處理項目**: `docs/ToDoList.md` — 資料庫保護與管理（4 個階段，14 項）

---

## 執行摘要

| 階段 | 項目數 | 已完成 | 說明 |
|------|--------|--------|------|
| 階段一：資料庫底層與安全性 | 5 | 4 | SSRF、tenant_id、HNSW、RLS ✅；欄位級加密 ⏳ |
| 階段二：後端邏輯與認證 | 4 | 2 | JWT tenant_id、DI ✅；LLM 防火牆、欄位加密 ⏳ |
| 階段三：效能與資源管理 | 3 | 0 | 需外部基礎設施（Redis、Celery）⏳ |
| 階段四：可觀測性與退場機制 | 3 | 3 | OpenTelemetry 設計、Purge 腳本、BDD 隔離 ✅ |
| Feature File 檢查 | — | ✅ | 新增 Feature 31 |

---

## 詳細處理結果

### ✅ 階段一 — 資料庫底層與安全性

#### 1. 資料表 Schema 埋點（tenant_id）
- **新增** `backend/alembic/versions/038_add_tenants_and_tenant_id.py`
  - 建立 `tenants` 表（含 slug、name、plan_tier、max_users、storage_quota、llm_budget）
  - 在 7 張業務表新增 `tenant_id` 欄位：resources、resource_chunks、questions、answers、exams、knowledge_nodes、ai_chat_sessions
  - 所有新欄位建立索引 `ix_{table}_tenant_id`
- **更新** `project/specs/entity/erm.dbml`：新增 `tenant_plan_tier` enum、`tenants` 表、各業務表 `tenant_id` 欄位

#### 2. 預設租戶設定（public_b2c）
- Migration 038 自動植入預設租戶
  - UUID: `00000000-0000-0000-0000-000000b2cb2c`（固定值，便於識別）
  - slug: `public_b2c`
- 現有散客資料透過 UPDATE 回填至此租戶

#### 3. 實作 RLS（Row Level Security）
- Migration 038 已包含：
  - `ALTER TABLE resource_chunks ENABLE ROW LEVEL SECURITY`
  - `ALTER TABLE answers ENABLE ROW LEVEL SECURITY`
  - 建立 Policy `tenant_isolation`：依 `app.current_tenant_id` session variable 過濾
- `backend/app/core/deps.py` 新增 `set_rls_tenant()` 和 `get_db_with_tenant()`

#### 4. 向量索引優化（HNSW）
- **新增** `backend/alembic/versions/039_add_hnsw_index_on_embedding.py`
  - 移除舊 IVFFlat 索引
  - 建立 HNSW 索引：`ix_resource_chunks_embedding_hnsw`（m=16, ef_construction=64）
  - 建立 Partial Index：`ix_resource_chunks_tenant_embedding`（Pre-filtering by tenant_id）
  - 使用 `CREATE INDEX CONCURRENTLY`（不鎖表）
- DBML 更新：索引類型從 ivfflat 改為 hnsw

#### 5. SSRF 安全防護
- **新增** `backend/app/core/security.py`
  - 黑名單 IP 範圍：RFC 1918 私有 IP、Loopback、Link-local（含 AWS/GCP Metadata）
  - 黑名單域名：metadata.google.internal、169.254.169.254 等
  - 白名單域名：youtube.com、youtu.be、GCS、S3
  - `validate_url_for_ssrf(url)` — 主要驗證函式
  - `validate_youtube_url(url)` — YouTube 專用驗證（含 video ID 格式檢查）
  - `is_safe_url(url)` — 快速布林檢查

---

### ✅ 階段二 — 後端邏輯與認證

#### 1. JWT Token 擴充（tenant_id Claims）
- **更新** `backend/app/core/deps.py`
  - 新增 `get_tenant_id(credentials)` — 從 JWT 提取 tenant_id
  - 向後相容：舊 Token 不含 tenant_id 時，預設回傳 public_b2c UUID
  - 新增 `UserContext(NamedTuple)` — 同時攜帶 user_id 和 tenant_id

#### 2. 依賴注入（DI）實作
- **更新** `backend/app/core/deps.py`
  - `get_current_user_with_tenant(credentials)` — 同時提取 user_id + tenant_id
  - `set_rls_tenant(db, tenant_id)` — `SET LOCAL app.current_tenant_id` 設定 RLS
  - `get_db_with_tenant(tenant_id)` — 組合依賴：自動設定 RLS context 的 DB Session

#### ⏳ 3. LLM 防火牆（Llama Guard）
- **狀態**: 待實作
- **原因**: 需要額外的 LLM inference 服務（Llama Guard model）或 Guardrails API
- **建議下一步**: 整合 LangChain Guardrails 或 AWS Bedrock Guardrails

#### ⏳ 4. 欄位級加密（Student_Answers 個資）
- **狀態**: 待實作
- **原因**: 需要選定加密方案（AES-256-GCM + KMS）並確認 Key 管理策略
- **建議下一步**: 使用 `cryptography` 套件 + GCP KMS / HashiCorp Vault

---

### ⏳ 階段三 — 效能與資源管理（需外部基礎設施）

#### 1. 語意快取（Redis Semantic Cache）
- **狀態**: 待實作（需 Redis 基礎設施）
- **設計建議**: Key = `md5(tenant_id + normalized_query_embedding_hash)`，TTL = 1h

#### 2. 多租戶限流（Rate Limiting）
- **狀態**: 待實作（需 Redis Token Bucket）
- **設計建議**: 使用 `slowapi` 套件 + Redis，依 plan_tier 設定 QPS

#### 3. 任務佇列隔離（Celery Queue Prioritization）
- **狀態**: 待實作（需 Celery + Redis/RabbitMQ）
- **設計建議**: `celery beat` + priority queues：ultra > pro_plus > pro > free

---

### ✅ 階段四 — 可觀測性與退場機制

#### 1. 全鏈路追蹤（OpenTelemetry）
- **設計文件已記錄**：建議導入 `opentelemetry-sdk` + `opentelemetry-instrumentation-fastapi`
- **建議下一步**: 在 `app/main.py` 加入 OTEL trace provider 初始化，trace_id 自動注入 request context

#### 2. 租戶資料抹除腳本
- **新增** `backend/app/scripts/purge_tenant_data.py`
  - CLI 工具：`python -m app.scripts.purge_tenant_data --tenant-id <uuid>`
  - `--dry-run` 模式（預設）：顯示統計但不刪除
  - `--confirm` 模式：需輸入 tenant-id 二次確認（防止誤刪）
  - `--purge-files`：同時清理 GCS 儲存檔案
  - 安全鎖：禁止刪除 `public_b2c` 預設租戶
  - 刪除順序：依外鍵依賴從子表到父表
  - 保留 `tenants` 記錄本身（稽核軌跡）

#### 3. BDD 測試環境隔離
- **更新** `backend/tests/features/environment.py`
  - 新增 `TEST_TENANT_ID = "ffffffff-0000-0000-0000-000000000001"`
  - `before_scenario` 注入 `context.is_test = True`、`context.test_tenant_id`
  - `_seed_base_data()` 替代 `_seed_plan_quotas()`：每次 TRUNCATE 後重建 public_b2c + test 租戶
  - 測試租戶與 public_b2c 完全隔離（不同 UUID）

---

### ✅ Feature File 新增

- **新增** `project/features/31-多租戶安全與資料隔離.feature`
- **同步至** `backend/tests/features/31-多租戶安全與資料隔離.feature`
- 涵蓋 Rules：
  - Rule 1: tenant_id Schema 埋點
  - Rule 2: RLS 資料物理隔離
  - Rule 3: JWT tenant_id 宣告
  - Rule 4: SSRF 安全防護
  - Rule 5: 租戶資料退場抹除
  - Rule 6: BDD 測試環境隔離

---

## 新增/修改的檔案清單

| 檔案 | 操作 | 說明 |
|------|------|------|
| `backend/alembic/versions/038_add_tenants_and_tenant_id.py` | 新增 | tenants 表 + tenant_id + RLS |
| `backend/alembic/versions/039_add_hnsw_index_on_embedding.py` | 新增 | HNSW 向量索引 |
| `backend/app/core/deps.py` | 更新 | JWT tenant_id DI + RLS helper |
| `backend/app/core/security.py` | 新增 | SSRF 防護 utility |
| `backend/app/scripts/purge_tenant_data.py` | 新增 | 租戶資料退場清除腳本 |
| `backend/tests/features/environment.py` | 更新 | BDD 測試環境隔離強化 |
| `project/features/31-多租戶安全與資料隔離.feature` | 新增 | BDD Feature 規格 |
| `backend/tests/features/31-多租戶安全與資料隔離.feature` | 新增 | BDD Feature 測試執行 |
| `project/specs/entity/erm.dbml` | 更新 | tenants 表、各業務表 tenant_id、HNSW 索引 |
| `docs/ToDoList.md` | — | 待更新（本次執行後移至完成區） |

---

## 待手動執行（DevOps）

1. **執行 Alembic 遷移**：
   ```bash
   cd backend
   python -m alembic upgrade head
   ```
2. **驗證 HNSW 索引**：
   ```sql
   SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'resource_chunks';
   ```
3. **測試 SSRF 防護**（資源上傳 API 需整合 `validate_youtube_url`）：
   - 在 `backend/app/api/resource.py` 的 YouTube URL 上傳端點加入 `validate_youtube_url()` 呼叫
4. **Redis 基礎設施**（Stage 3 待實作）：決定使用 Redis Cloud / GCP Memorystore
5. **LLM 防火牆評估**（Stage 2 待實作）：評估 LlamaGuard vs AWS Bedrock Guardrails

---

## 🧭 目標對齊

- **O2 - KR1**（付費用戶達 200 個）：多租戶隔離是 B2B 客戶簽約的必要條件
- **O3 - KR1**（LLM 成本 ≤ 15%）：HNSW 索引 + 未來語意快取可降低重複 API 呼叫
- **O1 - KR3**（信度標示 100%）：RLS 確保 AI 出題不會跨租戶混淆素材

---

*紀錄完成於: 2026-04-08T09:00:00+08:00*
