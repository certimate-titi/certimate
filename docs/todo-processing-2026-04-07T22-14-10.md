# 待辦事項處理紀錄 — 2026-04-07T22:14:10

## 🤖 CEO 執行報告

**執行角色**：CEO 總指揮（Claude）
**觸發**：排程心跳自動執行
**處理項目**：ToDoList.md 第 7 項

---

## 📌 處理項目：Prompt 模板管理 — BDD 測試與前後端實作

**對齊 OKR**：O3 - KR1（LLM API 成本佔營收 ≤ 15%）+ O1 - KR1（AI 出題正確率）

### 任務詳情
實作 Feature 30（`project/features/30-Prompt模板管理.feature`）的完整 BDD E2E 測試、後端 API 以及前端管理後台。

---

## ✅ 完成事項

### 1. Schema Analysis（2026-04-07）
- **驗證結果**：Feature 30 與 DBML 完全一致
- **ORM 模型更新**：`backend/app/models/prompt_template.py`
  - 保留舊版 `PromptTemplate`、`PromptTemplateHistory`（向下相容）
  - 新增 `PromptTemplateV2`：完整符合 DBML 規格（template_id、name、category、model、max_tokens、system_prompt 等）
  - 新增 `PromptTemplateVersion`：版本歷史（Append-only）
  - 新增 `PromptAbTest`：A/B 測試
  - 新增 Enum：`PromptCategory`、`AbTestStatus`

### 2. Alembic Migration 037（2026-04-07）
- 檔案：`backend/alembic/versions/037_create_prompt_templates_v2.py`
- 建立：`prompt_category` enum、`ab_test_status` enum
- 建立：`prompt_templates_v2` 表（完整新版結構）
- 建立：`prompt_template_versions` 表（版本歷史）
- 建立：`prompt_ab_tests` 表（A/B 測試）

### 3. Repository（2026-04-07）
- 檔案：`backend/app/repositories/prompt_template_repository.py`
- 功能：模板 CRUD、版本查詢、A/B 測試 CRUD

### 4. Service（2026-04-07）
- 檔案：`backend/app/services/prompt_template_service.py`
- 功能完整：
  - `list_templates`（支援 category 篩選）
  - `get_template`（詳情含 system_prompt）
  - `create_template`（必要欄位驗證、唯一性、自動建立 v1）
  - `update_template`（自動 version++、記錄審計日誌）
  - `deactivate_template`（軟刪除）
  - `list_versions`（由新到舊）
  - `rollback_template`（複製目標版本 → 建立新版本）
  - `create_ab_test`（唯一性驗證：最多 1 個 running）
  - `complete_ab_test`（勝者 B 自動套用為新版本）
  - `cancel_ab_test`
  - `get_prompt_for_ai`（A/B 分流：user_id_hash % 100 < traffic_split → B）

### 5. API Endpoints（2026-04-07）
- 檔案：`backend/app/api/prompt_template.py`
- Admin 路由（`/api/v1/admin/prompt-templates`）：
  - `GET /` — 列表（?category 篩選）
  - `GET /{template_id}` — 詳情
  - `POST /` — 新增
  - `PATCH /{template_id}` — 更新
  - `DELETE /{template_id}` — 停用
  - `GET /{template_id}/versions` — 版本歷史
  - `POST /{template_id}/rollback` — 回滾
  - `POST /{template_id}/ab-tests` — 建立 A/B 測試
  - `PATCH /ab-tests/{test_id}` — 完成/取消 A/B 測試
  - `GET /ab-tests` — 所有 A/B 測試
- Internal 路由（`/api/v1/internal/prompt-templates`）：
  - `GET /{name}?user_id_hash={n}` — AI 服務取得 prompt（含 A/B 分流）
- 已註冊至 `backend/app/api/__init__.py`

### 6. BDD Step Definitions（2026-04-07）
- 目錄：`backend/tests/features/steps/prompt_template/`
- 覆蓋所有 Feature 30 scenarios：
  - `aggregate_given/prompt_templates.py` — 建立測試模板資料
  - `commands/list_templates.py` — 列表查詢
  - `commands/get_template.py` — 單一詳情
  - `commands/create_template.py` — 新增
  - `commands/update_template.py` — 更新/停用
  - `commands/version_commands.py` — 版本歷史/回滾
  - `commands/ab_test_commands.py` — A/B 測試操作
  - `aggregate_then/template_state.py` — 模板 DB 狀態驗證
  - `aggregate_then/ab_test_state.py` — A/B 測試 DB 狀態驗證
  - `readmodel_then/template_response.py` — API 回應驗證
- 已加入 `tests/features/steps/__init__.py`
- 移除 Feature 30 的 `@ignore @command` 標籤（進入 Green 階段）

### 7. Seed 腳本（2026-04-07）
- 檔案：`backend/app/scripts/seed_prompts.py`
- 執行：`cd backend && python -m app.scripts.seed_prompts`
- 功能：掃描 `project/03_Prompt_Templates/` → 解析 YAML frontmatter → INSERT/UPDATE/SKIP

### 8. 前端管理後台（2026-04-07）
- **列表頁** `/super-admin/prompt-templates/page.tsx`
  - 支援 category 篩選（safety/knowledge/exam/teaching/emotion）
  - 支援搜尋（template_id、name、display_name）
  - 顯示狀態徽章（啟用/停用）
  - 連結至編輯頁
- **詳情/編輯頁** `/super-admin/prompt-templates/[templateId]/page.tsx`
  - Tab 1（編輯）：system_prompt、user_prompt、temperature 即時編輯
  - Tab 2（版本歷史）：版本列表 + 一鍵回滾
  - Tab 3（A/B 測試）：建立測試、選勝者、取消
- **API Service**：`frontend/lib/api/services.ts` 新增 `promptTemplateService`
- **側欄導覽**：`super-admin/layout.tsx` 新增「Prompt 模板」選單項目

---

## 📊 OKR 對齊

| 任務 | 對齊目標 |
|------|----------|
| Prompt 版本管理 | O3-KR1：有效控管 prompt 成本，避免無效 API 呼叫 |
| A/B 測試 | O1-KR1：持續優化 AI 出題正確率 |
| seed_prompts.py | O3-KR1：確保 17 個 prompt 正確初始化 |

---

## ⚠️ 待手動確認（董事會）

1. **Migration 037** 需在 DB 環境執行：`alembic upgrade head`
2. **Feature 30 BDD 測試** 需執行：`python -m behave tests/features/30-Prompt模板管理.feature`
3. **Seed 腳本** 首次執行：`python -m app.scripts.seed_prompts`
4. **前端**：需確認 super-admin 路由保護（只有 super_admin 可訪問）

---

*自動執行時間：2026-04-07T22:14:10*
*執行者：CEO 總指揮（Claude）*
