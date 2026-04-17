# 待辦事項處理紀錄

**執行時間：** 2026-04-15T09:00:00+08:00（排程自動執行）
**執行者：** TiTi Commander v2.1（CEO 角色）
**觸發方式：** 每日 09:00 心跳排程

---

## 💓 TiTi 心跳報告

**時間：** 2026-04-15 09:00
**類型：** 🟢 日常巡檢 + 新功能交付確認

---

## 📋 任務狀態總覽

本次巡檢 `docs/ToDoList.md` 中所有待辦事項，並確認自上次巡檢（2026-04-12）以來的新工作：

### ToDoList 基礎設施待辦項（維持不變）

| 項目 | 所屬階段 | 程式碼狀態 | 基礎設施狀態 | 備註 |
|------|----------|-----------|-------------|------|
| LLM 防火牆配置（Llama Guard） | 階段二 | ✅ 已完成 | ⏳ 等待部署 | 需 `LLAMA_GUARD_URL` 推理服務 |
| 欄位級加密（KMS） | 階段二 | ✅ 已完成 | ⏳ 等待部署 | 需設定 `FIELD_ENCRYPTION_KEY` |
| 語意快取（Semantic Cache） | 階段三 | ✅ 已完成 | ⏳ 等待部署 | 需 Redis 基礎設施 |
| 多租戶限流（Rate Limiting） | 階段三 | ✅ 已完成 | ⏳ 等待部署 | 需 Redis 基礎設施 |
| 任務佇列隔離（Celery Queue） | 階段三 | ✅ 已完成 | ⏳ 等待部署 | 需 Redis + Celery Worker |
| 全鏈路追蹤（OpenTelemetry） | 階段四 | ✅ 已完成 | ⏳ 等待部署 | 需 OTLP Collector / Grafana Tempo |

**結論：基礎設施待辦項狀態未變，仍需人工部署。**

---

## 🆕 本次新增完成項目

### Feature 32 — 節點練習模式

**狀態：** ✅ 程式碼完成，待 BDD 測試驗收

**新增/修改檔案：**
- `backend/app/api/practice.py`（97 行）：3 支 REST API
  - `GET /api/v1/practice/nodes/{node_id}/questions`：查詢節點練習題列表
  - `POST /api/v1/practice/questions/{question_id}/answer`：提交作答
  - `GET /api/v1/practice/nodes/{node_id}/progress`：查詢節點進度
- `backend/tests/features/steps/practice/`：完整 BDD step definitions
  - `aggregate_given/knowledge_nodes.py`：知識節點 Given 步驟
  - `aggregate_given/practice_questions.py`：練習題 Given 步驟
  - `commands/practice_actions.py`：練習作答 When 步驟
  - `readmodel_then/practice_results.py`：作答結果驗證 Then 步驟
- `backend/tests/features/steps/__init__.py`：新增 practice 模組 import
- `backend/app/api/__init__.py`：新增 practice_router 掛載
- `frontend/lib/api/services.ts`：新增前端 API 方法

**Feature 32 功能範圍：**
- 查詢節點練習題列表（含空列表支援）
- 練習作答即時回饋（答對 / 答錯均回傳正確答案與詳解）
- 進度更新與向上傳播至父節點
- 不存在題目的 404 處理

---

### Feature 33 — 雲端與 AI 成本監控中心

**狀態：** ✅ 程式碼完成，待 Alembic migration 執行與 BDD 測試驗收

**新增檔案清單：**

#### 資料庫層
| 檔案 | 說明 |
|------|------|
| `backend/alembic/versions/048_add_cost_monitor_tables.py` | Migration 048：ai_usage_ledger / budget_config / budget_alert_log 三張表 |
| `backend/alembic/versions/049_add_embedding_provider_metadata.py` | Migration 049：resource_chunks 新增 embedding_provider / embedding_model 欄位 |
| `backend/alembic/versions/050_add_gcp_budget_sync_fields.py` | Migration 050：budget_config 新增 GCP Native Budget 同步欄位 |
| `backend/app/models/ai_usage_ledger.py` | ORM 模型：AI token 級用量明細 |
| `backend/app/models/budget_config.py` | ORM 模型：四 scope 預算設定（AI_ANTHROPIC / AI_GEMINI / AI_VOYAGE / GCP_TOTAL） |
| `backend/app/models/budget_alert_log.py` | ORM 模型：預算告警日誌（WARNING / DEGRADE / DISABLED / BUDGET_OVERRIDE） |

#### 業務邏輯層
| 檔案 | 說明 |
|------|------|
| `backend/app/repositories/ai_usage_repository.py` | AI 用量查詢（每月總計、趨勢 30 天、按 provider / feature 聚合） |
| `backend/app/repositories/budget_config_repository.py` | 預算設定 CRUD + GCP 同步欄位更新 |
| `backend/app/repositories/budget_alert_log_repository.py` | 告警日誌寫入與查詢 |
| `backend/app/services/cost_monitor_service.py` | 成本總覽（四 scope 金額 + 使用率）、供應商詳情、趨勢圖 30 天 |
| `backend/app/services/budget_service.py` | 預算檢查觸發（50%/80%/100%）、功能降級管理、整體調整（+%、固定金額等比）、解除停用 |
| `backend/app/services/gcp_billing_service.py` | GCP BigQuery Billing Export 查詢（服務分類、快取 1 小時） |
| `backend/app/services/gcp_budget_sync_service.py` | GCP Native Budget API 單向同步（建立 / 更新，AI_GEMINI + GCP_TOTAL） |
| `backend/app/services/voyage_quota_service.py` | Voyage embedding 配額鎖（check_and_reserve）、等待佇列管理 |

#### API 與中介層
| 檔案 | 說明 |
|------|------|
| `backend/app/api/cost_monitor.py` | 成本監控 REST API（super_admin 限定，7 支端點） |
| `backend/app/core/permissions.py` | `require_super_admin` 依賴注入、`FORBIDDEN_SUPER_ADMIN_ONLY` 錯誤 |
| `backend/app/middleware/` | AI Budget 降級 Middleware（攔截 AI 功能呼叫，注入降級/停用判斷） |

#### 前端
| 檔案 | 說明 |
|------|------|
| `frontend/app/super-admin/cost-monitor/` | 成本監控頁面（總覽 + 供應商詳情 + GCP 分類 + 趨勢圖 + 預算設定） |
| `frontend/types/cost-monitor.ts` | 前端型別定義（CostOverview / BudgetConfig / AlertLog / TrendSeries） |

#### BDD 測試
| 目錄 | 說明 |
|------|------|
| `backend/tests/features/steps/cost_monitor/aggregate_given/` | 預算設定 / 用量 / 輔助 Given 步驟 |
| `backend/tests/features/steps/cost_monitor/commands/` | 查詢端點 / 預算變更 / 系統動作 When 步驟 |
| `backend/tests/features/steps/cost_monitor/readmodel_then/` | 回應欄位 / 輔助 Then 步驟 |
| `backend/tests/features/steps/cost_monitor/aggregate_then/` | 資料庫狀態驗證 Then 步驟 |

#### DBML / 規格
- `project/specs/entity/erm.dbml`：新增 ai_usage_ledger / budget_config / budget_alert_log 三張表，resource_chunks 新增 embedding_provider / embedding_model，resource_processing_status 新增 `PENDING_BUDGET_RECOVERY`
- `project/features/33-成本監控中心.feature`：Feature 規格（17 個 Rules / 27 個 Examples）
- `backend/tests/features/33-成本監控中心.feature`：同步測試 Feature

---

## 📊 OKR 對齊狀態

| OKR 指標 | 相關功能 | 目前狀態 |
|----------|---------|---------|
| O1-KR1（AI 輸出品質 ≥ 95%） | LLM 防火牆 | 程式碼備妥，待部署 |
| O1-KR2（知識節點覆蓋率） | Feature 32 節點練習 | ✅ 程式碼完成 |
| O2-KR2（付費轉換率） | 任務佇列隔離 | 程式碼備妥，待 Celery 基礎設施 |
| O3-KR1（LLM 成本 ≤ 15% 營收） | Feature 33 成本監控 | ✅ 程式碼完成，待 Migration + GCP 設定 |
| O3-KR3（成本可視化） | Feature 33 成本監控 | ✅ 程式碼完成 |

---

## 🔍 Git 狀態

### 已修改（待提交）
| 檔案 | 異動 |
|------|------|
| `backend/app/api/__init__.py` | 新增 practice_router + cost_monitor_router |
| `backend/app/models/__init__.py` | 新增 AiUsageLedger / BudgetConfig / BudgetAlertLog import |
| `backend/app/models/resource.py` | 新增 PENDING_BUDGET_RECOVERY 狀態 |
| `backend/app/services/document_processing_service.py` | 整合 voyage_quota_service 配額鎖 |
| `backend/tests/features/environment.py` | 更新測試環境初始化 |
| `backend/tests/features/steps/__init__.py` | 新增 practice + cost_monitor 模組 import |
| `frontend/app/super-admin/layout.tsx` | 新增成本監控導覽項目 |
| `frontend/lib/api/services.ts` | 新增 practice + cost_monitor API 方法 |
| `project/specs/entity/erm.dbml` | 新增三張 cost_monitor 表 + 欄位更新 |

### 待手動執行（部署步驟）
1. **Alembic migrations**（必要）：
   ```bash
   cd backend && .venv/bin/python -m alembic upgrade head
   ```
   → 套用 migration 048 / 049 / 050

2. **GCP Billing Export 設定**（Feature 33 GCP 分類功能）：
   ```bash
   export GCP_BILLING_PROJECT_ID="your-project"
   export GCP_BILLING_DATASET="billing_export"
   export GCP_BILLING_EXPORT_TABLE="gcp_billing_export_v1_XXXXXX"
   ```

3. **GCP Budget API 設定**（Feature 33 Native Budget 同步）：
   ```bash
   export GCP_BUDGET_PARENT="billingAccounts/XXXXXX-XXXXXX-XXXXXX"
   ```

4. **BDD 測試驗收**：
   ```bash
   cd backend && .venv/bin/python -m behave tests/features/32-節點練習模式.feature
   cd backend && .venv/bin/python -m behave tests/features/33-成本監控中心.feature
   ```

---

## 🔒 需要董事會決策

目前無緊急決策事項。

**建議優先順序：**

| 優先度 | 項目 | 理由 |
|--------|------|------|
| 🔴 高 | Alembic migration 048/049/050 | Feature 33 無法啟用 |
| 🔴 高 | BDD 測試驗收（Feature 32 + 33） | 品質閘門必要步驟 |
| 🟡 中 | Redis 服務部署 | 解鎖語意快取 + 限流 + 佇列 |
| 🟡 中 | GCP Billing Export 設定 | 成本監控 GCP 分類功能 |
| 🟢 低 | GCP Budget API 設定 | Native Budget 同步（可選）|

---

## 📁 本次異動

```
docs/ToDoList.md                              ← 新增 Feature 32 + 33 完成項目
docs/todo-processing-2026-04-15T09-00-00.md  ← 新增（本紀錄）
```

（本次 commit 同時包含 Feature 32 / 33 全部程式碼）

---

## ⏭️ 下次心跳

**預計時間：** 2026-04-16 09:00
**預計內容：** 確認 BDD 測試驗收結果；若 migration 已執行，進行功能驗證。

---

*自動產出 by TiTi Commander v2.1 | CEO 角色 | 2026-04-15*
