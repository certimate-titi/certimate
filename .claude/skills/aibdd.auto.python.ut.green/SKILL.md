---
name: aibdd.auto.python.ut.green
description: Python UT Stage 3：綠燈階段。實作 FakeRepository（dict-based）+ Service 業務邏輯。Trial-and-error 循環直到測試通過。可被 /python-ut 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${PY_TEST_FEATURES_DIR}/**/*.feature, ${PY_STEPS_DIR}/**/*.py, ${PY_REPOSITORIES_DIR}/fake_*.py, ${PY_SERVICES_DIR}/**/*.py
output: ${PY_REPOSITORIES_DIR}/fake_*.py（完整實作）, ${PY_SERVICES_DIR}/**/*.py（完整實作）
---

# 角色

BDD 綠燈階段協調器，負責讓紅燈階段的失敗測試變成通過。

**核心任務**：實作最簡單的業務邏輯，讓測試從紅燈（失敗）變成綠燈（通過）。

---

# 入口條件（雙模式）

## 模式 A：獨立使用

使用者直接調用 `/python-ut-green`。

1. 詢問目標 Feature File（若使用者未在 argument 帶入）
2. 確認紅燈階段產出已存在（FakeRepository + Service 有 NotImplementedError）
3. 執行綠燈流程

## 模式 B：被 /python-ut 調用

接收參數：Feature File 路徑。直接執行綠燈流程。

---

# 綠燈階段的核心原則

## 可以做的事

- 實作 **FakeRepository**（使用 dict 模擬資料庫）
- 實作 **Service 業務邏輯**（最簡單能通過測試的邏輯）
- 建立 **自定義例外類別**（如 `InvalidStateError`、`NotFoundError`）
- 讓測試通過

## 不可以做的事

- **不要過度設計**
- **不要加入測試沒有要求的功能**
- **不要優化程式碼**（那是重構階段的事）

---

# 工作流程

## 步驟 1: 執行測試，確認紅燈

```bash
behave ${PY_TEST_FEATURES_DIR}/{feature_file}
```

**預期結果**：測試失敗（因為 Service/Repository 拋出 `NotImplementedError`）

## 步驟 2: 實作 FakeRepository

找到紅燈階段建立的 Repository 類別，把 `NotImplementedError` 替換成實際的 Fake 實作。

**FakeRepository 的特點**：
- 使用 Python `dict` 作為資料儲存（`self._store = {}`）
- 不需要資料庫連線
- 測試執行快速
- 透過 `${PY_ENV_FILE}` 初始化並掛到 `context.repos.*`

## 步驟 3: 實作 Service 業務邏輯

找到紅燈階段建立的 Service 類別，把 `NotImplementedError` 替換成實際的業務邏輯。

**原則**：
- 只寫能讓測試通過的最簡單邏輯
- 不要預先考慮邊界情況（除非測試有涵蓋）
- 不要優化（那是重構階段的事）

## 步驟 4: 執行測試，確認綠燈

```bash
behave ${PY_TEST_FEATURES_DIR}/{feature_file}
```

**預期結果**：測試通過（綠燈）

**如果測試仍然失敗**：進入 trial-and-error 循環：
1. 閱讀錯誤訊息
2. 修正 FakeRepository 或 Service
3. 重新執行測試
4. 重複直到通過

## 步驟 5: 執行回歸測試

```bash
behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore
```

**所有測試都必須通過**。這個命令會執行所有沒有 `@ignore` 標籤的 features，確保：
1. 新實作的功能測試通過
2. 沒有破壞既有的功能（回歸測試）
3. 所有已移除 `@ignore` 的 features 都保持綠燈

如果有任何測試失敗，必須修正後重新執行，直到全部通過為止。

---

# FakeRepository 範例

## 紅燈階段的 Repository（NotImplementedError）

```python
# ${PY_REPOSITORIES_DIR}/lesson_progress_repository.py（紅燈階段）

from typing import Optional
from app.models.lesson_progress import LessonProgress

class LessonProgressRepository:
    """課程進度 Repository - 僅定義介面，不實作"""

    def save(self, lesson_progress: LessonProgress) -> None:
        raise NotImplementedError("紅燈階段：尚未實作")

    def find(self, user_id: str, lesson_id: int) -> Optional[LessonProgress]:
        raise NotImplementedError("紅燈階段：尚未實作")
```

## 綠燈階段的 FakeRepository（實作）

```python
# ${PY_REPOSITORIES_DIR}/lesson_progress_repository.py（綠燈階段）

from typing import Optional, Dict, Tuple
from app.models.lesson_progress import LessonProgress

class LessonProgressRepository:
    """課程進度 Repository - Fake 實作（使用 dict 模擬資料庫）"""

    def __init__(self):
        # 使用 dict 作為資料儲存
        # Key: (user_id, lesson_id)，Value: LessonProgress
        self._store: Dict[Tuple[str, int], LessonProgress] = {}

    def save(self, lesson_progress: LessonProgress) -> None:
        """保存課程進度"""
        key = (lesson_progress.user_id, lesson_progress.lesson_id)
        self._store[key] = lesson_progress

    def find(self, user_id: str, lesson_id: int) -> Optional[LessonProgress]:
        """查詢課程進度"""
        key = (user_id, lesson_id)
        return self._store.get(key)

    def find_all(self) -> list:
        """查詢所有課程進度"""
        return list(self._store.values())

    def clear(self) -> None:
        """清空所有資料（用於測試重置）"""
        self._store.clear()
```

---

# Service 實作範例

## 紅燈階段的 Service（NotImplementedError）

```python
# ${PY_SERVICES_DIR}/lesson_service.py（紅燈階段）

from app.repositories.lesson_progress_repository import LessonProgressRepository

class LessonService:
    """課程服務 - 僅定義介面，不實作"""

    def __init__(self, lesson_progress_repository: LessonProgressRepository):
        self.lesson_progress_repository = lesson_progress_repository

    def update_video_progress(self, user_id: str, lesson_id: int, progress: int) -> None:
        raise NotImplementedError("紅燈階段：尚未實作")
```

## 綠燈階段的 Service（實作業務邏輯）

```python
# ${PY_SERVICES_DIR}/lesson_service.py（綠燈階段）

from app.models.lesson_progress import LessonProgress
from app.repositories.lesson_progress_repository import LessonProgressRepository
from app.exceptions import InvalidStateError

class LessonService:
    """課程服務"""

    def __init__(self, lesson_progress_repository: LessonProgressRepository):
        self.lesson_progress_repository = lesson_progress_repository

    def update_video_progress(self, user_id: str, lesson_id: int, progress: int) -> None:
        """更新影片進度"""
        # 查詢現有進度
        current = self.lesson_progress_repository.find(user_id, lesson_id)

        if current is None:
            # 如果不存在，建立新的進度記錄
            lesson_progress = LessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                progress=progress,
                status="IN_PROGRESS"
            )
            self.lesson_progress_repository.save(lesson_progress)
            return

        # 業務規則：進度只能遞增
        if progress < current.progress:
            raise InvalidStateError("進度不可倒退")

        # 更新進度
        current.progress = progress

        # 如果進度達到 100%，更新狀態
        if progress >= 100:
            current.status = "COMPLETED"

        self.lesson_progress_repository.save(current)
```

---

# 自定義例外

```python
# ${PY_APP_DIR}/exceptions.py

class InvalidStateError(Exception):
    """無效狀態例外"""
    pass

class InvalidArgumentError(Exception):
    """無效參數例外"""
    pass

class NotFoundError(Exception):
    """找不到資源例外"""
    pass
```

---

# Context 依賴注入（Behave 版）

**重要**：Service 和 Repository 都透過 `${PY_ENV_FILE}` 初始化並掛到 context。

## 為什麼使用 context？

1. **scenario 隔離**：每個 scenario 前重新初始化
2. **依賴統一管理**：所有依賴都在 environment.py 集中定義
3. **測試一致性**：Given/When/Then 都用同一個 repo/service 實例

## environment.py 範例

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

    # 初始化 repositories（Fake 實作）
    context.repos.lesson_progress = LessonProgressRepository()

    # 初始化 services（注入同一個 Repository 實例）
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

**關鍵點**：
- `context.repos.lesson_progress` 在同一個 scenario 中只建立一次
- `context.services.lesson` 依賴 `context.repos.lesson_progress`（同一個實例）
- Given 透過 `context.repos.lesson_progress.save()` 儲存的資料，Service 可以透過同一個 Repository 讀取到

---

# common_then（操作成功/失敗）

```python
# ${PY_STEPS_DIR}/common_then/success.py

from behave import then

@then("操作成功")
def step_impl(context):
    """驗證操作成功（沒有錯誤）"""
    assert context.last_error is None, \
        f"預期操作成功，但發生錯誤：{context.last_error}"
```

```python
# ${PY_STEPS_DIR}/common_then/failure.py

from behave import then

@then("操作失敗")
def step_impl(context):
    """驗證操作失敗（有錯誤）"""
    assert context.last_error is not None, \
        "預期操作失敗，但沒有發生錯誤"
```

---

# Complete Example

## 前置狀態（紅燈階段的產出）

**Feature File**：
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

**紅燈階段產出（已存在）**：
- `${PY_MODELS_DIR}/lesson_progress.py` — Aggregate 定義
- `${PY_REPOSITORIES_DIR}/lesson_progress_repository.py` — Repository 介面（NotImplementedError）
- `${PY_SERVICES_DIR}/lesson_service.py` — Service 介面（NotImplementedError）
- `${PY_STEPS_DIR}/lesson/*` — Step Definitions
- `${PY_ENV_FILE}` — Context 初始化

## 綠燈階段實作

1. 實作 FakeRepository（將 NotImplementedError 替換成 dict-based 實作）
2. 實作 Service 業務邏輯（將 NotImplementedError 替換成最簡邏輯）
3. 建立例外類別（如果需要）

## 執行測試

```bash
$ behave ${PY_TEST_FEATURES_DIR}/

Feature: 課程平台 - 增加影片進度

  Scenario: 成功增加影片進度
    Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"  # passes
    When 用戶 "Alice" 更新課程 1 的影片進度為 80%              # passes
    Then 操作成功                                              # passes
    And 用戶 "Alice" 在課程 1 的進度應為 80%                    # passes

  Scenario: 進度不可倒退
    Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"  # passes
    When 用戶 "Alice" 更新課程 1 的影片進度為 60%              # passes (捕獲錯誤)
    Then 操作失敗                                              # passes
    And 用戶 "Alice" 在課程 1 的進度應為 70%                    # passes

1 feature passed, 0 failed, 0 skipped
2 scenarios passed, 0 failed, 0 skipped
8 steps passed, 0 failed, 0 skipped, 0 undefined
```

---

# Critical Rules

### R1: 只寫能讓測試通過的最簡單邏輯
不要過度設計，不要預先考慮測試沒有涵蓋的情況。

### R2: FakeRepository 使用 dict
使用 Python dict 作為資料儲存（`self._store = {}`），不需要資料庫。

### R3: 依賴透過 environment.py 初始化
所有依賴都在 `${PY_ENV_FILE}` 的 `before_scenario` 初始化。

### R4: 共用 Repository 實例
`before_scenario` 確保同一個 scenario 中使用同一個 Repository 實例：
- Given 建資料用 `context.repos.lesson_progress.save()`
- Service 內部用同一個 `context.repos.lesson_progress`
- Then 查資料用 `context.repos.lesson_progress.find()`

### R5: 不要重構
綠燈階段只讓測試通過，程式碼優化是重構階段的事。

### R6: 狀態直接用 context 屬性
- `context.last_error` 直接賦值（不是 dict）
- `context.query_result` 直接賦值（不是 dict）

### R7: 必須執行完整回歸測試
**完成綠燈階段的唯一標準**：執行 `behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore` 後，所有測試都通過。沒有例外。

---

# 完成條件

- FakeRepository 使用 dict 完整實作所有方法
- Service 實作最簡單的業務邏輯
- 自定義例外類別已建立（如果需要）
- 執行 `behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore` 後所有測試通過
- 沒有破壞既有的功能（回歸測試通過）
