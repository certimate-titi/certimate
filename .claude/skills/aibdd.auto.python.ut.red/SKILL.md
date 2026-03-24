---
name: aibdd.auto.python.ut.red
description: Python UT Stage 2：紅燈生成器。建立 FakeRepository（NotImplementedError）+ Service 介面（NotImplementedError）+ 完整 Step Definition。預期失敗：NotImplementedError。可被 /python-ut 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${PY_STEPS_DIR}/**/*.py（樣板）, ${ENTITY_SPECS_DIR}/erm.dbml, handler skills
output: ${PY_STEPS_DIR}/**/*.py（完整）, ${PY_MODELS_DIR}/**/*.py, ${PY_REPOSITORIES_DIR}/fake_*.py, ${PY_SERVICES_DIR}/**/*.py（介面）
---

# 角色

BDD 測試協調器，負責紅燈階段。你的任務是：
1. 找到尚未實作的 Step Definition 樣板
2. 讀取樣板中的 TODO 註解（作為路牌）
3. 根據路牌指示，調用對應的 Handler Prompt 來實作

**你不需要自己實作邏輯，只需要按照註解路牌指示，找到正確的 Handler Prompt 閱讀他、執行他的要求。**

---

# 入口條件（雙模式）

## 模式 A：獨立使用

使用者直接調用 `/python-ut-red`。

1. 詢問目標 Feature File（若使用者未在 argument 帶入）
2. 確認 Step Definition 樣板已存在（若無，提示先執行 `/python-ut-step-template`）
3. 執行紅燈流程

## 模式 B：被 /python-ut 調用

接收參數：Feature File 路徑。直接執行紅燈流程。

---

# 紅燈階段的核心原則

## 可以做的事

- 實作 Step Definition 方法（Aggregate Given/Then、Command、Query）
- 建立 Aggregate 類別定義（屬性、`__init__`）
- 建立 FakeRepository 類別定義（方法簽名，內部拋出 `NotImplementedError`）
- 建立 Service 類別定義（方法簽名，內部拋出 `NotImplementedError`）
- 在 `${PY_ENV_FILE}` 設定 context 初始化

## 不可以做的事

- **不實作 FakeRepository 的方法體**（只定義簽名）
- **不實作 Service 的業務邏輯**（只定義簽名）
- **不讓測試通過**（測試應該失敗）

## 為什麼？

紅燈階段的目的是讓測試**失敗**。Step Definition 會呼叫 Service → 拋出 `NotImplementedError`。這正是 TDD 的紅燈：測試運行但失敗。綠燈階段才實作 FakeRepository 和 Service，讓測試通過。

---

# 核心契約（Behave Context）

## 契約 1：共用狀態

**所有 scenario 狀態只能放在 context 的以下屬性**：

```python
# ${PY_ENV_FILE} - before_scenario

context.last_error = None      # Exception | None（When 寫入、Then 只讀）
context.query_result = None    # Any | None（When(Query) 寫入、Then(ReadModel) 只讀）
context.ids = {}               # dict：名稱 → ID 映射（如 "Alice" -> user_id）
context.memo = {}              # dict：其他臨時共享狀態
```

**規則**：
- **When 負責寫入**：Command/Query 執行後寫入 `context.last_error` 或 `context.query_result`
- **Then 負責讀取**：驗證步驟只讀這些狀態，不重新執行 When
- **禁止跨 scenario 共用**：每個 scenario 前必須重新初始化

## 契約 2：依賴注入（純 Behave 版）

**所有依賴只能放在 context 的以下命名空間**：

```python
# ${PY_ENV_FILE} - before_scenario

from types import SimpleNamespace

context.repos = SimpleNamespace()      # 所有 FakeRepositories
context.services = SimpleNamespace()   # 所有 Services

# 範例：初始化 repositories（Fake，dict-based）
context.repos.lesson_progress = LessonProgressRepository()
context.repos.user = UserRepository()

# 範例：初始化 services（注入 repos）
context.services.lesson = LessonService(
    lesson_progress_repository=context.repos.lesson_progress
)
```

**規則**：
- **steps 只能從 `context.repos.*` / `context.services.*` 取依賴**
- **禁止在 step 內 new repo/service**
- **禁止 module/global 變數跨 scenario**
- **每個 scenario 前都重新初始化（before_scenario）**

## 契約 3：AAA 責任切分

- **Given = Arrange**：只建前置資料，不驗證業務規則
- **When = Act**：執行一次受測行為，捕獲錯誤到 `context.last_error`
- **Then = Assert**：只驗證結果，不重做 When

## 契約 4：Step 函數簽名規則

```python
# 正確：只有 context + 從 pattern 解析的參數
@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    # 從 context 取得依賴
    repo = context.repos.lesson_progress
    # ...

# 錯誤：不能有 fixture 參數（那是 pytest-bdd 的東西）
@given('...')
def step_impl(context, user_name, lesson_progress_repository):
    # behave 不支援這種注入
```

---

# 工作流程

## 步驟 1: 識別未實作的樣板

掃描 `${PY_STEPS_DIR}/` 目錄，找到包含 TODO 註解的 Step Definition 方法。

**檢查模式**：
```python
"""
TODO: 參考 XXX-Handler.md 實作
"""
pass  # 表示尚未實作
```

## 步驟 2: 讀取路牌資訊

從 TODO 註解中提取：
1. **Handler Prompt 檔名**：如 `Aggregate-Given-Handler.md`
2. **參考的 Spec**：從 `erm.dbml` 找對應的 Table 定義

## 步驟 3: 調用對應的 Handler Prompt

**傳入資訊**：
1. **樣板代碼**：包含方法簽名、參數
2. **DBML 定義**（如果需要）

**Handler Prompt 位置**：對應的 handler skill（如 /aibdd.auto.python.ut.handlers.command）

## 步驟 4: 實作 Step Definition

Handler Prompt 會根據樣板和 Spec，生成以下內容：

### 紅燈階段會建立的內容

- **Step Definition 方法的完整實作**
- **Aggregate 類別**（如果尚未存在）
  - 屬性定義
  - `__init__` 方法
- **FakeRepository 類別**（如果尚未存在）
  - 方法**簽名**（如 `def save(self, entity):`）
  - **內部拋出 `NotImplementedError`**
- **Service 類別**（如果尚未存在）
  - 方法**簽名**
  - **內部拋出 `NotImplementedError`**
- **`${PY_ENV_FILE}`**（hooks 定義）

### 紅燈階段不會建立的內容

- **FakeRepository 的實作邏輯** — 完全不建立
- **Service 的業務邏輯** — 完全不建立

## 步驟 5: 設定 environment.py

**必須建立此檔案來初始化 context**：

```python
# ${PY_ENV_FILE}

from types import SimpleNamespace

def before_scenario(context, scenario):
    """每個 scenario 執行前初始化"""
    # 初始化狀態
    context.last_error = None
    context.query_result = None
    context.ids = {}
    context.memo = {}

    # 初始化依賴
    context.repos = SimpleNamespace()
    context.services = SimpleNamespace()

    # TODO: 根據需要的 repos/services 初始化
    # 範例：
    # from app.repositories.lesson_progress_repository import LessonProgressRepository
    # from app.services.lesson_service import LessonService
    #
    # context.repos.lesson_progress = LessonProgressRepository()
    # context.services.lesson = LessonService(
    #     lesson_progress_repository=context.repos.lesson_progress
    # )

def after_scenario(context, scenario):
    """每個 scenario 執行後清理"""
    context.last_error = None
    context.query_result = None
    context.ids.clear()
    context.memo.clear()
```

## 步驟 6: 執行測試確認紅燈

**紅燈階段完成後，必須執行測試確認紅燈狀態。**

```bash
behave ${PY_TEST_FEATURES_DIR}/{feature_file}
```

**預期結果**：測試失敗（紅燈）

**失敗原因**：Service/Repository 方法拋出 `NotImplementedError`

**檢查要點**：
1. Step Definitions 是否正確載入（沒有 "undefined step" 錯誤）
2. 測試是否執行（不是語法錯誤）
3. 測試是否失敗（因為 `NotImplementedError`）
4. 錯誤訊息是否為 "紅燈階段：尚未實作"

**範例輸出**：
```
Feature: 課程平台 - 增加影片進度

  Scenario: 成功增加影片進度
    Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"  # passes
    When 用戶 "Alice" 更新課程 1 的影片進度為 80%              # fails
      NotImplementedError: 紅燈階段：尚未實作

Failing scenarios:
  tests/features/03-增加影片進度.dsl.feature:6  成功增加影片進度

0 features passed, 1 failed, 0 skipped
0 scenarios passed, 1 failed, 0 skipped
```

**如果測試沒有失敗，請檢查**：
- Step Definition 是否正確實作
- Service 方法是否拋出 `NotImplementedError`
- `__init__.py` 是否正確導入所有 step definition 模組

## 步驟 7: 移除 @ignore tag

當你完成這個 feature 的紅燈骨架後，請把該 feature file 第一行的 `@ignore` 刪掉，讓它後續可以被「排除 `@ignore` 的回歸測試」涵蓋到。

---

# 路牌對照表

| TODO 註解中的 Handler | Handler Prompt 檔案 | 需要的 Spec |
|---------------------|-------------------|-----------|
| `Aggregate-Given-Handler.md` | /aibdd.auto.python.ut.handlers.aggregate-given | erm.dbml (Table 定義) |
| `Aggregate-Then-Handler.md` | /aibdd.auto.python.ut.handlers.aggregate-then | erm.dbml (Table 定義) |
| `Command-Handler.md` | /aibdd.auto.python.ut.handlers.command | erm.dbml (Table 定義) |
| `Query-Handler.md` | /aibdd.auto.python.ut.handlers.query | erm.dbml (Table 定義) |
| `ReadModel-Then-Handler.md` | /aibdd.auto.python.ut.handlers.readmodel-then | - |
| `Success-Failure-Handler.md` | /aibdd.auto.python.ut.handlers.success-failure | - |

---

# Complete Example

## Input（Step Definition 樣板）

```python
@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """
    TODO: [事件風暴部位: Aggregate - LessonProgress]
    TODO: 參考 /aibdd.auto.python.ut.handlers.aggregate-given 實作
    TODO: 參考 Aggregate/Table: LessonProgress
    """
    pass

@when('用戶 "{user_name}" 更新課程 {lesson_id:d} 的影片進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    """
    TODO: [事件風暴部位: Command - update_video_progress]
    TODO: 參考 /aibdd.auto.python.ut.handlers.command 實作
    """
    pass

@then('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度應為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    """
    TODO: [事件風暴部位: Aggregate - LessonProgress]
    TODO: 參考 /aibdd.auto.python.ut.handlers.aggregate-then 實作
    """
    pass
```

## Output 1（Step Definition 實作）

```python
# ${PY_STEPS_DIR}/lesson/aggregate_given/lesson_progress.py

from behave import given
from app.models.lesson_progress import LessonProgress

@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    # 取得用戶 ID（從 context.ids 或建立新的）
    if user_name not in context.ids:
        context.ids[user_name] = user_name
    user_id = context.ids[user_name]

    # 狀態映射：中文 → 英文 enum
    status_map = {
        "進行中": "IN_PROGRESS",
        "已完成": "COMPLETED",
        "未開始": "NOT_STARTED",
    }

    # 建立 Aggregate
    lesson_progress = LessonProgress(
        user_id=user_id,
        lesson_id=lesson_id,
        progress=progress,
        status=status_map.get(status, status)
    )

    # 儲存到 FakeRepository（從 context 取得）
    context.repos.lesson_progress.save(lesson_progress)
```

```python
# ${PY_STEPS_DIR}/lesson/commands/video_progress.py

from behave import when

@when('用戶 "{user_name}" 更新課程 {lesson_id:d} 的影片進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    user_id = context.ids.get(user_name, user_name)

    try:
        context.services.lesson.update_video_progress(
            user_id=user_id,
            lesson_id=lesson_id,
            progress=progress
        )
        context.last_error = None
    except Exception as e:
        context.last_error = e
```

```python
# ${PY_STEPS_DIR}/lesson/aggregate_then/lesson_progress.py

from behave import then

@then('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度應為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    user_id = context.ids.get(user_name, user_name)

    lesson_progress = context.repos.lesson_progress.find(
        user_id=user_id,
        lesson_id=lesson_id
    )

    assert lesson_progress is not None, \
        f"找不到用戶 {user_name} 在課程 {lesson_id} 的進度"
    assert lesson_progress.progress == progress, \
        f"預期進度 {progress}%，實際為 {lesson_progress.progress}%"
```

## Output 2（Aggregate 定義）

```python
# ${PY_MODELS_DIR}/lesson_progress.py

class LessonProgress:
    """課程進度 Aggregate"""

    def __init__(self, user_id: str, lesson_id: int, progress: int, status: str):
        self.user_id = user_id
        self.lesson_id = lesson_id
        self.progress = progress
        self.status = status
```

## Output 3（FakeRepository 定義 — NotImplementedError）

```python
# ${PY_REPOSITORIES_DIR}/lesson_progress_repository.py

from typing import Optional
from app.models.lesson_progress import LessonProgress

class LessonProgressRepository:
    """課程進度 Repository - 僅定義介面，不實作"""

    def save(self, lesson_progress: LessonProgress) -> None:
        """保存課程進度 - 紅燈階段：空實作"""
        raise NotImplementedError("紅燈階段：尚未實作")

    def find(self, user_id: str, lesson_id: int) -> Optional[LessonProgress]:
        """查詢課程進度 - 紅燈階段：空實作"""
        raise NotImplementedError("紅燈階段：尚未實作")
```

## Output 4（Service 定義 — NotImplementedError）

```python
# ${PY_SERVICES_DIR}/lesson_service.py

from app.repositories.lesson_progress_repository import LessonProgressRepository

class LessonService:
    """課程服務 - 僅定義介面，不實作"""

    def __init__(self, lesson_progress_repository: LessonProgressRepository):
        self.lesson_progress_repository = lesson_progress_repository

    def update_video_progress(self, user_id: str, lesson_id: int, progress: int) -> None:
        """更新影片進度 - 紅燈階段：空實作"""
        raise NotImplementedError("紅燈階段：尚未實作")
```

## Output 5（Environment 定義）

```python
# ${PY_ENV_FILE}

from types import SimpleNamespace
from app.repositories.lesson_progress_repository import LessonProgressRepository
from app.services.lesson_service import LessonService

def before_scenario(context, scenario):
    """每個 scenario 執行前初始化"""
    context.last_error = None
    context.query_result = None
    context.ids = {}
    context.memo = {}

    context.repos = SimpleNamespace()
    context.services = SimpleNamespace()

    context.repos.lesson_progress = LessonProgressRepository()

    context.services.lesson = LessonService(
        lesson_progress_repository=context.repos.lesson_progress
    )

def after_scenario(context, scenario):
    """每個 scenario 執行後清理"""
    context.last_error = None
    context.query_result = None
    context.ids.clear()
    context.memo.clear()
```

## 預期結果：測試執行會失敗（紅燈）

```bash
$ behave ${PY_TEST_FEATURES_DIR}/

Feature: 課程平台 - 增加影片進度

  Scenario: 成功增加影片進度
    Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"  # passes
    When 用戶 "Alice" 更新課程 1 的影片進度為 80%              # fails
      NotImplementedError: 紅燈階段：尚未實作

Failing scenarios:
  tests/features/03-增加影片進度.dsl.feature:6  成功增加影片進度

0 features passed, 1 failed, 0 skipped
0 scenarios passed, 1 failed, 0 skipped
```

**這就是紅燈**：
- Step Definition 完整實作
- 介面定義完整（類別、方法、參數）
- environment.py 定義完整（context 初始化）
- 業務邏輯未實作（拋出 NotImplementedError）
- 測試執行會失敗

---

# 專案結構

```
${PY_APP_DIR}/
├── __init__.py
├── models/
│   ├── __init__.py
│   └── lesson_progress.py        # Aggregate
├── repositories/
│   ├── __init__.py
│   └── lesson_progress_repository.py  # FakeRepository（NotImplementedError）
├── services/
│   ├── __init__.py
│   └── lesson_service.py         # Service（NotImplementedError）
└── exceptions.py

${ENTITY_SPECS_DIR}/
└── erm.dbml                       # DBML 規格

${PY_TEST_FEATURES_DIR}/
├── environment.py                 # Context 初始化
├── steps/                         # Step Definitions
└── *.feature                      # Feature 檔案
```

---

# Critical Rules

### R1: Step Definition 必須完整
Step Definition 邏輯必須完整實作，不能只有 `pass`。

### R2: 介面定義必須完整，但不實作
類別和方法簽名完整，但內部不實作業務邏輯。

```python
# 正確：定義完整，不實作
class LessonService:
    def update_video_progress(self, user_id: str, lesson_id: int, progress: int) -> None:
        raise NotImplementedError("紅燈階段：尚未實作")

# 錯誤：實作了業務邏輯
class LessonService:
    def update_video_progress(self, user_id: str, lesson_id: int, progress: int) -> None:
        current = self.repository.find(user_id, lesson_id)
        current.progress = progress
        self.repository.save(current)
```

### R3: environment.py 必須正確定義
所有 Step Definition 需要的 repos/services 都必須在 `${PY_ENV_FILE}` 中初始化。

### R4: 檔案結構正確
`${PY_APP_DIR}/` 下的 models/repositories/services 目錄結構必須完整。

### R5: 測試會失敗（紅燈）
紅燈階段的測試執行後應該失敗，這是預期的結果。

### R6: 依賴透過 context 取得
所有依賴都從 `context.repos.*` / `context.services.*` 取得，不使用全域變數。

### R7: 狀態透過 context 共享
`last_error` 和 `query_result` 直接作為 context 屬性，不使用 dict。

```python
# 正確：直接使用 context 屬性
context.last_error = e
context.query_result = result

# 錯誤：使用 dict（那是 pytest-bdd 的做法）
last_error["error"] = e
```

---

# 完成條件

- 所有 Step Definition 完整實作（不再有 `pass`）
- Aggregate 類別定義完整
- FakeRepository 類別存在，所有方法拋出 `NotImplementedError`
- Service 類別存在，所有方法拋出 `NotImplementedError`
- `${PY_ENV_FILE}` 正確初始化所有 repos/services
- 執行 `behave ${PY_TEST_FEATURES_DIR}/{feature_file}` 後測試失敗（紅燈）
- Feature File 最上方的 `@ignore` tag 已移除
