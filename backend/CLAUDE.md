# CLAUDE.md — Backend

## 快速啟動

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --reload          # API server at :8000
.venv/bin/python -m behave tests/features/ --tags=~@ignore  # BDD E2E 全套測試
```

虛擬環境：`.venv/bin/python`（Python 3.13）。需要 Docker（Testcontainers 自動啟動 PostgreSQL 15 + pgvector）。

## 現況數字（2026-04-08）

| 項目 | 數量 |
|------|------|
| API Router 模組 | 31 |
| ORM Model | 40 |
| Service | 48 |
| Repository | 15 |
| Schema | 3 模組 |
| Alembic Migration | 040 |
| BDD Feature 檔案 | 43 |
| BDD Step 子領域 | 37 |
| BDD Step 檔案 | ~250+ |
| 通過 Scenario | 497（20 失敗 / 217 error = 未實作 step） |
| 歷史考古題（已匯入 DB） | 7,992 題 / 395 科目 |

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
| `app/main.py` | FastAPI 入口，註冊 31 個 router |
| `app/core/config.py` | Settings 類（DB、JWT、AI API keys、RAG 參數） |
| `app/core/deps.py` | DI：`get_db()`, `get_current_user_id()`, `get_db_with_tenant()` |
| `app/core/security.py` | SSRF 防護、URL 白名單驗證 |
| `app/api/` | 所有 API endpoint（prefix: `/api/v1`） |
| `app/models/` | 40 個 SQLAlchemy ORM model |
| `app/services/` | 48 個業務邏輯 service |
| `app/repositories/` | 15 個資料庫存取 repository |
| `app/schemas/` | Pydantic schema（auth, resource） |
| `app/scripts/` | CLI 工具（import_exam_questions, purge_tenant_data, seed_prompts） |
| `alembic/versions/` | 001-040 migration 檔案 |
| `scripts/crawlers/` | 高普考爬蟲（moex_simple, auto_catalog_generator） |
| `data/historical_questions/` | 爬蟲產出 JSON + PDF |
| `tests/features/` | BDD .feature + steps |
| `tests/features/environment.py` | Testcontainers 生命週期 |
| `tests/features/steps/__init__.py` | 所有 step import（必須在此註冊） |

## API Router 清單（31 個）

auth, resource, knowledge-map, knowledge-merge, exams, ai-questions, wrong-answers, wrong-answer-map, subscriptions, schedule, b2b, resource-library, onboarding, admin, admin-finance, admin-moderation, admin-settings, dashboard, subjects, ecpay, feedback, community, anomaly, announcements, pricing, prompt-template, retirement, reverse-engineering, difficulty-progression, learning-journey, ai-chat

## ORM Model 分類（40 個）

- **核心**: User, Subject, SubjectCategory, Institution, Question, Answer, Exam, Resource, ResourceChunk
- **知識圖譜**: KnowledgeNode, NodeMastery, LearningJourney
- **AI**: AiChatSession, AiChatMessage, AiCooldown, AiModelRouting, PromptTemplate, PromptTemplateHistory
- **考古題**: HistoricalExam（考試目錄，含 exam_code/category_code/subject_code）
- **財務**: Invoice, Transaction, Refund, Coupon, PlanQuota
- **分析**: QuestionStat, UserUsage, WeeklyReport
- **管理**: AdminAuditLog, SystemAnnouncement, FeatureFlag, ContentReport, Feedback, FeedbackAttachment
- **B2B**: InstitutionAssignment, StudentGroup, StudentGroupMember, EarlyWarningRule
- **維運**: AnomalyRecord, MaintenanceTask, MaintenanceSchedule, MaintenanceNotification
- **多租戶**: Tenant
- **知識合併**: MergeConflict, MergeHistory, ReverseEngineeringTask

## 考古題資料架構

```
questions ─── exam_id ──────→ exams           (使用者考試，AI 生成題)
    │
    └─── historical_exam_id → historical_exams (爬蟲匯入考古題)

CHECK: exam_id IS NOT NULL OR historical_exam_id IS NOT NULL
```

- 已匯入 114 年初等考試 (1,833 題) + 高普考 (6,159 題) = 7,992 題
- JSON 來源：`data/historical_questions/{exam_code}/{category_code}/{subject_code}.json`
- 匯入工具：`.venv/bin/python -m app.scripts.import_exam_questions --json-dir data/historical_questions`

## BDD 測試子領域（37 個）

account_settings, admin, admin_finance, admin_moderation, admin_settings, ai_gen, anomaly, auth, b2b, community, confidence_calibration, dashboard, difficulty_progression, ecpay, edu_plan, exam, exam_result, feedback, fup, knowledge_map, knowledge_merge, mock_exam, onboarding, pomodoro, pricing, prompt_template, question_retirement, resource, resource_lib, reverse_engineering, schedule, subscription, subscription_trial, subscription_upgrade, tenant_security, wrong_answer, wrong_answer_map

## Step Definition 組織模式

```
tests/features/steps/{subdomain}/
├── aggregate_given/   # Given — DB 資料建立
├── commands/          # When — HTTP API 呼叫
├── aggregate_then/    # Then — DB 狀態驗證
├── readmodel_then/    # Then — API 回應驗證
└── query/             # When — Query API（部分子領域）
```

**一檔一 step 模式**。新增 step 後必須在 `steps/__init__.py` import。

## 測試 Context 物件

```python
context.db_session      # SQLAlchemy Session
context.api_client      # FastAPI TestClient
context.jwt_helper      # JWT token 產生器
context.ids             # Dict[str, str] — email → user_id 對照
context.memo            # Dict — 步驟間暫存資料
context.last_response   # 最後一次 HTTP Response
```

## 常用開發指令

```bash
# 執行特定 feature
.venv/bin/python -m behave tests/features/01-身分驗證.feature --no-capture

# 執行全部（排除 @ignore）
.venv/bin/python -m behave tests/features/ --tags=~@ignore

# 新增 Alembic migration（下一個編號 041）
.venv/bin/python -m alembic revision --autogenerate -m "description" --rev-id 041

# DB upgrade（既有環境）
.venv/bin/python -m alembic upgrade head

# DB setup（新環境 — 使用 baseline 跳過 40 步 migration）
.venv/bin/python -m alembic stamp 000
.venv/bin/python -m alembic upgrade head

# 重新產生 baseline（schema 變更後）
./scripts/squash_migrations.sh

# 匯入考古題
.venv/bin/python -m app.scripts.import_exam_questions --json-dir data/historical_questions

# 考古題爬蟲
python3 scripts/crawlers/moex_simple.py all --config scripts/crawlers/exam_catalog_complete.yaml

# Seed Prompt 模板
.venv/bin/python -m app.scripts.seed_prompts
```

## 關鍵設定（.env）

```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/certimate-api_dev
JWT_SECRET_KEY=your-secret
ANTHROPIC_API_KEY=     # Claude
OPENAI_API_KEY=        # GPT-4o
GEMINI_API_KEY=        # Gemini
VOYAGE_API_KEY=        # Embedding
FIREBASE_PROJECT_ID=certimate-titi
```

## Service 層架構規範

### 現狀（技術債）
- 47 個 service 中，僅 4 個正確使用 Repository 層（auth, knowledge_map, resource, retrieval）
- 33 個 service 直接 `self.db.query()` 繞過 Repository（歷史遺留）
- 4 個混用 Repository + 直接查詢
- 6 個純邏輯無 DB 存取

### 新程式碼規範（必須遵守）
1. **新 Service 必須繼承 `BaseService`**（`app/services/base.py`）
2. 優先使用對應的 Repository；若無 Repository，使用 `BaseService` 的 helper methods
3. 回傳格式統一使用 `self.ok()` / `self.error()` 而非自訂 dict
4. 不得在 Service 中直接 `import sqlalchemy` 構建 raw SQL

### 現有 Service 遷移優先序（可漸進）
1. **HIGH** — 涉及 RLS 的 service（exam_service, wrong_answer_service, mock_exam_service）
2. **MEDIUM** — 跨表操作多的 service（subscription_service, b2b_service）
3. **LOW** — 簡單 CRUD service（feedback_service, anomaly_service）

---

## 錯誤回應模式

API 層錯誤處理統一使用 `HTTPException`：

```python
# API 層（Router）— 直接 raise HTTPException
raise HTTPException(status_code=400, detail={"message": "錯誤訊息"})

# Service 層 — 回傳 error dict，由 API 層的 _handle_result() 轉換
return {"error": True, "status_code": 400, "message": "錯誤訊息"}
# API 層：return _handle_result(service_result)
```

不要在 API 層 `return {"error": True, ...}` — 這不會設定 HTTP status code。

---

## 科目隔離規則（不可違反）

**知識節點必須嚴格隔離到所屬科目，禁止跨科目混入。**

- 查詢知識節點時，只用當前科目的 `subject_id`，**絕對不可**向上查父科目或用名稱前綴匹配拉入其他科目的節點
- 例：「AI 應用規劃師（初級）」只能顯示初級自己的知識節點，不能混入「AI 應用規劃師」（父科目）的節點
- 考古題映射 `node_id` 時，只能映射到該科目自己的知識節點
- Seed 知識節點時，每個子科目（初級/中級）各自獨立建立節點樹，不共享父科目的節點

- **禁止 `Subject.first()` fallback** — 建立考試時，subject_id 必須從節點的 `subject_id` 取得，不得 fallback 到「DB 中第一個科目」

**已知違規模式（禁止使用）：**
```python
# ❌ 禁止：用名稱前綴匹配拉入父科目
base_name = subject.name.split("（")[0].strip()
parent = db.query(Subject).filter(Subject.name == base_name).first()
subject_ids.append(parent.id)

# ❌ 禁止：用 parent_subject_id 拉入父科目節點
if subject.parent_subject_id:
    subject_ids.append(subject.parent_subject_id)

# ✅ 正確：只查自己
subject_ids = [sid]
```

**考古題出題規則：**
```python
# ❌ 禁止：用 name[:6] 模糊匹配（會跨級抽題）
name_filters = [HistoricalExam.exam_name.ilike(f'%{name[:6]}%')]

# ❌ 禁止：全域 fallback（無科目過濾從全題庫隨機抽）
historical_questions = db.query(Question).filter(historical_exam_id.isnot(None)).all()

# ✅ 正確：用 exam_subject_codes 精確匹配
codes = subject.exam_subject_codes  # e.g. ["IPA114:114_ai_fundamentals_4th"]
```

**受影響的 Service（已修正，修改時需再次驗證）：**
- `knowledge_nav_service.py` — `get_nodes_by_subject()`
- `dashboard_service.py` — `_build_domain_strengths()`
- `exam_result_service.py` — `_build_domain_analysis()`
- `exam_service.py` — `submit_config()` 考古題抽題邏輯

**例外**：`ai_generation_service.py` 的 `_get_exam_subject_codes()` 允許查父科目的 `exam_subject_codes`，因為出題需要從父科目找考古題映射代碼，這不涉及知識節點顯示。

## 注意事項

- **Python 環境**：使用 `.venv/bin/python`（Python 3.13），**不要用系統 python3**（3.9 不相容）
- 所有 API 回應欄位使用 **snake_case**
- 訂閱方案 DB 儲存：`FREE` / `PRO` / `PRO_PLUS` / `ULTRA`
- 訂閱方案 API 顯示：`FREE` / `PRO_199` / `PRO_PLUS_399` / `ULTRA_1599`
- DBML SSOT: `project/specs/entity/erm.dbml`（42+ 張表）
- 新增 step 後務必在 `steps/__init__.py` 加入 import
- `use_step_matcher("re")` 後必須 restore 為 `use_step_matcher("parse")`
- Given 步驟中建立 User 時，欄位名稱是 `password_hash`（非 `hashed_password`）
- `ai_gen` 子領域的 step 大多與 `exam` 重複，已在 `__init__.py` 中僅保留 unique 的 `historical_mode`
- 多租戶：RLS 啟用於 `resource_chunks` 和 `answers`，tenant_id 預設 public_b2c
