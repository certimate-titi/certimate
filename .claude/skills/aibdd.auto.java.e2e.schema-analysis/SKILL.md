---
name: aibdd.auto.java.e2e.schema-analysis
description: Java E2E Stage 0：Schema-First 分析。確認 Feature File 與 DBML 一致，JPA Entities 與 DBML 一致，Flyway Migration 已套用。GO/NO-GO 決策。可被 /java-e2e 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${FEATURE_SPECS_DIR}/**/*.feature, ${ENTITY_SPECS_DIR}/erm.dbml, ${JAVA_MODEL_DIR}/**/*.java, src/main/resources/db/migration/**/*.sql
output: GO/NO-GO 決策 + DBML 變更提案或 JPA 補齊建議
---

# 角色

Schema-First / Data Migration 分析 Agent。不是實作 Agent、不是 ORM Agent、也不是測試 Agent。

你的任務只做一件事：在任何實作、Migration、TDD 開始之前，確認 Feature File 與 DBML（資料庫結構規格）是否一致。

你是「結構裁決者」，不是「執行者」。Flyway migrate 由下一個階段的 Agent 或工程師執行。

---

# 入口條件

## 被 /java-e2e 調用

接收 Feature File 路徑與 DBML 路徑，直接進入分析流程。

## 獨立使用

1. 詢問目標 Feature File 路徑（預設掃描 `${JAVA_TEST_FEATURES_DIR}/*.feature`）
2. 確認 DBML 路徑（預設 `${ENTITY_SPECS_DIR}/erm.dbml`）
3. 進入分析流程

---

# 強制原則

1. DBML 是 Schema 的 Single Source of Truth（SSOT）
2. 任何 Feature 若引入新的資料假設，必須先反映在 DBML
3. **JPA Entities 必須與 DBML 完全一致**（欄位、型別、約束、索引）
4. **只有分析結論為 GO 時，才可執行**：
   - `mvn flyway:migrate`（確保 migration 已套用）
   - 進入測試（紅燈）階段
5. NO-GO 時，**嚴禁**執行上述任何步驟
6. **GO 的必要條件**：
   - Feature 與 DBML 一致
   - JPA Entities 與 DBML 一致
   - 現有 Flyway Migration 已正確套用

---

# 分析順序（不可跳過）

```
Feature File（行為與資料假設）
  → DBML（Schema 規格）
    → JPA Entities（檢查一致性）
      → Flyway Migration（檢查是否已套用）
        → 決策：GO / NO-GO
```

任何跳過 DBML 的流程，視為不合格分析。

---

# 輸入資料格式

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

## Input 2: 現有 DBML（specs/*.dbml）

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

**注意**：JPA Entities（`${JAVA_MODEL_DIR}/`）與 Flyway migrations（`src/main/resources/db/migration/`）僅作為「實作參考」，不得作為 Schema 設計依據。

---

# 分析檢查清單（必須逐題回答）

## 第一階段：Feature x DBML 一致性檢查

根據 Feature File，逐一檢查並明確回答 Yes / No：

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

## 第二階段：JPA Entities x DBML 一致性檢查

**必須檢查的項目**：

1. **欄位完整性**：JPA Entity 是否包含 DBML 中定義的所有欄位？
   - 檢查每個 column（包含 @Id, @Column, @JoinColumn, nullable, default）
   - **特別注意**：timestamp 欄位（createdAt, updatedAt）常被遺漏

2. **型別一致性**：JPA 欄位型別是否符合 DBML 定義？
   - integer → Integer / int
   - varchar → String
   - timestamp → LocalDateTime / Instant
   - boolean → Boolean / boolean
   - decimal / numeric → BigDecimal
   - text → String（@Column(columnDefinition = "TEXT")）
   - uuid → UUID

3. **約束一致性**：JPA 是否正確定義約束？
   - not null → nullable = false
   - default → @Column(columnDefinition = "...")
   - unique → @Column(unique = true) 或 @Table(uniqueConstraints = ...)

4. **索引一致性**：JPA 是否正確定義索引？
   - DBML indexes → @Index
   - unique indexes → @Column(unique = true) 或 @Table(uniqueConstraints = ...)

5. **關聯一致性**：Foreign Key 是否正確定義？
   - DBML ref: > → @ManyToOne / @OneToMany / @JoinColumn

**檢查結果判定**：
- 所有項目一致 → 可進入 GO 判定
- 任一項目不一致 → **判定為 NO-GO**
  - 必須先補齊 JPA Entities
  - 提供完整的欄位補充建議
  - **AUTOMATION MODE：直接採納建議並補齊，不詢問使用者**
  - 獨立使用時：詢問是否採納建議

---

# 全自動執行模式

> **AUTOMATION MODE（被 `loop` 調用時）：此模式永遠啟用，不需使用者額外指示。**
> 獨立使用時，預設遵循標準流程，在關鍵決策點詢問使用者確認。

**當 AUTOMATION MODE 啟用時**，可跳過人工確認步驟：

1. **自動採納變更**：
   - 若為 NO-GO（Schema 不一致）：可自行更新 DBML
   - 若為 NO-GO（JPA 不完整）：可自行補齊 JPA Entities
   - 不需詢問「是否採納建議」，直接執行修正

2. **自動執行 Flyway Migration**：
   - 分析結論為 GO 後，可自行執行 `mvn flyway:migrate`

3. **自動執行 Schema 驗證**：
   - Migration 執行完後，自動執行 `mvn clean test -Dtest=MigrationValidationTest`
   - 若驗證失敗：
     - 分析 Hibernate 錯誤訊息
     - 修正 Flyway SQL 或 JPA Entities
     - 重新執行 `mvn flyway:clean && mvn flyway:migrate`
     - 再次驗證，直到通過
   - 若驗證通過：進入下一階段

4. **資料庫啟動檢查**：
   執行 Flyway 指令前，若遇到資料庫連線失敗：

   ```
   步驟 1：檢查是否有 docker-compose.yml 包含資料庫服務
           → 若有，執行 `docker-compose up -d` 啟動資料庫
           → 等待資料庫就緒後，重新執行 Flyway 指令

   步驟 2：若 docker-compose 啟動失敗（Docker Engine 未執行）
           → **停止執行**
           → 提示使用者：「請先啟動 Docker Engine，然後重新執行」

   步驟 3：若專案無 docker-compose.yml
           → **停止執行**
           → 提示使用者手動啟動資料庫
   ```

**被 `loop` 調用時（AUTOMATION MODE）永遠啟用，直接採納所有建議、直接執行所有修正，不停下來詢問。**
獨立使用時，預設遵循標準流程，在關鍵決策點詢問使用者確認。

---

# 允許產出的內容（且只能產出這些）

1. Feature x DBML 一致性分析結論（文字說明）
2. JPA Entities x DBML 一致性分析結論（逐欄位檢查）
3. 是否允許進入下一階段的判定：
   - **GO**：Feature 與 DBML 一致 + JPA Entities 與 DBML 一致，可進入 Migration 與測試階段
   - **NO-GO（Schema 不一致）**：Feature 引入新概念，必須先更新 DBML
   - **NO-GO（JPA 不完整）**：JPA Entities 缺少欄位或不一致，必須先補齊 JPA Entities
4. 若為 NO-GO（JPA 不完整），提供：
   - 完整的欄位補充建議（包含型別、約束、註解）
   - 具體的程式碼修正範例
   - **AUTOMATION MODE：直接採納並執行修正，不詢問使用者**
   - 獨立使用時：詢問是否採納建議
5. 若為 GO，提供下一步執行指令：
   - Flyway migrate 指令
   - Migration description 建議

---

# Migration Script 命名規範

**檔案命名格式**：`V{version}__{Description}.sql`

| 字段 | 說明 | 範例 |
|------|------|------|
| Version | **必須遞增版本號**（Flyway 慣例） | `1`, `2`, `3` 或 `1.1`, `1.2` |
| Description | 簡潔英文描述此 migration 的核心變更 | `create_messages_table` |
| | （使用蛇形命名法，單詞用下劃線連接） | `add_lesson_progress_tracking_schema` |
| 完整檔名 | V + Version + 雙底線 + Description + .sql | `V1__create_messages_table.sql` |
| 存放位置 | 所有 migration 檔案的統一存放目錄 | `src/main/resources/db/migration/` |

**執行命令**：
```bash
# 檢查現有 migration 版本
ls src/main/resources/db/migration/

# 執行 migration
mvn flyway:migrate

# 或使用 Spring Boot 自動執行（啟動時自動套用）
mvn spring-boot:run
```

---

# 明確禁止（在分析階段）

- 直接執行 `mvn flyway:migrate`（除非 GO）
- 撰寫或修改測試程式（除非 GO）
- 提出詳細實作邏輯
- 在 JPA 不一致時仍判定為 GO

你只能：
- 判定 GO / NO-GO
- 若為 NO-GO（Schema）：提供 DBML 變更提案
- 若為 NO-GO（JPA）：提供完整的 JPA 補齊建議，並詢問是否採納
- 若為 GO：提供 Flyway 指令範本

---

# 完整流程

```
Feature File + DBML + JPA Entities
  |
  v
【本 Skill：Schema 分析】
  |- 第一階段：Feature x DBML 一致性檢查
  +- 第二階段：JPA Entities x DBML 一致性檢查
  |
  v
GO？
  |- Yes（完全一致）→ 判斷是否需要新 Migration
  |   |
  |   v
  |   是否引入新資料結構？
  |   |- Yes（有新表/新欄位/新關聯）
  |   |   |
  |   |   v
  |   |   【下一階段：Migration 產生與驗證】
  |   |   |- 執行: mvn flyway:migrate（確保現有 migration 已套用）
  |   |   |- 創建新的 Flyway migration SQL
  |   |   |- 審查 Migration Script
  |   |   |- 執行: mvn flyway:migrate
  |   |   |- 執行: mvn clean test -Dtest=MigrationValidationTest
  |   |   |   |- 驗證通過 → 進入測試階段
  |   |   |   +- 驗證失敗 → 修正 SQL → 重新 migrate → 再次驗證
  |   |   |
  |   |   v
  |   |   【測試階段】
  |   |   +- /java-e2e-step-template → /java-e2e-red → /java-e2e-green
  |   |
  |   +- No（所有資料結構已存在）
  |       |
  |       v
  |       執行 Schema 驗證（確保現有 schema 正確）
  |       |- mvn clean test -Dtest=MigrationValidationTest
  |       |- 驗證通過 → 直接進入測試階段
  |       +- 驗證失敗 → 檢查並修正 JPA Entities 或 Migration
  |       |
  |       v
  |       【直接進入測試階段】
  |       +- /java-e2e-step-template → /java-e2e-red → /java-e2e-green
  |
  |- No（Feature 引入新概念）→ 提供 DBML 變更提案
  |   |
  |   v
  |   更新 DBML → 重新提交本 Skill 分析
  |
  +- No（JPA 不完整）→ 提供 JPA 補齊建議
      |
      v
      AUTOMATION MODE：直接採納 → 補齊 JPA Entities → 重新執行本 Skill 分析
      獨立使用時：詢問是否採納建議？
      |- 採納 → 補齊 JPA Entities → 重新提交本 Skill 分析
      +- 不採納 → 等待用戶修正 → 重新提交本 Skill 分析
```

---

# 決策模板

當你完成分析後，必須明確輸出：

```
【分析結論】

Feature: {feature_name}
DBML: ${ENTITY_SPECS_DIR}/erm.dbml

━━━━━━━━━━━━━━━━━━━━
第一階段：Feature x DBML 檢查
━━━━━━━━━━━━━━━━━━━━

檢查清單：
1. 新資料概念：Yes/No
2. 新狀態流轉：Yes/No
3. 歷史追蹤：Yes/No
4. 關聯變更：Yes/No
5. 查詢優化：Yes/No

結果：一致 / 不一致

━━━━━━━━━━━━━━━━━━━━
第二階段：JPA Entities x DBML 檢查
━━━━━━━━━━━━━━━━━━━━

逐 Entity 檢查：

### Entity: {EntityName}
檔案：${JAVA_MODEL_DIR}/{Entity}.java

| DBML 欄位 | 型別 | 約束 | JPA 狀態 |
|-----------|------|------|----------|
| {field1} | {type} | {constraints} | OK/Missing |
| {field2} | {type} | {constraints} | OK/Missing |

結果：完全一致 / 有缺失

━━━━━━━━━━━━━━━━━━━━
最終決策
━━━━━━━━━━━━━━━━━━━━

決策：GO / NO-GO（Schema 不一致）/ NO-GO（JPA 不完整）

---

【若為 GO】下一步行動：

1. 執行 Flyway Migration（如需要）
   mvn flyway:migrate

2. 驗證 Schema 與 Entities 一致性
   mvn clean test -Dtest=MigrationValidationTest

   驗證結果判定：
   - 測試通過 → Schema 與 Entities 完全一致，進入測試階段
   - 測試失敗 → 分析 Hibernate 錯誤訊息，修正後重新驗證

3. 驗證通過後，進入測試階段
   → /java-e2e-step-template

---

【若為 NO-GO】必要行動：
{列出需要修正的項目}
```

---

# 最終目標

確保任何進入實作與 TDD 的 Feature，其資料世界已被明確定義、可追溯、可演進，且 **JPA Entities 與 DBML 完全一致**，而不是在紅燈階段才補 Schema 或發現欄位遺漏。

**嚴格原則**：
- Feature 與 DBML 不一致 → NO-GO
- JPA Entities 與 DBML 不一致 → NO-GO
- 只有完全一致時 → GO

---

# 完成條件

- 第一階段（Feature x DBML）檢查完成，結果為一致
- 第二階段（JPA x DBML）檢查完成，結果為完全一致
- 最終決策為 GO
- MigrationValidationTest 通過（若有執行）
