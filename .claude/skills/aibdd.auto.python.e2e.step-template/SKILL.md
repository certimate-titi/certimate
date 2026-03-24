---
name: aibdd.auto.python.e2e.step-template
description: Python E2E Stage 1：從 Gherkin Feature 生成 Step Definition 樣板。識別事件風暴部位，指引對應的 Handler Prompt。可被 /python-e2e 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${PY_TEST_FEATURES_DIR}/**/*.feature, ${ENTITY_SPECS_DIR}/erm.dbml, ${PY_STEPS_DIR}/**/*.py
output: ${PY_STEPS_DIR}/{subdomain}/{category}/{step_name}.py（樣板）, ${PY_STEPS_DIR}/common_then/{step_name}.py（跨 subdomain 共用）
---

# 角色

BDD Step Definition 樣板生成器。從 Gherkin Feature File 生成 **E2E Step Definition 樣板**，識別事件風暴部位，並指引使用對應的 Handler Prompt 生成程式碼。

**重要**：此 Skill 的產出僅為「樣板」（TODO 註解），不包含實作邏輯。實作邏輯由後續的 Handler Prompts（Stage 2 紅燈）負責。

---

# 入口

## 被 /python-e2e 調用時

接收參數 `FEATURE_FILE`，直接進入樣板生成流程。

## 獨立使用時

詢問目標 feature 檔案：

```
請指定要處理的 Feature 檔案路徑：
（例如：${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature）
```

---

# 工作流程

**永遠不要覆蓋已存在的 Step Definition！**

1. **此 Skill（樣板生成）**：
   - **第一步：檢查現有 Step Definitions**（避免覆蓋）
   - 解析 Feature File，列出所有需要的步驟
   - 對比現有步驟，找出缺少的步驟
   - 識別事件風暴部位（僅針對缺少的步驟）
   - 生成 Step Definition 骨架（behave 裝飾器、方法簽名、TODO 註解）
   - 輸出：包含 TODO 註解的樣板檔案（僅針對缺少的步驟）

2. **後續工作（Stage 2 紅燈）**：
   - 根據標註的 Handler Prompt
   - 實作具體邏輯
   - 替換 TODO 為實際程式碼

---

# Core Mapping

領域模型 → Gherkin（已完成）→ Step Definition 樣板

映射規則：
- Given → Aggregate / Command / Event
- When → Command / Query / Event
- Then → 操作成功/失敗 / Aggregate / Read Model / Event

---

# 輸入資料

1. **Feature Files 路徑** = `${PY_TEST_FEATURES_DIR}/*.feature`
2. **DBML（Aggregate 定義）** = `${ENTITY_SPECS_DIR}/erm.dbml`
3. **Tech Stack** = Python + Behave + FastAPI TestClient + SQLAlchemy + Testcontainers
4. **Step Definition 檔案路徑** = `${PY_STEPS_DIR}/`
5. **Environment 路徑** = `${PY_ENV_FILE}`

---

# 執行前檢查（防止覆蓋已存在的 Step Definition）

在生成任何 Step Definition 樣板之前，**必須先執行以下檢查流程**：

## 檢查流程

1. **掃描現有 Step Definitions**
   ```bash
   # 列出所有現有的 Step Definition 檔案
   find ${PY_STEPS_DIR} -type f -name "*.py"

   # 搜尋所有 @given, @when, @then 裝飾器
   grep -r "@given\|@when\|@then" ${PY_STEPS_DIR}/
   ```

2. **提取已存在的 Step Patterns**
   - 從現有檔案中提取所有 `@given('...')`, `@when('...')`, `@then('...')` 的 Pattern
   - 建立「已存在步驟清單」

3. **解析 Feature File 需要的步驟**
   - 從目標 Feature File 提取所有 Given/When/Then/And 步驟
   - 建立「需要的步驟清單」

4. **對比找出缺少的步驟**
   - 對比「需要的步驟清單」與「已存在步驟清單」
   - 找出「缺少的步驟清單」
   - **只針對缺少的步驟生成樣板**

5. **輸出檢查結果**
   ```
   已存在的步驟（不需生成）:
   - Given 系統中有以下用戶：
   - Given 系統中有以下課程：
   - ...

   需要新增的步驟（將生成樣板）:
   - Given 用戶 "Alice" 在課程 1 的狀態為 "已完成"
   - When 用戶 "Alice" 更新課程 1 的進度
   - ...
   ```

---

# 輸出格式

**重要**：輸出僅包含「缺少的」Step Definition 樣板

Step Definition 樣板，格式：

```python
# ${PY_STEPS_DIR}/{subdomain}/{分類目錄}/{step檔名}.py
# 規範：一個 Step Pattern 對應一個 Python module（檔案內只放一個 step function）
# subdomain 由 Feature File 的業務領域決定（例如 lesson, order, product, role）
# common_then/ 為跨 subdomain 共用，放在 ${PY_STEPS_DIR}/common_then/（不進 subdomain）

from behave import given, when, then

@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """
    TODO: [事件風暴部位: {部位類型} - {名稱}]
    TODO: 參考 對應的 handler skill 實作
    TODO: 參考 Aggregate/Table: {Aggregate名稱} (若為 DB 相關)
    """
    pass
```

**樣板規範**：
1. **檔案與目錄**：先按 subdomain 分目錄（例：`lesson/`, `order/`, `product/`），再按分類（例：`aggregate_given/`, `commands/`, `query/`, `aggregate_then/`, `readmodel_then/`）。`common_then/` 為跨 subdomain 共用，直接放在 `${PY_STEPS_DIR}/common_then/`
2. **一個 step 一個 module**：每個 Step Pattern 產出為一個獨立 `.py` 檔，檔案內只包含一個 step function（可命名為 `step_impl`）
3. **檔名命名**：用語意化檔名（例如 `lesson_progress.py`, `order_info.py`），避免 `steps.py` 這類大雜燴
4. **函數簽名**：第一個參數必須是 `context`，後接從 pattern 解析的參數
5. **TODO 註解**：標註事件風暴部位與對應的 Handler Prompt
6. **空方法體**：方法內容為 `pass`，等待後續實作
7. **不使用 fixtures 參數**：所有依賴從 `context` 取得

---

# E2E 測試的核心特色

**與 Unit Test 的關鍵差異**：

| 面向 | Unit Test (UT) | E2E Test |
|------|---------------|----------|
| 測試對象 | Service 方法 | HTTP API Endpoint |
| 資料庫 | Fake Repository（記憶體） | PostgreSQL (Testcontainers) |
| 認證 | 無 | JWT Token in Header |
| 依賴 | 從 context.repos/services 取得 | 從 context.api_client + context.db_session |
| Given | 使用 Fake Repository | 使用 SQLAlchemy 寫入真實 DB |
| When | 呼叫 Service 方法 | 呼叫 HTTP API |
| Then | 驗證 context.last_error 或 Fake Repo | 驗證 HTTP status code 或真實 DB |

---

# Behave 語法重點

## 參數解析

Behave 原生支援參數解析（不需要 `parsers.parse()`）：

```python
from behave import given

# 字串參數：使用引號
@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    # user_name: str (自動解析)
    # lesson_id: int (由 :d 指定)
    # progress: int (由 :d 指定)
    pass

# 參數類型標記：
# {param}      - 字串（預設）
# {param:d}    - 整數
# {param:f}    - 浮點數
# {param:w}    - 單字（不含空格）
# "{param}"    - 帶引號的字串
```

## Context 取得依賴（E2E 版本）

**重要**：Behave 不使用 fixtures，所有依賴從 `context` 取得：

```python
@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    # 正確：從 context 取得依賴
    db_session = context.db_session
    api_client = context.api_client
    jwt_helper = context.jwt_helper

    # 錯誤：不能有 fixture 參數
    # def step_impl(context, user_name, lesson_id, progress, db_session):
```

## Context 狀態欄位（E2E 版本）

```python
# ${PY_ENV_FILE} - before_scenario 初始化

# 狀態
context.last_error = None        # When 寫入、Then 讀取
context.last_response = None     # HTTP Response
context.query_result = None      # When(Query) 寫入、Then(ReadModel) 讀取
context.ids = {}                 # 名稱 → ID 映射
context.memo = {}                # 其他臨時狀態

# 依賴
context.db_session = _SessionLocal()     # SQLAlchemy Session
context.api_client = TestClient(app)     # FastAPI TestClient
context.jwt_helper = JwtHelper()         # JWT Token 生成器
context.repos = SimpleNamespace()        # Repositories
context.services = SimpleNamespace()     # Services
```

## DataTable / DocString

Behave 自動將 DataTable 和 DocString 填充到 context：

```python
# DataTable
@given('系統中有以下課程：')
def step_impl(context):
    # context.table 自動填充
    for row in context.table:
        lesson_id = int(row['lessonId'])
        name = row['name']

# DocString
@given('用戶 "{user_name}" 的個人簡介為：')
def step_impl(context, user_name):
    # context.text 自動填充
    bio = context.text
```

---

# 常見 Step Definition 範例（E2E 版本）

## Aggregate Given（建立前置資料 - 寫入 DB）

```python
# ${PY_STEPS_DIR}/lesson/aggregate_given/lesson_progress.py

from behave import given

@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """
    TODO: [事件風暴部位: Aggregate - LessonProgress]
    TODO: 參考 /aibdd.auto.python.e2e.handlers.aggregate-given 實作
    TODO: 使用 SQLAlchemy 寫入真實 PostgreSQL
    TODO: 參考 Aggregate/Table: LessonProgress
    """
    pass
```

## Command（執行 HTTP API）

```python
# ${PY_STEPS_DIR}/lesson/commands/video_progress.py

from behave import when

@when('用戶 "{user_name}" 更新課程 {lesson_id:d} 的影片進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    """
    TODO: [事件風暴部位: Command - update_video_progress]
    TODO: 參考 /aibdd.auto.python.e2e.handlers.command 實作
    TODO: 調用 HTTP POST API，使用 JWT Token
    """
    pass
```

## Query（執行 HTTP GET API）

```python
# ${PY_STEPS_DIR}/lesson/query/lesson_progress.py

from behave import when

@when('用戶 "{user_name}" 查詢課程 {lesson_id:d} 的進度')
def step_impl(context, user_name, lesson_id):
    """
    TODO: [事件風暴部位: Query - get_lesson_progress]
    TODO: 參考 /aibdd.auto.python.e2e.handlers.query 實作
    TODO: 調用 HTTP GET API，將 response 存入 context
    """
    pass
```

## Success/Failure（驗證 HTTP Status Code）

```python
# ${PY_STEPS_DIR}/common_then/success.py

from behave import then

@then("操作成功")
def step_impl(context):
    """
    TODO: 參考 /aibdd.auto.python.e2e.handlers.success-failure 實作
    TODO: 驗證 context.last_response.status_code
    """
    pass
```

## Aggregate Then（驗證 DB 狀態）

```python
# ${PY_STEPS_DIR}/lesson/aggregate_then/lesson_progress.py

from behave import then

@then('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度應為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    """
    TODO: [事件風暴部位: Aggregate - LessonProgress]
    TODO: 參考 /aibdd.auto.python.e2e.handlers.aggregate-then 實作
    TODO: 使用 SQLAlchemy 從 PostgreSQL 查詢驗證
    TODO: 參考 Aggregate/Table: LessonProgress
    """
    pass
```

## ReadModel Then（驗證 HTTP Response）

```python
# ${PY_STEPS_DIR}/lesson/readmodel_then/lesson_progress.py

from behave import then

@then('查詢結果應包含進度 {progress:d}，狀態為 "{status}"')
def step_impl(context, progress, status):
    """
    TODO: [事件風暴部位: Read Model]
    TODO: 參考 /aibdd.auto.python.e2e.handlers.readmodel-then 實作
    TODO: 驗證 context.last_response.json()
    """
    pass
```

---

# Decision Rules

## Rule 1: Given 語句識別

### Pattern 1.1: Given + Aggregate
**識別規則**：
- 語句中包含實體名詞 + 屬性描述
- 描述「某個東西的某個屬性是某個值」
- 常見句型（非窮舉）：「在...的...為」「的...為」「包含」「存在」「有」

**通用判斷**：如果 Given 是在建立測試的初始資料狀態（而非執行動作），就使用此 Handler

**E2E 特色**：使用 SQLAlchemy 寫入真實 PostgreSQL

→ 參考 `/aibdd.auto.python.e2e.handlers.aggregate-given`

### Pattern 1.2: Given + Command
**識別規則**：
- 動作會修改系統狀態（已完成的動作）
- 描述「已經執行完某個動作」
- 常見過去式（非窮舉）：「已訂閱」「已完成」「已建立」「已添加」「已註冊」

**通用判斷**：如果 Given 描述已完成的寫入操作（用於建立前置條件），就使用此 Handler

**E2E 特色**：可能直接調用 HTTP API 建立前置條件

→ 參考 `/aibdd.auto.python.e2e.handlers.command`

---

## Rule 2: When 語句識別

### Pattern 2.1: When + Command
**識別規則**：
- 動作會修改系統狀態
- 描述「執行某個動作」
- 常見現在式（非窮舉）：「更新」「提交」「建立」「刪除」「添加」「移除」

**通用判斷**：如果 When 是修改系統狀態的操作且不需要回傳值，就使用此 Handler

**E2E 特色**：調用 HTTP POST/PUT/DELETE API

→ 參考 `/aibdd.auto.python.e2e.handlers.command`

### Pattern 2.2: When + Query
**識別規則**：
- 動作不修改系統狀態，只讀取資料
- 描述「取得某些資訊」的動作
- 常見動詞（非窮舉）：「查詢」「取得」「列出」「檢視」「獲取」

**通用判斷**：如果 When 是讀取操作且需要回傳值供 Then 驗證，就使用此 Handler

**E2E 特色**：調用 HTTP GET API

→ 參考 `/aibdd.auto.python.e2e.handlers.query`

---

## Rule 3: Then 語句識別

### Pattern 3.1: Then 操作成功
**識別規則**：明確描述操作成功，常見句型：「操作成功」「執行成功」

**E2E 特色**：驗證 HTTP response status code（2XX）

→ 參考 `/aibdd.auto.python.e2e.handlers.success-failure`

### Pattern 3.2: Then 操作失敗
**識別規則**：明確描述操作失敗，常見句型：「操作失敗」「執行失敗」

**E2E 特色**：驗證 HTTP response status code（4XX）

→ 參考 `/aibdd.auto.python.e2e.handlers.success-failure`

### Pattern 3.3: Then + Aggregate
**識別規則**：
- 驗證實體的屬性值（而非 Query 回傳值）
- 描述「某個東西的某個屬性應該是某個值」
- 常見句型（非窮舉）：「在...的...應為」「的...應為」「應包含」

**通用判斷**：如果 Then 是驗證 Command 操作後的資料狀態（需要從資料庫查詢），就使用此 Handler

**E2E 特色**：使用 SQLAlchemy 從真實 PostgreSQL 查詢驗證

→ 參考 `/aibdd.auto.python.e2e.handlers.aggregate-then`

### Pattern 3.4: Then + Read Model
**識別規則**：
- 前提：When 是 Query 操作（已接收 response）
- 驗證的是查詢回傳值（而非 repository 中的狀態）
- 常見句型（非窮舉）：「查詢結果應」「回應應」「應返回」「結果包含」

**通用判斷**：如果 Then 是驗證 Query 操作的回傳值，就使用此 Handler

**E2E 特色**：驗證 HTTP response.json() 的內容

→ 參考 `/aibdd.auto.python.e2e.handlers.readmodel-then`

---

# Decision Tree

```
讀取 Gherkin 語句
|
判斷位置（Given/When/Then/And）

Given:
  建立測試的初始資料狀態（實體屬性值）？
    → /aibdd.auto.python.e2e.handlers.aggregate-given（使用 SQLAlchemy 寫入 DB）
  已完成的寫入操作（建立前置條件）？
    → /aibdd.auto.python.e2e.handlers.command（調用 HTTP API 或直接寫入 DB）

When:
  讀取操作（調用 HTTP GET API）？
    → /aibdd.auto.python.e2e.handlers.query
  寫入操作（調用 HTTP POST/PUT/DELETE API）？
    → /aibdd.auto.python.e2e.handlers.command

Then:
  只關注操作成功或失敗（HTTP status code）？
    → /aibdd.auto.python.e2e.handlers.success-failure
  驗證 Command 操作後的資料狀態（從 DB 查詢）？
    → /aibdd.auto.python.e2e.handlers.aggregate-then
  驗證 Query 操作的回傳值（response.json()）？
    → /aibdd.auto.python.e2e.handlers.readmodel-then

And:
  繼承前一個 Then 的判斷規則
```

---

# Handler Prompt 映射表（E2E 版本）

| 事件風暴部位 | 位置 | 識別規則 | Handler Prompt | E2E 特色 |
|------------|------|---------|---------------|---------|
| Aggregate | Given | 建立初始資料狀態（實體屬性值） | /aibdd.auto.python.e2e.handlers.aggregate-given | 用 SQLAlchemy 寫入 DB |
| Command | Given/When | 寫入操作（已完成/現在執行） | /aibdd.auto.python.e2e.handlers.command | 調用 HTTP POST API |
| Query | When | 讀取操作（需要回傳值） | /aibdd.auto.python.e2e.handlers.query | 調用 HTTP GET API |
| 操作成功/失敗 | Then | 只驗證成功或失敗 | /aibdd.auto.python.e2e.handlers.success-failure | 驗證 HTTP status code |
| Aggregate | Then | 驗證實體狀態（從 DB 查詢） | /aibdd.auto.python.e2e.handlers.aggregate-then | 用 SQLAlchemy 查詢 DB |
| Read Model | Then | 驗證查詢回傳值 | /aibdd.auto.python.e2e.handlers.readmodel-then | 驗證 response.json() |

---

# Behave 專案結構（E2E 版本）

```
${PY_APP_DIR}/
├── models/                    # SQLAlchemy ORM Models
├── repositories/              # SQLAlchemy Repositories
├── services/                  # Services
├── api/                       # FastAPI endpoints
└── main.py                    # FastAPI app

${ENTITY_SPECS_DIR}/
└── erm.dbml                   # DBML 規格

${PY_TEST_FEATURES_DIR}/
├── environment.py              # hooks：初始化 context（Testcontainers + DB）
├── steps/                      # Step Definitions（subdomain → 分類 → 一個 step 一個 module）
│   ├── {subdomain}/            # 按業務領域分（例：lesson, order, product, role）
│   │   ├── aggregate_given/
│   │   ├── commands/
│   │   ├── query/
│   │   ├── aggregate_then/
│   │   └── readmodel_then/
│   └── common_then/            # 跨 subdomain 共用（操作成功/失敗等）
└── *.feature                   # Feature files
```

---

# Critical Rules

## R1: 永遠不覆蓋已存在的 Step Definition
執行前必須先掃描 `${PY_STEPS_DIR}/`，只生成缺少的步驟。

## R2: 使用 Behave 原生語法
- 使用 `from behave import given, when, then`
- 不使用 `parsers.parse()`（Behave 原生支援）
- 不使用 fixtures 參數

## R3: 函數簽名規則
- 第一個參數必須是 `context`
- 後接從 pattern 解析的參數
- 不包含任何 fixture 參數

## R4: 只輸出樣板
不生成任何程式碼，只生成裝飾器、簽名、TODO 註解和 `pass`。

## R5: 保留完整 Gherkin 語句
pattern 中必須包含完整的 Gherkin 語句（含參數標記）。

## R6: 明確標註事件風暴部位
每個語句都要識別出對應的事件風暴部位。

## R7: 指引正確的 Handler（E2E 版本）
根據 Decision Tree 指引使用正確的 Handler Prompt，並標註 E2E 特色。

## R8: 處理 And 語句
And 語句繼承前一個 Given/When/Then 的判斷邏輯。

## R9: 所有依賴從 context 取得
E2E 版本的依賴包括：`context.db_session`, `context.api_client`, `context.jwt_helper` 等。

---

# 完成條件

- [ ] 已掃描現有 Step Definitions，避免覆蓋
- [ ] 已輸出已存在步驟清單與需新增步驟清單
- [ ] 每個新增步驟都有正確的事件風暴部位標註
- [ ] 每個新增步驟都指引了正確的 Handler Prompt
- [ ] 一個 step 一個 module，目錄分類正確
- [ ] 所有函數簽名正確（context 為第一參數，無 fixture 參數）
- [ ] 所有方法體為 `pass`，無實作邏輯
