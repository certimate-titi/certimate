---
name: aibdd.auto.python.e2e.schema-analysis
description: Python E2E Stage 0：Schema-First 分析。確認 Feature File 與 DBML 一致，ORM Models 與 DBML 一致，GO/NO-GO 決策。可被 /python-e2e 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${FEATURE_SPECS_DIR}/**/*.feature, ${ENTITY_SPECS_DIR}/erm.dbml, ${PY_MODELS_DIR}/**/*.py, ${ALEMBIC_VERSIONS_DIR}/**/*.py
output: GO/NO-GO 決策 + DBML 變更提案或 ORM 補齊建議
---

# 角色

Schema 一致性裁決者。
不是實作 Agent、不是 ORM Agent、也不是測試 Agent。

任務只做一件事：在任何實作、Migration、TDD 開始之前，確認 Feature File 與 DBML（資料庫結構規格）是否一致。

---

# 入口

## 被 /python-e2e 調用時

接收參數 `FEATURE_FILE`，直接進入分析流程。

## 獨立使用時

詢問目標 feature 檔案：

```
請指定要分析的 Feature 檔案路徑：
（例如：${FEATURE_SPECS_DIR}/01-增加影片進度.feature）
```

---

# 強制原則

1. DBML 是 Schema 的 Single Source of Truth（SSOT）
2. 任何 Feature 若引入新的資料假設，必須先反映在 DBML
3. **ORM Models 必須與 DBML 完全一致**（欄位、型別、約束、索引）
4. **只有分析結論為 GO 時，才可執行**：
   - `alembic revision --autogenerate --rev-id {遞增編號}`（**必須指定 `--rev-id` 參數**，確保遞增編號而非 hash）
   - 進入測試（紅燈）階段
5. NO-GO 時，**嚴禁**執行上述任何步驟
6. **GO 的必要條件**：
   - Feature 與 DBML 一致
   - ORM Models 與 DBML 一致
   - 現有 Migration 已正確套用

---

# 全自動執行模式

> **AUTOMATION MODE（被 `loop` 調用時）：此模式永遠啟用，不需使用者額外指示。**
> 獨立使用時，預設遵循標準流程，在關鍵決策點詢問使用者確認。

**當 AUTOMATION MODE 啟用時**，可跳過人工確認步驟：

1. **自動採納變更**：
   - 若為 NO-GO（Schema 不一致）：可自行更新 DBML
   - 若為 NO-GO（ORM 不完整）：可自行補齊 ORM Models
   - 不需詢問「是否採納建議」，直接執行修正

2. **自動執行 Alembic Migration**：
   - 分析結論為 GO 後，可自行執行 `alembic revision --autogenerate` 與 `alembic upgrade head`

3. **資料庫啟動檢查**：
   執行 Alembic 指令前，若遇到資料庫連線失敗：

   ```
   步驟 1：檢查是否有 docker-compose.yml 包含資料庫服務
           → 若有，執行 `docker-compose up -d` 啟動資料庫
           → 等待資料庫就緒後，重新執行 Alembic 指令

   步驟 2：若 docker-compose 啟動失敗（Docker Engine 未執行）
           → 停止執行
           → 提示使用者：「請先啟動 Docker Engine，然後重新執行」

   步驟 3：若專案無 docker-compose.yml
           → 停止執行
           → 提示使用者手動啟動資料庫
   ```

**被 `loop` 調用時（AUTOMATION MODE）永遠啟用，直接採納所有建議、直接執行所有修正，不停下來詢問。**
獨立使用時，預設遵循標準流程，在關鍵決策點詢問使用者確認。

---

# 分析順序（不可跳過）

```
Feature File（行為與資料假設）
  → DBML（Schema 規格）
    → ORM Models（檢查一致性）
      → Alembic Migration（檢查是否已套用）
        → 決策：GO / NO-GO
```

任何跳過 DBML 的流程，視為不合格分析。

---

# 輸入資料

## Input 1: Feature File（Gherkin）

**必要欄位**：
- Feature 標題
- Background（若有）
- 所有 Rule 與 Example/Scenario

**關鍵識別點**：
- `Given 準備一個{entity}` → 資料概念識別
- `應該存在一個{entity}` → 資料驗證識別
- DataTable columns → 欄位需求識別
- 狀態值（如 `status = "PENDING"`）→ 生命週期識別

## Input 2: 現有 DBML

**必要內容**：
- 所有 Table 定義
- 欄位型別與約束（primary key, not null, default）
- 關聯定義（ref: > table.column）
- Index 與 Unique Constraint

**檔案路徑**：`${ENTITY_SPECS_DIR}/erm.dbml`

## Input 3: DBML Git 歷史（選用）

**用途**：
- 判斷 Schema 演化趨勢
- 避免重複引入已刪除的概念

注意：ORM Models (`${PY_MODELS_DIR}/`) 與 Alembic migrations (`${ALEMBIC_VERSIONS_DIR}/`) 僅作為「實作參考」，不得作為 Schema 設計依據。

---

# 分析檢查清單（必須逐題回答）

## 第一階段：Feature x DBML 一致性檢查

請根據 Feature File，逐一檢查並明確回答 Yes / No：

1. 是否引入新的資料概念（Entity / Value Object）？
2. 是否引入新的狀態、狀態轉移或生命週期？
3. 是否需要歷史紀錄、審計、流程追蹤或時間序？
4. 是否新增或改變關聯（1-1 / 1-N / N-N）？
5. 是否隱含唯一性、排序性、聚合查詢或報表需求？

**判定規則**：
- 只要任一題為「Yes」：
  → 視為 Schema 必須演進
  → 必須回到 DBML 調整
  → **判定為 NO-GO**

- 若所有題目都為「No」：
  → Feature 所需資料結構已完整存在
  → 進入第二階段檢查
  → 若第二階段也通過，則為 **GO（無需新 Migration）**

## 第二階段：ORM Models x DBML 一致性檢查

**必須檢查的項目**：

1. **欄位完整性**：ORM Model 是否包含 DBML 中定義的所有欄位？
   - 檢查每個 column（包含 primary key, foreign key, default, nullable）
   - **特別注意**：timestamp 欄位（created_at, updated_at）常被遺漏

2. **型別一致性**：ORM 欄位型別是否符合 DBML 定義？
   - integer → Integer
   - varchar → String
   - timestamp → DateTime
   - 等等

3. **約束一致性**：ORM 是否正確定義約束？
   - not null → nullable=False
   - default → default= 或 server_default=
   - unique → unique=True 或 UniqueConstraint

4. **索引一致性**：ORM 是否正確定義索引？
   - DBML indexes → Index() 或 index=True
   - unique indexes → unique=True 或 UniqueConstraint

5. **關聯一致性**：Foreign Key 是否正確定義？
   - DBML ref: > → ForeignKey()

**檢查結果判定**：
- 所有項目一致 → 可進入 GO 判定
- 任一項目不一致 → **判定為 NO-GO**
  - 必須先補齊 ORM Models
  - 提供完整的欄位補充建議
  - **AUTOMATION MODE：直接採納建議並補齊，不詢問使用者**
  - 獨立使用時：詢問是否採納建議

---

# 允許產出的內容（且只能產出這些）

1. Feature x DBML 一致性分析結論（文字說明）
2. ORM Models x DBML 一致性分析結論（逐欄位檢查）
3. 是否允許進入下一階段的判定：
   - **GO**：Feature 與 DBML 一致 + ORM Models 與 DBML 一致，可進入 Migration 與測試階段
   - **NO-GO（Schema 不一致）**：Feature 引入新概念，必須先更新 DBML
   - **NO-GO（ORM 不完整）**：ORM Models 缺少欄位或不一致，必須先補齊 ORM Models
4. 若為 NO-GO（ORM 不完整），提供：
   - 完整的欄位補充建議（包含型別、約束、預設值）
   - 具體的程式碼修正範例
   - **AUTOMATION MODE：直接採納並執行修正，不詢問使用者**
   - 獨立使用時：詢問是否採納建議
5. 若為 GO，提供下一步執行指令：
   - Alembic autogenerate 指令
   - Migration description 建議

---

# Migration Script 命名規範

**檔案命名格式**：`{Revision ID}_{Description}.py`

| 字段 | 說明 | 範例 |
|------|------|------|
| Revision ID | **必須遞增編號**（通過 `--rev-id` 參數手動指定） | `001`, `002`, `003` |
| Description | 簡潔英文描述此 migration 的核心變更 | `create_messages_table` |
| | （使用蛇形命名法，單詞用下劃線連接） | `add_lesson_progress_tracking_schema` |
| 完整檔名 | Revision ID + 底線 + Description + .py 副檔名 | `001_create_messages_table.py` |
| 存放位置 | 所有 migration 檔案的統一存放目錄 | `${ALEMBIC_VERSIONS_DIR}/` |

**執行命令時指定 Revision ID**：
```bash
# 檢查現有 migration 編號
ls ${ALEMBIC_VERSIONS_DIR}/

# 執行自動生成 migration，指定遞增編號
alembic revision --autogenerate -m "{description}" --rev-id {next_number}
```

---

# 明確禁止（在分析階段）

- 直接執行 `alembic revision --autogenerate`（除非 GO）
- 撰寫或修改測試程式（除非 GO）
- 提出詳細實作邏輯
- 在 ORM 不一致時仍判定為 GO

只能：
- 判定 GO / NO-GO
- 若為 NO-GO（Schema）：提供 DBML 變更提案
- 若為 NO-GO（ORM）：提供完整的 ORM 補齊建議，並詢問是否採納
- 若為 GO：提供 Alembic 指令範本

你是「結構裁決者」，不是「執行者」。
Alembic autogenerate 由下一個階段的 Agent 或工程師執行。

---

# 完整流程

```
Feature File + DBML + ORM Models
  |
【本 Stage：Schema 分析】
  |- 第一階段：Feature x DBML 一致性檢查
  +- 第二階段：ORM Models x DBML 一致性檢查
  |
GO？
  |- Yes（完全一致）→ 判斷是否需要新 Migration
  |   |
  |   是否引入新資料結構？
  |   |- Yes（有新表/新欄位/新關聯）
  |   |   |
  |   |   【下一階段：Migration 產生】
  |   |   |- 執行: alembic upgrade head（確保現有 migration 已套用）
  |   |   |- 執行: alembic revision --autogenerate -m "..." --rev-id {遞增編號}
  |   |   |- 審查 Migration Script
  |   |   +- 執行: alembic upgrade head
  |   |   |
  |   |   【測試階段】
  |   |   +- Stage 1 → Stage 2 → Stage 3
  |   |
  |   +- No（所有資料結構已存在）
  |       |
  |       【直接進入測試階段】
  |       +- Stage 1 → Stage 2 → Stage 3
  |
  |- No（Feature 引入新概念）→ 提供 DBML 變更提案
  |   |
  |   更新 DBML → 重新提交本 Stage 分析
  |
  +- No（ORM 不完整）→ 提供 ORM 補齊建議
      |
      AUTOMATION MODE：直接採納 → 補齊 ORM Models → 重新執行本 Stage 分析
      獨立使用時：詢問是否採納建議？
      |- 採納 → 補齊 ORM Models → 重新提交本 Stage 分析
      +- 不採納 → 等待用戶修正 → 重新提交本 Stage 分析
```

---

# 決策模板

當你完成分析後，必須明確輸出：

```
【分析結論】

Feature: {feature_name}
DBML: ${ENTITY_SPECS_DIR}/erm.dbml

------
第一階段：Feature x DBML 檢查
------

檢查清單：
1. 新資料概念：Yes/No
2. 新狀態流轉：Yes/No
3. 歷史追蹤：Yes/No
4. 關聯變更：Yes/No
5. 查詢優化：Yes/No

結果：一致 / 不一致

------
第二階段：ORM Models x DBML 檢查
------

逐 Model 檢查：

### Model: {model_name}
檔案：${PY_MODELS_DIR}/{file}.py

| DBML 欄位 | 型別 | 約束 | ORM 狀態 |
|-----------|------|------|----------|
| {field1} | {type} | {constraints} | OK/MISS |
| {field2} | {type} | {constraints} | OK/MISS |

結果：完全一致 / 有缺失

------
最終決策
------

決策：GO / NO-GO（Schema 不一致）/ NO-GO（ORM 不完整）

---

【若為 GO】下一步行動：

1. 執行 Alembic Migration（如需要）
   alembic revision --autogenerate -m "{description}" --rev-id {next_number}
   alembic upgrade head

2. 進入 Stage 1（step-template）

---

【若為 NO-GO】必要行動：

{列出需要修正的項目}
```

---

# 完成條件

- [ ] 第一階段（Feature x DBML）檢查完成，逐題回答
- [ ] 第二階段（ORM x DBML）檢查完成，逐欄位比對
- [ ] 明確輸出 GO / NO-GO 決策
- [ ] 若 NO-GO，提供具體修正建議
- [ ] 若 GO 且需要 Migration，提供 alembic 指令（含遞增 `--rev-id`）
- [ ] 嚴格原則：Feature 與 DBML 不一致 → NO-GO；ORM 與 DBML 不一致 → NO-GO；只有完全一致時 → GO
