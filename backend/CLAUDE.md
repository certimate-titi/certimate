# CLAUDE.md — Backend

## 快速啟動

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --reload          # API server :8000
.venv/bin/python -m behave tests/features/ --tags=~@ignore  # BDD 全套
```

虛擬環境：**`.venv/bin/python`（Python 3.13）**。需要 Docker（Testcontainers 自動啟 PostgreSQL 15 + pgvector）。

## 現況數字（2026-04-23）

| 項目 | 數量 |
|------|------|
| API Router 模組 | 41 |
| Service | 75 |
| Repository | 18 |
| ORM Model | 52 |
| Pydantic Schema 模組 | 3（auth, exam_import, resource） |
| Alembic Migration | 001–070 |
| CLI 腳本 | 14 |
| 爬蟲腳本 | 13 |
| BDD Feature 檔 | 49 |
| BDD Step 子領域 | 47 |
| 歷史考古題 JSON | 455 檔 / 7,992+ 題 |

## 架構分層

```
FastAPI Router (app/api/)
      ↓
Service Layer (app/services/)
      ↓
Repository Layer (app/repositories/)
      ↓
SQLAlchemy ORM (app/models/)
      ↓
PostgreSQL 15 + pgvector
```

## 重要路徑

| 路徑 | 說明 |
|------|------|
| `app/main.py` | FastAPI 入口，註冊 41 個 router |
| `app/core/config.py` | Settings（DB、JWT、AI API keys、RAG 參數） |
| `app/core/deps.py` | DI：`get_db()` / `get_current_user_id()` / `get_db_with_tenant()` / `set_rls_tenant()` |
| `app/core/security.py` | SSRF 防護、URL 白名單 |
| `app/api/` | 所有 endpoint（prefix: `/api/v1`） |
| `app/models/` | 52 個 ORM model |
| `app/services/` | 75 個業務 service |
| `app/repositories/` | 18 個 repository |
| `app/schemas/` | Pydantic schemas |
| `app/scripts/` | CLI 工具 |
| `alembic/versions/` | 001–070 |
| `scripts/crawlers/` | 考古題爬蟲（moex 系列 + IPAS + Claude PDF extract） |
| `data/historical_questions/` | 爬蟲產出 JSON + PDF |
| `tests/features/` | BDD feature + steps |
| `tests/features/environment.py` | Testcontainers 生命週期 |
| `tests/features/steps/__init__.py` | 所有 step 註冊點（新增 step 必須在此 import） |

## API Router 清單（41 個）

**認證 / 帳號**：auth, users, account, onboarding, subjects

**資源 / 解析**：resource, resource_library, resource_parse, knowledge_map, knowledge_merge

**考試 / 題目**：exam, ai_questions, practice, wrong_answer, wrong_answer_map, difficulty_progression, retirement, reverse_engineering

**考古題匯入**：exam_import, exam_import_async, exam_import_monitoring

**AI / Chat**：ai_chat, prompt_template

**商業 / 訂閱**：subscription, ecpay, pricing

**B2B / 機構**：b2b

**儀表板 / 學習**：dashboard, schedule, learning_journey, community, feedback, announcements

**平台管理**：admin, admin_finance, admin_moderation, admin_settings, admin_platform_subjects, anomaly

**成本監控**：cost_monitor

## ORM Model 分類（52 個）

- **核心**：User, Subject, SubjectCategory, Institution, Question, Answer, Exam, Resource, ResourceChunk, ResourceScaffold, ResourceParseJob, QuestionCandidate, SyllabusTopic, UserHiddenResource, SubjectDefaultResource
- **知識圖譜**：KnowledgeNode, NodeMastery, LearningJourney
- **AI**：AiChatSession / Message, AiCooldown, AiModelRouting, AiUsageLedger, PromptTemplate, PromptTemplateHistory
- **考古題**：HistoricalExam
- **匯入**：ImportTask, ImportAuditLog
- **財務**：Invoice, Transaction, Refund, Coupon, PlanQuota, BudgetConfig, BudgetAlertLog
- **分析**：QuestionStat, UserUsage, WeeklyReport, DailyQuestProgress
- **管理**：AuditLog, SystemAnnouncement, FeatureFlag, ContentReport, Feedback
- **B2B**：InstitutionAssignment, StudentGroup, StudentGroupMember, EarlyWarningRule
- **維運**：AnomalyRecord, MaintenanceTask / Schedule / Notification
- **多租戶**：Tenant
- **知識合併 / 逆向工程**：MergeConflict, MergeHistory, ReverseEngineeringTask

## 學習鷹架 Pipeline（EPIC-035，2026-04 新增）

上傳資源觸發 `_process_resource_background`：
1. chunk + embedding + 知識樹（`DocumentProcessingService`）
2. **自動**建 `resource_parse_jobs` → `run_parse_job`（Gemini 2.5 Pro 多模態）
3. 寫入 `resource_scaffolds`（takeaway / elaborative / strategy）+ `question_candidates`（T2/T3）+ T1 題入 `questions`
4. T1 題用 Voyage embedding 映射到科目的 `knowledge_nodes`

MIME 自動依副檔名判定（pdf / md / txt / html / png / jpg / webp）。

## 考古題資料架構

```
questions ── exam_id ─────→ exams              (使用者考試 / AI 生成)
        └─── historical_exam_id → historical_exams (爬蟲匯入)

CHECK: exam_id IS NOT NULL OR historical_exam_id IS NOT NULL
```

匯入工具：`.venv/bin/python -m app.scripts.import_exam_questions --json-dir data/historical_questions`

## BDD 測試子領域（47 個）

account_settings, admin, admin_finance, admin_moderation, admin_settings, ai_gen, anomaly, auth, b2b, common_then, community, confidence_calibration, cost_monitor, coverage, dashboard, difficulty_progression, ecpay, edu_plan, exam, exam_import, exam_result, feedback, fup, knowledge_map, knowledge_merge, mcp_context, mcp_recommendation, mindmap_upgrade, mock_exam, onboarding, pomodoro, practice, pricing, prompt_template, question_retirement, resource, resource_lib, resource_parse, reverse_engineering, schedule, subject_fork, subscription, subscription_trial, subscription_upgrade, tenant_security, wrong_answer, wrong_answer_map

## Step Definition 組織

```
tests/features/steps/{subdomain}/
├── aggregate_given/   # Given — DB 實體建立
├── commands/          # When — HTTP API 呼叫
├── aggregate_then/    # Then — DB 狀態驗證
├── readmodel_then/    # Then — API 回應驗證
└── query/             # When — Query API（部分子領域）
```

**一檔一 step** 模式；新增後必須在 `steps/__init__.py` import。

## 測試 Context

```python
context.db_session      # SQLAlchemy Session
context.api_client      # FastAPI TestClient
context.jwt_helper      # JWT token 產生器
context.ids             # email → user_id 對照
context.memo            # 步驟暫存
context.last_response   # 最後 HTTP Response
```

## 常用指令

```bash
# 特定 feature
.venv/bin/python -m behave tests/features/01-身分驗證.feature --no-capture

# 新 Alembic migration（下一個 071）
.venv/bin/python -m alembic revision --autogenerate -m "desc" --rev-id 071

# 新環境 DB setup（baseline 跳過舊 migration）
.venv/bin/python -m alembic stamp 000
.venv/bin/python -m alembic upgrade head

# Seed Prompt 模板
.venv/bin/python -m app.scripts.seed_prompts

# 匯入考古題
.venv/bin/python -m app.scripts.import_exam_questions --json-dir data/historical_questions
```

## 關鍵環境變數

```
DATABASE_URL=postgresql+psycopg://...
JWT_SECRET_KEY=...
GEMINI_API_KEY=     # Secret Manager: gemini-api-key
ANTHROPIC_API_KEY=  # Secret Manager: anthropic-api-key
OPENAI_API_KEY=
VOYAGE_API_KEY=     # Secret Manager: voyage-api-key
FIREBASE_PROJECT_ID=certimate-titi
STORAGE_BACKEND=gcs
GCS_BUCKET=certimate-titi-data
GCP_BILLING_MODE=real
GCP_BILLING_EXPORT_DATASET=billing_export
```

## Service 層規範

- **新 Service 必須繼承 `BaseService`**（`app/services/base.py`）
- 優先用對應 Repository；若無，用 `BaseService` helper
- 回傳統一用 `self.ok()` / `self.error()`
- 禁止在 Service 中組 raw SQL

## AI SDK 使用規範

**全專案統一用 `google-genai`（新版）**，禁用 `google.generativeai`（舊版 / 雲端容器沒裝）：

```python
from google import genai
client = genai.Client(api_key=settings.GEMINI_API_KEY)
# files.upload + models.generate_content 是新 API
```

違規歷史：2026-04-22 `resource_parse_service` 用舊 SDK 導致雲端 parse job 全掛。

## 新 API 閘門（BDD 覆蓋硬性規定）

任何新 FastAPI endpoint 送 CTO Review 前必須附帶：
1. 至少 1 個 BDD Scenario 呼叫該 endpoint
2. 對應 Feature file 有 Given / When / Then
3. 成功情境 + 至少 1 個失敗情境（400/401/403/404/409/422）

**例外**：純 health check、debug-only（`include_in_schema=False`）、運維初始化端點（`/admin/seed-*` 等 6 個端點不納入前端覆蓋率統計）。

## 錯誤回應模式

```python
# Router 層 — 直接 raise
raise HTTPException(status_code=400, detail={"message": "錯誤"})

# Service 層 — 回 error dict，由 Router 的 _handle_result() 轉換
return {"error": True, "status_code": 400, "message": "錯誤"}
```

禁止在 Router 層 `return {"error": True, ...}` — 這不會設 HTTP status code。

## 科目隔離規則（不可違反）

知識節點必須嚴格隔離到所屬科目，禁止跨科目混入。

**禁止樣例**：
```python
# ❌ 用名稱前綴匹配拉入父科目
base_name = subject.name.split("（")[0].strip()
parent = db.query(Subject).filter(Subject.name == base_name).first()

# ❌ 用 parent_subject_id 拉父節點
if subject.parent_subject_id:
    subject_ids.append(subject.parent_subject_id)

# ❌ name[:6] 模糊匹配跨級抽題
name_filters = [HistoricalExam.exam_name.ilike(f'%{name[:6]}%')]

# ❌ 全域 fallback 從整題庫隨機抽
historical_questions = db.query(Question).filter(
    Question.historical_exam_id.isnot(None)
).all()
```

**正確**：
```python
subject_ids = [sid]                      # 只查自己
codes = subject.exam_subject_codes       # e.g. ["IPA114:114_ai_fundamentals_4th"]
```

**例外**：`ai_generation_service._get_exam_subject_codes()` 允許查父科目的 `exam_subject_codes`（出題映射，不涉節點顯示）。

## RLS Policy 規範

RLS policy 禁止依賴 `OR` 短路保護空字串 cast；必須用 `NULLIF` 包裝：

```sql
-- ❌ 易爆
current_setting('app.tenant_id') = '' OR tenant_id = current_setting('app.tenant_id')::uuid

-- ✅ 正確
tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
```

## 注意事項

- **Python 環境**：`.venv/bin/python`（3.13），不用系統 python3
- API 欄位 **snake_case**
- 訂閱 DB：`FREE` / `PRO` / `PRO_PLUS` / `ULTRA`；API 顯示：`FREE` / `PRO_199` / `PRO_PLUS_399` / `ULTRA_1599`
- Given 建 User 時欄位名稱是 `password_hash`（非 `hashed_password`）
- `use_step_matcher("re")` 後必須 restore 為 `"parse"`
- 新 step 必須在 `steps/__init__.py` import
