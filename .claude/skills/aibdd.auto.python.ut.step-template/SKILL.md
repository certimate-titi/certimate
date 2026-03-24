---
name: aibdd.auto.python.ut.step-template
description: Python UT Stage 1：從 Gherkin Feature 生成 Unit Test Step Definition 樣板。使用 context.repos/context.services 取代 api_client/db_session。可被 /python-ut 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${PY_TEST_FEATURES_DIR}/**/*.feature, ${ENTITY_SPECS_DIR}/erm.dbml, ${PY_STEPS_DIR}/**/*.py
output: ${PY_STEPS_DIR}/{subdomain}/{category}/{step_name}.py（樣板）, ${PY_STEPS_DIR}/common_then/{step_name}.py（跨 subdomain 共用）
---

# 角色

BDD Step Definition 樣板生成器。從 Gherkin Feature File 生成可執行的 Step Definition 骨架（behave 裝飾器 + 函數簽名 + TODO 註解 + `pass`）。

**重要**：此 Skill 的產出僅為「樣板」（TODO 註解），不包含實作邏輯。實作邏輯由後續的紅燈 Stage 負責。

---

# 入口條件（雙模式）

## 模式 A：獨立使用

使用者直接調用 `/python-ut-step-template`。

1. 詢問目標 Feature File（若使用者未在 argument 帶入）
2. 確認 Feature File 存在於 `${PY_TEST_FEATURES_DIR}/`
3. 執行樣板生成流程

## 模式 B：被 /python-ut 調用

接收參數：Feature File 路徑。直接執行樣板生成流程。

---

# 執行前檢查（防止覆蓋已存在的 Step Definition）

**永遠不要覆蓋已存在的 Step Definition。**

## 檢查流程

1. **掃描現有 Step Definitions**
   ```bash
   find ${PY_STEPS_DIR} -type f -name "*.py"
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
   - When 用戶 "Alice" 交付課程 1
   - ...
   ```

---

# Core Mapping

領域模型 → Gherkin（已完成）→ Step Definition 樣板

映射規則：
- Given → Aggregate / Command / Event
- When → Command / Query / Event
- Then → 操作成功/失敗 / Aggregate / Read Model / Event

---

# 樣板格式

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
    TODO: 參考 {Handler-檔名}.md 實作
    TODO: 參考 Aggregate/Table: {Aggregate名稱} (若為 DB 相關)
    """
    pass
```

## 樣板規範

1. **檔案與目錄**：先按 subdomain 分目錄（例：`lesson/`, `order/`, `product/`），再按分類（例：`aggregate_given/`, `commands/`, `query/`, `aggregate_then/`, `readmodel_then/`）。`common_then/` 為跨 subdomain 共用，直接放在 `${PY_STEPS_DIR}/common_then/`
2. **一個 step 一個 module**：每個 Step Pattern 產出為一個獨立 `.py` 檔，檔案內只包含一個 step function（可命名為 `step_impl`）
3. **檔名命名**：用語意化檔名（例如 `lesson_progress.py`, `order_info.py`），避免 `steps.py` 這類大雜燴
4. **函數簽名**：第一個參數必須是 `context`，後接從 pattern 解析的參數
5. **TODO 註解**：標註事件風暴部位與對應的 Handler Prompt
6. **空方法體**：方法內容為 `pass`，等待後續實作
7. **不使用 fixtures 參數**：所有依賴從 `context` 取得

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

## Context 取得依賴

**重要**：Behave 不使用 fixtures，所有依賴從 `context` 取得：

```python
@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    # 正確：從 context 取得依賴
    repo = context.repos.lesson_progress

    # 錯誤：不能有 fixture 參數
    # def step_impl(context, user_name, lesson_id, progress, lesson_progress_repository):
```

## Context 狀態欄位（參考紅燈契約）

```python
# ${PY_ENV_FILE} - before_scenario 初始化

context.last_error = None      # When 寫入、Then 讀取
context.query_result = None    # When(Query) 寫入、Then(ReadModel) 讀取
context.ids = {}               # 名稱 → ID 映射
context.memo = {}              # 其他臨時狀態

context.repos = SimpleNamespace()      # FakeRepositories
context.services = SimpleNamespace()   # Services
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
        # ...

# DocString
@given('用戶 "{user_name}" 的個人簡介為：')
def step_impl(context, user_name):
    # context.text 自動填充
    bio = context.text
    # ...
```

---

# Decision Tree

```
讀取 Gherkin 語句
  |
  v
判斷位置（Given/When/Then/And）

Given:
  建立測試的初始資料狀態（實體屬性值）？
    → /aibdd.auto.python.ut.handlers.aggregate-given
  已完成的寫入操作（建立前置條件）？
    → /aibdd.auto.python.ut.handlers.command

When:
  讀取操作？
    → /aibdd.auto.python.ut.handlers.query
  寫入操作？
    → /aibdd.auto.python.ut.handlers.command

Then:
  只關注操作成功或失敗？
    → /aibdd.auto.python.ut.handlers.success-failure
  驗證 Command 操作後的資料狀態（從 repository 查詢）？
    → /aibdd.auto.python.ut.handlers.aggregate-then
  驗證 Query 操作的回傳值（context.query_result）？
    → /aibdd.auto.python.ut.handlers.readmodel-then

And:
  繼承前一個 Then 的判斷規則
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

**範例**：
```gherkin
Given 學生 "Alice" 在課程 1 的進度為 80%，狀態為 "進行中"
```

**輸出**：
```python
# ${PY_STEPS_DIR}/lesson/aggregate_given/lesson_progress.py

@given('學生 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """
    TODO: [事件風暴部位: Aggregate - LessonProgress]
    TODO: 參考 /aibdd.auto.python.ut.handlers.aggregate-given 實作
    TODO: 參考 Aggregate/Table: LessonProgress
    """
    pass
```

### Pattern 1.2: Given + Command

**識別規則**：
- 動作會修改系統狀態（已完成的動作）
- 描述「已經執行完某個動作」
- 常見過去式（非窮舉）：「已訂閱」「已完成」「已建立」「已添加」「已註冊」

**通用判斷**：如果 Given 描述已完成的寫入操作（用於建立前置條件），就使用此 Handler

**範例**：
```gherkin
Given 用戶 "Alice" 已訂閱旅程 1
```

**輸出**：
```python
@given('用戶 "{user_name}" 已訂閱旅程 {journey_id:d}')
def step_impl(context, user_name, journey_id):
    """
    TODO: [事件風暴部位: Command - subscribe_journey]
    TODO: 參考 /aibdd.auto.python.ut.handlers.command 實作
    """
    pass
```

## Rule 2: When 語句識別

### Pattern 2.1: When + Command

**識別規則**：
- 動作會修改系統狀態
- 描述「執行某個動作」
- 常見現在式（非窮舉）：「更新」「提交」「建立」「刪除」「添加」「移除」

**通用判斷**：如果 When 是修改系統狀態的操作且不需要回傳值，就使用此 Handler

**範例**：
```gherkin
When 學生 "Alice" 更新課程 1 的影片進度為 80%
```

**輸出**：
```python
@when('學生 "{user_name}" 更新課程 {lesson_id:d} 的影片進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    """
    TODO: [事件風暴部位: Command - update_video_progress]
    TODO: 參考 /aibdd.auto.python.ut.handlers.command 實作
    """
    pass
```

### Pattern 2.2: When + Query

**識別規則**：
- 動作不修改系統狀態，只讀取資料
- 描述「取得某些資訊」的動作
- 常見動詞（非窮舉）：「查詢」「取得」「列出」「檢視」「獲取」

**通用判斷**：如果 When 是讀取操作且需要回傳值供 Then 驗證，就使用此 Handler

**範例**：
```gherkin
When 學生 "Alice" 查詢課程 1 的進度
```

**輸出**：
```python
@when('學生 "{user_name}" 查詢課程 {lesson_id:d} 的進度')
def step_impl(context, user_name, lesson_id):
    """
    TODO: [事件風暴部位: Query - get_lesson_progress]
    TODO: 參考 /aibdd.auto.python.ut.handlers.query 實作
    """
    pass
```

## Rule 3: Then 語句識別

### Pattern 3.1: Then 操作成功

**識別規則**：明確描述操作成功。常見句型：「操作成功」「執行成功」

**輸出**：
```python
@then("操作成功")
def step_impl(context):
    """
    TODO: 參考 /aibdd.auto.python.ut.handlers.success-failure 實作
    """
    pass
```

### Pattern 3.2: Then 操作失敗

**識別規則**：明確描述操作失敗。常見句型：「操作失敗」「執行失敗」

**輸出**：
```python
@then("操作失敗")
def step_impl(context):
    """
    TODO: 參考 /aibdd.auto.python.ut.handlers.success-failure 實作
    """
    pass
```

### Pattern 3.3: Then + Aggregate

**識別規則**：
- 驗證實體的屬性值（而非 Query 回傳值）
- 描述「某個東西的某個屬性應該是某個值」
- 常見句型（非窮舉）：「在...的...應為」「的...應為」「應包含」

**通用判斷**：如果 Then 是驗證 Command 操作後的資料狀態（需要從 repository 查詢），就使用此 Handler

**範例**：
```gherkin
And 學生 "Alice" 在課程 1 的進度應為 90%
```

**輸出**：
```python
@then('學生 "{user_name}" 在課程 {lesson_id:d} 的進度應為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    """
    TODO: [事件風暴部位: Aggregate - LessonProgress]
    TODO: 參考 /aibdd.auto.python.ut.handlers.aggregate-then 實作
    TODO: 參考 Aggregate/Table: LessonProgress
    """
    pass
```

### Pattern 3.4: Then + Read Model

**識別規則**：
- 前提：When 是 Query 操作（已接收 result）
- 驗證的是查詢回傳值（而非 repository 中的狀態）
- 常見句型（非窮舉）：「查詢結果應」「回應應」「應返回」「結果包含」

**通用判斷**：如果 Then 是驗證 Query 操作的回傳值，就使用此 Handler

**範例**：
```gherkin
And 查詢結果應包含進度 80，狀態為 "進行中"
```

**輸出**：
```python
@then('查詢結果應包含進度 {progress:d}，狀態為 "{status}"')
def step_impl(context, progress, status):
    """
    TODO: [事件風暴部位: Read Model]
    TODO: 參考 /aibdd.auto.python.ut.handlers.readmodel-then 實作
    """
    pass
```

---

# Handler Prompt 映射表

| 事件風暴部位 | 位置 | 識別規則 | Handler Prompt |
|------------|------|---------|---------------|
| Aggregate | Given | 建立初始資料狀態（實體屬性值） | /aibdd.auto.python.ut.handlers.aggregate-given |
| Command | Given/When | 寫入操作（已完成/現在執行） | /aibdd.auto.python.ut.handlers.command |
| Query | When | 讀取操作（需要回傳值） | /aibdd.auto.python.ut.handlers.query |
| 操作成功/失敗 | Then | 只驗證成功或失敗 | /aibdd.auto.python.ut.handlers.success-failure |
| Aggregate | Then | 驗證實體狀態（從 repository 查詢） | /aibdd.auto.python.ut.handlers.aggregate-then |
| Read Model | Then | 驗證查詢回傳值 | /aibdd.auto.python.ut.handlers.readmodel-then |

---

# Complete Example

**Input** (Feature File):
```gherkin
Feature: 課程平台 - 增加影片進度

Rule: 影片進度必須單調遞增

  Example: 成功增加影片進度
    Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"
    When 用戶 "Alice" 更新課程 1 的影片進度為 80%
    Then 操作成功
    And 用戶 "Alice" 在課程 1 的進度應為 80%

  Example: 進度不可倒退
    Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"
    When 用戶 "Alice" 更新課程 1 的影片進度為 60%
    Then 操作失敗
    And 用戶 "Alice" 在課程 1 的進度應為 70%
```

**Output** (Step Definition 樣板):

```python
# ${PY_STEPS_DIR}/lesson/aggregate_given/lesson_progress.py

from behave import given

@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """
    TODO: [事件風暴部位: Aggregate - LessonProgress]
    TODO: 參考 /aibdd.auto.python.ut.handlers.aggregate-given 實作
    TODO: 參考 Aggregate/Table: LessonProgress
    """
    pass
```

```python
# ${PY_STEPS_DIR}/lesson/commands/video_progress.py

from behave import when

@when('用戶 "{user_name}" 更新課程 {lesson_id:d} 的影片進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    """
    TODO: [事件風暴部位: Command - update_video_progress]
    TODO: 參考 /aibdd.auto.python.ut.handlers.command 實作
    """
    pass
```

```python
# ${PY_STEPS_DIR}/lesson/aggregate_then/lesson_progress.py

from behave import then

@then('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度應為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    """
    TODO: [事件風暴部位: Aggregate - LessonProgress]
    TODO: 參考 /aibdd.auto.python.ut.handlers.aggregate-then 實作
    TODO: 參考 Aggregate/Table: LessonProgress
    """
    pass
```

```python
# ${PY_STEPS_DIR}/common_then/success.py

from behave import then

@then("操作成功")
def step_impl(context):
    """
    TODO: 參考 /aibdd.auto.python.ut.handlers.success-failure 實作
    """
    pass
```

```python
# ${PY_STEPS_DIR}/common_then/failure.py

from behave import then

@then("操作失敗")
def step_impl(context):
    """
    TODO: 參考 /aibdd.auto.python.ut.handlers.success-failure 實作
    """
    pass
```

---

# 專案結構

```
${PY_APP_DIR}/
├── models/                    # Aggregates
├── repositories/              # FakeRepositories
└── services/                  # Services

${ENTITY_SPECS_DIR}/
└── erm.dbml                   # DBML 規格

${PY_TEST_FEATURES_DIR}/
├── environment.py             # hooks：初始化 context
├── steps/                     # Step Definitions（subdomain → 分類 → 一個 step 一個 module）
│   ├── {subdomain}/           # 按業務領域分（例：lesson, order, product, role）
│   │   ├── aggregate_given/
│   │   ├── commands/
│   │   ├── query/
│   │   ├── aggregate_then/
│   │   └── readmodel_then/
│   └── common_then/           # 跨 subdomain 共用（操作成功/失敗等）
└── *.feature                  # Feature files（包含 *.dsl.feature）
```

---

# 執行步驟

1. 掃描 `${PY_STEPS_DIR}/` 目錄，建立已存在步驟清單
2. 解析 Feature File，提取所有 Given/When/Then/And 步驟
3. 對比找出缺少的步驟
4. 對每個缺少的步驟：
   - 應用 Decision Tree 識別事件風暴部位
   - 確定對應的 Handler Prompt
   - 生成樣板（裝飾器 + 函數簽名 + TODO 註解 + pass）
5. 按目錄分類組織，且每個 Step Pattern 產出為一個獨立 `.py` 檔
6. 輸出樣板檔案

---

# Critical Rules

### R1: 永遠不覆蓋已存在的 Step Definition
執行前必須先掃描 `${PY_STEPS_DIR}/`，只生成缺少的步驟。

### R2: 使用 Behave 原生語法
- 使用 `from behave import given, when, then`
- 不使用 `parsers.parse()`（Behave 原生支援）
- 不使用 fixtures 參數

### R3: 函數簽名規則
- 第一個參數必須是 `context`
- 後接從 pattern 解析的參數
- 不包含任何 fixture 參數

### R4: 只輸出樣板
不生成任何實作程式碼，只生成裝飾器、簽名、TODO 註解和 `pass`。

### R5: 保留完整 Gherkin 語句
pattern 中必須包含完整的 Gherkin 語句（含參數標記）。

### R6: 明確標註事件風暴部位
每個語句都要識別出對應的事件風暴部位。

### R7: 指引正確的 Handler
根據 Decision Tree 指引使用正確的 Handler Prompt（引用對應的 handler skill）。

### R8: 處理 And 語句
And 語句繼承前一個 Given/When/Then 的判斷邏輯。

---

# 完成條件

- 所有缺少的 Step 都有對應的 `.py` 樣板檔案
- 每個樣板包含正確的 behave 裝飾器、函數簽名、TODO 註解
- 樣板方法體為 `pass`
- 已存在的 Step Definition 未被覆蓋
- 檔案按分類目錄正確組織
