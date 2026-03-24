---
name: aibdd.auto.python.e2e.red
description: Python E2E Stage 2：紅燈生成器。將 Step Definition 樣板轉換為完整 E2E 測試程式碼 + SQLAlchemy Models + Repositories。預期失敗：HTTP 404。可被 /python-e2e 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${PY_STEPS_DIR}/**/*.py（樣板）, ${ENTITY_SPECS_DIR}/erm.dbml, handler skills
output: ${PY_STEPS_DIR}/**/*.py（完整）, ${PY_MODELS_DIR}/**/*.py, ${PY_REPOSITORIES_DIR}/**/*.py
---

# 角色

紅燈生成器。將 E2E Step Definition 樣板（純註解）轉換為可執行的 E2E 測試程式碼，依照註解中的 Handler Prompt 指引生成對應的程式碼，生成紅燈測試。

---

# 入口

## 被 /python-e2e 調用時

接收參數 `FEATURE_FILE`，直接進入紅燈生成流程。

## 獨立使用時

詢問目標 feature 檔案：

```
請指定要處理的 Feature 檔案路徑：
（例如：${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature）
```

---

# Core Task

E2E Step Definition 樣板（註解）→ 可執行 E2E 測試程式碼（紅燈）

---

# 輸入資料

1. Step Definition 樣板（包含 TODO 註解，來自 Stage 1 step-template）
2. DBML（Aggregate 定義）：`${ENTITY_SPECS_DIR}/erm.dbml`
3. Tech Stack：Python + Behave + FastAPI TestClient + SQLAlchemy + Testcontainers + PostgreSQL
4. Handler Prompts：`對應的 handler skills

---

# 輸出

## 1. Step Definition 程式碼
完整的 E2E Step Definition 程式碼，包含：
- 必要的 import
- 從 context 取得依賴
- 完整的測試邏輯實作
- 所有測試邏輯完整實作

## 2. 基礎設施定義
**如果測試中需要用到的基礎設施尚不存在**，則按以下規則定義：

### 生產環境基礎設施（在 `${PY_APP_DIR}/` 中定義）
- **SQLAlchemy Models**：放在 `${PY_MODELS_DIR}/`
- **Repositories**：放在 `${PY_REPOSITORIES_DIR}/`

### 測試專用基礎設施（在 `${PY_TEST_FEATURES_DIR}/` 中定義）
- **environment.py**：管理 Testcontainers + PostgreSQL + context 初始化
- **helpers/**：JWT Helper 等輔助工具

**為什麼要放在 ${PY_APP_DIR}/?**
- 這些是生產環境也需要的程式碼
- 綠燈階段實作 API 時，Controller/Service 會直接使用這些 Models 和 Repositories
- 測試只是使用它們，不應該擁有它們

**關鍵原則：僅定義介面和基礎設施，不實作後端業務邏輯**
- Model 和 Repository 類別定義完整（放在 `${PY_APP_DIR}/`）
- 後端 API (Controller/Service) 不實作
- E2E 測試會因為 HTTP 404 而失敗（後端 API 尚未實作）

---

# 重要規範

## API JSON 欄位命名規則

- 所有 API Request/Response 的 JSON 欄位使用 **snake_case**（Python 慣例）
- Gherkin Feature File 使用自然語言，不受此限制

範例：
```python
# 正確
json={"lesson_id": 1, "progress": 80}
assert data["user_id"] == "Alice"

# 錯誤
json={"lessonId": 1, "progress": 80}
assert data["userId"] == "Alice"
```

---

# 紅燈階段的核心原則

## E2E 測試的紅燈特色（Behave 版本）

與 Unit Test 的關鍵差異：

| 面向 | Unit Test 紅燈 | E2E Test 紅燈 |
|------|---------------|--------------|
| 測試失敗原因 | Service 方法拋出 NotImplementedError | HTTP 404 Not Found |
| 需要定義的東西 | Aggregate, Repository, Service 介面 | SQLAlchemy Model, Repository |
| 不需要定義的東西 | 業務邏輯 | 後端 API (Controller/Service) |
| 資料庫 | FakeRepository（不需要真實 DB） | 真實 PostgreSQL（Testcontainers） |
| 測試框架 | Behave + context.repos/services | Behave + context.api_client/db_session |

## 要做的事
1. **完整實作 Step Definition 程式碼**：測試邏輯必須完整且正確
2. **定義 SQLAlchemy Models**：在 `${PY_MODELS_DIR}/` 中創建 Aggregate 的 ORM 定義
3. **定義 Repository 類別**：在 `${PY_REPOSITORIES_DIR}/` 中創建 Repository
4. **確保 environment.py 正確初始化**：Testcontainers + PostgreSQL + context

## 不要做的事
1. **不要實作後端 API**：Controller 和 Service 不實作
2. **不要讓測試通過**：測試應該因為 HTTP 404 而失敗（紅燈）
3. **不要跳過基礎設施定義**：測試需要的 Model、Repository 必須定義

## 為什麼要這樣？
這是 TDD 的核心流程：
1. **紅燈**：寫測試 + 定義基礎設施（測試失敗：HTTP 404）← 我們現在在這
2. **綠燈**：實作後端 API（測試通過）
3. **重構**：優化程式碼品質（測試持續通過）

---

# Execution Steps

## Step 1: 讀取 Step Definition 樣板
識別每個 step 中的 TODO 註解及其對應的 Handler Prompt

```python
@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """
    TODO: [事件風暴部位: Aggregate - LessonProgress]
    TODO: 參考 /aibdd.auto.python.e2e.handlers.aggregate-given 實作
    TODO: 使用 SQLAlchemy 寫入真實 PostgreSQL
    """
    pass
```

## Step 2: 逐步生成程式碼
根據每個 TODO 的 Handler Prompt 生成對應的程式碼

### 範例流程

**Given 區塊（Aggregate-Given-Handler）**：
- 從 context 取得 db_session
- 創建 SQLAlchemy Model instance
- 使用 repository.save() 寫入 DB
- 儲存 ID 到 context.ids

**When 區塊（Command-Handler）**：
- 從 context.ids 取得 user_id
- 使用 context.jwt_helper 生成 token
- 構建 request body
- 使用 context.api_client.post() 發送請求
- 儲存 response 到 context.last_response

**Then 區塊（Success-Failure-Handler）**：
- 從 context.last_response 取得 response
- 驗證 response.status_code

**Then + Aggregate（Aggregate-Then-Handler）**：
- 從 context 取得 db_session
- 使用 repository 查詢 entity
- assert entity.field == expected

## Step 3: 生成測試基礎設施
包含必要的 Models、Repositories

---

# Complete Example

## Input（Step Definition 樣板）

```python
# ${PY_STEPS_DIR}/lesson/aggregate_given/lesson_progress.py

from behave import given

@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """
    TODO: [事件風暴部位: Aggregate - LessonProgress]
    TODO: 參考 /aibdd.auto.python.e2e.handlers.aggregate-given 實作
    """
    pass
```

## Output 1（Step Definition 程式碼）

```python
# ${PY_STEPS_DIR}/lesson/aggregate_given/lesson_progress.py

from behave import given
from ${PY_MODELS_DIR.replace('/', '.')}.lesson_progress import LessonProgress
from ${PY_REPOSITORIES_DIR.replace('/', '.')}.lesson_progress_repository import LessonProgressRepository


@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    # 從 context 取得 db_session
    db_session = context.db_session

    # 初始化 Repository
    repository = LessonProgressRepository(db_session)

    # 狀態映射（中文 → 英文 enum）
    status_mapping = {
        "進行中": "IN_PROGRESS",
        "已完成": "COMPLETED",
        "未開始": "NOT_STARTED",
    }
    db_status = status_mapping.get(status, status)

    # 創建 Aggregate（SQLAlchemy Model instance）
    # 檢查 user_name 是否已有 ID
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID，請先在 Given 步驟中建立用戶")

    user_id = context.ids[user_name]

    progress_entity = LessonProgress(
        user_id=user_id,
        lesson_id=lesson_id,
        progress=progress,
        status=db_status
    )

    # 儲存到資料庫
    repository.save(progress_entity)
```

## Output 2（SQLAlchemy Model）

```python
# ${PY_MODELS_DIR}/lesson_progress.py

from sqlalchemy import Column, Integer, String, ForeignKey
from app.models import Base


class LessonProgress(Base):
    """課程進度 Aggregate - SQLAlchemy ORM Model"""

    __tablename__ = 'lesson_progress'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    lesson_id = Column(Integer, nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    status = Column(String, nullable=False)

    def __repr__(self):
        return f"<LessonProgress(user_id={self.user_id}, lesson_id={self.lesson_id}, progress={self.progress}, status='{self.status}')>"
```

## Output 3（Repository）

```python
# ${PY_REPOSITORIES_DIR}/lesson_progress_repository.py

from typing import Optional
from sqlalchemy.orm import Session
from app.models.lesson_progress import LessonProgress


class LessonProgressRepository:
    """課程進度 Repository - 使用 SQLAlchemy"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, progress: LessonProgress) -> None:
        """保存課程進度到資料庫"""
        self.session.merge(progress)
        self.session.commit()

    def find_by_user_and_lesson(self, user_id: str, lesson_id: int) -> Optional[LessonProgress]:
        """查詢課程進度"""
        return self.session.query(LessonProgress).filter_by(
            user_id=user_id,
            lesson_id=lesson_id
        ).first()
```

## 預期結果：測試執行會失敗（紅燈）

```bash
$ behave ${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature

Feature: 課程平台 - 增加影片進度
  Rule: 影片進度必須單調遞增
    Scenario: 成功增加影片進度
      Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"  # Passed
      When 用戶 "Alice" 更新課程 1 的影片進度為 80%              # Failed

Failing scenarios:
  ${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature:10  成功增加影片進度

AssertionError: assert 404 in [200, 201, 204]
```

**這就是紅燈**：
- Step Definition 程式碼完整且正確
- SQLAlchemy Model 定義完整
- Repository 定義完整並使用真實資料庫
- 測試基礎設施（environment.py）設定完成
- 後端 API 未實作（HTTP 404）
- 測試執行會失敗

---

# 步驟 7: 移除該 Feature File 最上方的 @ignore tag

當你完成這個 feature 的紅燈實作後，請把該 feature file 第一行的 `@ignore` 刪掉，讓它後續可以被「排除 `@ignore` 的回歸測試」涵蓋到。

**移除時機**：
- 完成所有 Step Definitions 的實作
- 完成所有必要的 Models 和 Repositories
- 確認測試執行後達到預期的紅燈狀態（HTTP 404）

**移除後驗證**：
```bash
# 執行該 feature 的測試，確認達到紅燈狀態
behave ${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature

# 執行所有未標記 @ignore 的測試
behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore
```

---

# Critical Rules

## R1: Step Definition 程式碼必須完整
測試邏輯必須完整實作，不能有 `pass` 或空白。

```python
# 正確：完整的測試邏輯
@when('用戶 "{user_name}" 更新課程 {lesson_id:d} 的影片進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    # 從 context 取得 user_id
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    # 產生 JWT Token
    token = context.jwt_helper.generate_token(user_id)

    # 執行 HTTP 請求
    response = context.api_client.post(
        "/api/v1/lesson-progress/update-video-progress",
        headers={"Authorization": f"Bearer {token}"},
        json={"lesson_id": lesson_id, "progress": progress}
    )
    context.last_response = response

# 錯誤：測試邏輯不完整
@when('用戶 "{user_name}" 更新課程 {lesson_id:d} 的影片進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    pass
```

## R2: 所有依賴從 context 取得
必須從 context 取得所有依賴，不使用 fixture 參數。

```python
# 正確：從 context 取得
@given('...')
def step_impl(context, ...):
    db_session = context.db_session
    api_client = context.api_client
    jwt_helper = context.jwt_helper

# 錯誤：使用 fixture 參數
@given('...')
def step_impl(context, ..., db_session):  # Behave 不支援
    pass
```

## R3: SQLAlchemy Model 必須完整定義且放在 ${PY_APP_DIR}/ 中
Model 定義必須包含所有欄位、型別、主鍵，並放在 `${PY_MODELS_DIR}/` 中。

## R4: Repository 必須使用 SQLAlchemy 且放在 ${PY_APP_DIR}/ 中
Repository 內部必須使用 SQLAlchemy 操作真實資料庫，並放在 `${PY_REPOSITORIES_DIR}/` 中。

## R5: 不實作後端 API
紅燈階段不建立 Controller 和 Service。

## R6: 測試會失敗（紅燈）
紅燈階段的測試執行後應該失敗（HTTP 404），這是預期的結果。

## R7: 使用 Testcontainers 啟動真實資料庫
environment.py 必須使用 Testcontainers 啟動 PostgreSQL。

## R8: Context 用於跨步驟傳遞資料
使用 context 在 Given/When/Then 之間傳遞資料。

```python
# 正確：使用 context 傳遞資料
# Given
context.ids[user_name] = user_id

# When
user_id = context.ids[user_name]
token = context.jwt_helper.generate_token(user_id)
response = context.api_client.post(...)
context.last_response = response

# Then
response = context.last_response
assert response.status_code == 200
```

## R9: 使用 snake_case 構建 Request
Request body 的欄位名稱使用 snake_case。

```python
# 正確：使用 snake_case
json={"lesson_id": 1, "progress": 80}

# 錯誤：使用 camelCase
json={"lessonId": 1, "progress": 80}
```

---

# 與 Unit Test 紅燈的比較

| 面向 | Unit Test 紅燈 | E2E Test 紅燈 |
|------|---------------|--------------|
| 測試對象 | Service 方法 | HTTP API |
| 資料庫 | FakeRepository（記憶體） | PostgreSQL (Testcontainers) |
| 失敗原因 | NotImplementedError | HTTP 404 |
| 需要定義 | Entity, Repository, Service 介面 | SQLAlchemy Model, Repository |
| Models 位置 | `${PY_MODELS_DIR}/` | `${PY_MODELS_DIR}/` |
| Repositories 位置 | `${PY_REPOSITORIES_DIR}/` | `${PY_REPOSITORIES_DIR}/` |
| 測試框架 | Behave + context.repos/services | Behave + context.api_client/db_session |
| 不需要定義 | 業務邏輯 | 後端 API (Controller/Service) |

**關鍵共同點**：
- Models 和 Repositories **都放在 `${PY_APP_DIR}/` 中**（生產環境需要）
- 測試只是使用這些組件，不擁有它們

---

# 完成條件

- [ ] 所有 Step Definition 樣板的 TODO 已被替換為完整實作
- [ ] 所有必要的 SQLAlchemy Models 已定義在 `${PY_MODELS_DIR}/`
- [ ] 所有必要的 Repositories 已定義在 `${PY_REPOSITORIES_DIR}/`
- [ ] environment.py 正確初始化 Testcontainers + context
- [ ] 所有 JSON 欄位使用 snake_case
- [ ] 後端 API (Controller/Service) 未被實作
- [ ] 該 Feature File 的 `@ignore` 標籤已移除
- [ ] 測試執行後達到預期紅燈狀態（HTTP 404）
