# CLAUDE.md — Backend

## 快速啟動

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload          # API server at :8000
python -m behave tests/features/ --tags=~@ignore  # BDD E2E 全套測試
```

需要 Docker（Testcontainers 自動啟動 PostgreSQL 15 + pgvector）。

## 現況數字（2026-04-01）

| 項目 | 數量 |
|------|------|
| API Router 模組 | 21 |
| ORM Model | 33 |
| Service | 30 |
| Repository | 13 |
| Schema | 3 模組 |
| Alembic Migration | 019 |
| BDD Feature 檔案 | 25 |
| BDD Step 子領域 | 24 |
| BDD Step 檔案 | ~200+ |
| 通過 Scenario | 280（0 失敗） |

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
| `app/main.py` | FastAPI 入口，註冊 21 個 router |
| `app/core/config.py` | Settings 類（DB、JWT、AI API keys、RAG 參數） |
| `app/core/deps.py` | DI：`get_db()`, `get_current_user_id()` |
| `app/api/` | 所有 API endpoint（prefix: `/api/v1`） |
| `app/models/` | 33 個 SQLAlchemy ORM model |
| `app/services/` | 30 個業務邏輯 service |
| `app/repositories/` | 13 個資料庫存取 repository |
| `app/schemas/` | Pydantic schema（auth, resource） |
| `alembic/versions/` | 001-019 migration 檔案 |
| `tests/features/` | BDD .feature + steps |
| `tests/features/environment.py` | Testcontainers 生命週期 |
| `tests/features/steps/__init__.py` | 所有 step import（必須在此註冊） |

## API Router 清單

auth, resource, knowledge-map, exams, wrong-answers, subscriptions, schedule, b2b, resource-library, onboarding, admin, admin-finance, admin-moderation, admin-settings, dashboard, subjects, ecpay, feedback, community, anomaly, announcements

## ORM Model 分類

- **核心**: User, Subject, Institution, Question, Answer, Exam, Resource, ResourceChunk
- **知識圖譜**: KnowledgeNode, NodeMastery, LearningJourney
- **AI**: AiChat, AiCooldown, AiModelRouting, PromptTemplate
- **財務**: Invoice, Transaction, Refund, Coupon, PlanQuota
- **分析**: QuestionStat, UserUsage, WeeklyReport
- **管理**: AdminAuditLog, SystemAnnouncement, FeatureFlag, ContentReport, Feedback
- **維運**: AnomalyRecord, MaintenanceTask, MaintenanceSchedule, MaintenanceNotification

## BDD 測試子領域（24 個）

admin, admin_finance, admin_moderation, admin_settings, ai_gen, anomaly, auth, b2b, common_then, community, dashboard, ecpay, exam, exam_result, feedback, knowledge_map, mock_exam, onboarding, resource, resource_lib, schedule, subscription, subscription_upgrade, wrong_answer

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
python -m behave tests/features/01-身分驗證.feature --no-capture

# 執行全部（排除 @ignore）
python -m behave tests/features/ --tags=~@ignore

# 新增 Alembic migration（下一個編號 020）
alembic revision --autogenerate -m "description" --rev-id 020

# DB upgrade
alembic upgrade head
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

## 注意事項

- 所有 API 回應欄位使用 **snake_case**
- 訂閱方案 DB 儲存：`FREE` / `PRO` / `PRO_PLUS` / `ULTRA`
- 訂閱方案 API 顯示：`FREE` / `PRO_199` / `PRO_PLUS_399` / `ULTRA_1599`
- DBML SSOT: `project/specs/entity/erm.dbml`（42 張表）
- 新增 step 後務必在 `steps/__init__.py` 加入 import
- `use_step_matcher("re")` 後必須 restore 為 `use_step_matcher("parse")`
- Given 步驟中建立 User 時，欄位名稱是 `password_hash`（非 `hashed_password`）
