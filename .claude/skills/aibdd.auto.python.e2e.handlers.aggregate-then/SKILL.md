---
name: aibdd.auto.python.e2e.handlers.aggregate-then
description: 當在 .isa.feature 這類 ISA Gherkin 測試中驗證「資料庫中應存在某實體資料」，務必參考此規範。
user-invocable: false
---

# Aggregate-Then-Handler (E2E Behave Version)

## Trigger
Then 語句驗證**Aggregate 的屬性狀態**（從資料庫查詢）

**識別規則**：
- 驗證實體的屬性值（而非 API 回傳值）
- 描述「某個東西的某個屬性應該是某個值」
- 常見句型（非窮舉）：「在...的...應為」「的...應為」「應包含」

**通用判斷**：如果 Then 是驗證 Command 操作後的資料狀態（需要從資料庫查詢），就使用此 Handler

## Task
使用 Repository 從資料庫查詢 Aggregate → Assert 屬性值

## E2E 特色
- 使用 SQLAlchemy Repository 從真實 PostgreSQL 查詢
- 根據 Gherkin 明確提到的欄位進行查詢
- 驗證 Aggregate 的狀態（而非 API response）
- 從 context.db_session 取得資料庫連線

---

## Steps

1. 從 context 取得 db_session
2. 識別 Aggregate 名稱
3. 從 Gherkin 提取查詢條件（通常是複合主鍵）
4. 使用 Repository 查詢 Aggregate
5. Assert Aggregate 的屬性值

---

## Pattern Examples (Python Behave)

### 驗證單一 Aggregate

```gherkin
And 用戶 "Alice" 的購物車中商品 "PROD-001" 的數量應為 2
```

```python
from behave import then
from app.repositories.cart_repository import CartRepository


@then('用戶 "{user_name}" 的購物車中商品 "{product_id}" 的數量應為 {quantity:d}')
def step_impl(context, user_name, product_id, quantity):
    # 從 context 取得 db_session
    db_session = context.db_session
    repository = CartRepository(db_session)

    # 取得用戶 ID
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    # 使用 Repository 查詢 Aggregate
    cart_item = repository.find_by_user_and_product(
        user_id=user_id,
        product_id=product_id
    )

    # Assert 屬性值
    assert cart_item is not None, f"找不到購物車項目"
    assert cart_item.quantity == quantity, f"預期數量 {quantity}，實際 {cart_item.quantity}"
```

### 驗證多個屬性

```gherkin
And 用戶 "Alice" 在課程 1 的進度應為 80%，狀態應為 "進行中"
```

```python
from behave import then
from app.repositories.lesson_progress_repository import LessonProgressRepository


@then('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度應為 {progress:d}%，狀態應為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    db_session = context.db_session
    repository = LessonProgressRepository(db_session)

    # 狀態映射（中文 → 英文 enum）
    status_mapping = {
        "進行中": "IN_PROGRESS",
        "已完成": "COMPLETED",
        "未開始": "NOT_STARTED",
    }
    expected_status = status_mapping.get(status, status)

    # 取得用戶 ID
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    # 查詢 Aggregate
    progress_entity = repository.find_by_user_and_lesson(
        user_id=user_id,
        lesson_id=lesson_id
    )

    # Assert 多個屬性
    assert progress_entity is not None, f"找不到課程進度"
    assert progress_entity.progress == progress, f"預期進度 {progress}%，實際 {progress_entity.progress}%"
    assert progress_entity.status == expected_status, f"預期狀態 {expected_status}，實際 {progress_entity.status}"
```

### 驗證 Aggregate 存在

```gherkin
And 訂單 "ORDER-123" 應存在
```

```python
from behave import then
from app.repositories.order_repository import OrderRepository


@then('訂單 "{order_id}" 應存在')
def step_impl(context, order_id):
    db_session = context.db_session
    repository = OrderRepository(db_session)

    order = repository.find_by_id(order_id=order_id)
    assert order is not None, f"訂單 {order_id} 應該存在但找不到"
```

### 驗證 Aggregate 不存在

```gherkin
And 購物車中應不存在商品 "PROD-001"
```

```python
from behave import then
from app.repositories.cart_repository import CartRepository


@then('購物車中應不存在商品 "{product_id}"')
def step_impl(context, product_id):
    db_session = context.db_session
    repository = CartRepository(db_session)

    cart_item = repository.find_by_product(product_id=product_id)
    assert cart_item is None, f"商品 {product_id} 不應該存在但找到了"
```

### 驗證進度（常見情境）

```gherkin
And 用戶 "Alice" 在課程 1 的進度應為 80%
```

```python
from behave import then
from app.repositories.lesson_progress_repository import LessonProgressRepository


@then('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度應為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    db_session = context.db_session
    repository = LessonProgressRepository(db_session)

    # 取得用戶 ID
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    # 查詢並驗證
    progress_entity = repository.find_by_user_and_lesson(
        user_id=user_id,
        lesson_id=lesson_id
    )
    assert progress_entity is not None, f"找不到課程進度"
    assert progress_entity.progress == progress, f"預期進度 {progress}%，實際 {progress_entity.progress}%"
```

---

## Query Strategy

### 根據 Gherkin 明確提到的欄位查詢

**規則**：只使用 Gherkin 中明確提到的欄位來查詢 Aggregate

**範例 1：複合主鍵查詢**

```gherkin
And 用戶 "Alice" 的購物車中商品 "PROD-001" 的數量應為 2
```

從 Gherkin 提取：
- 用戶: "Alice" → user_id（從 context.ids 取得）
- 商品: "PROD-001" → product_id

查詢方法：
```python
repository.find_by_user_and_product(user_id=user_id, product_id="PROD-001")
```

**範例 2：單一主鍵查詢**

```gherkin
And 訂單 "ORDER-123" 的狀態應為 "已付款"
```

從 Gherkin 提取：
- 訂單: "ORDER-123" → order_id

查詢方法：
```python
repository.find_by_id(order_id="ORDER-123")
```

---

## Repository Query Methods

### 命名規則

Repository 的查詢方法命名應該清晰表達查詢條件：

| Gherkin 查詢條件 | Repository 方法 |
|----------------|----------------|
| 用戶 "Alice" 在課程 1 | find_by_user_and_lesson(user_id, lesson_id) |
| 訂單 "ORDER-123" | find_by_id(order_id) |
| 商品 "PROD-001" | find_by_product_id(product_id) |
| 用戶 "Alice" 的所有訂單 | find_all_by_user(user_id) |

### Repository 實作範例

```python
# app/repositories/lesson_progress_repository.py

from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.lesson_progress import LessonProgress


class LessonProgressRepository:
    """課程進度 Repository"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, progress: LessonProgress) -> None:
        """保存課程進度"""
        self.session.merge(progress)
        self.session.commit()

    def find_by_user_and_lesson(
        self,
        user_id: str,
        lesson_id: int
    ) -> Optional[LessonProgress]:
        """根據用戶和課程查詢進度"""
        return self.session.query(LessonProgress).filter_by(
            user_id=user_id,
            lesson_id=lesson_id
        ).first()

    def find_all_by_user(self, user_id: str) -> List[LessonProgress]:
        """查詢用戶的所有課程進度"""
        return self.session.query(LessonProgress).filter_by(
            user_id=user_id
        ).all()
```

---

## State Mapping

**目的**: 將 Gherkin 中的中文業務術語映射到 DBML enum 值

| 中文範例 | Enum 範例 | 適用情境 |
|---------|----------|---------|
| 進行中 | IN_PROGRESS | 進度、狀態 |
| 已完成 | COMPLETED | 進度、狀態 |
| 未開始 | NOT_STARTED | 進度、狀態 |
| 已交付 | DELIVERED | 課程狀態 |
| 已付款 | PAID | 訂單、付款 |
| 待付款 | PENDING | 訂單、付款 |

```python
# ✅ 正確：使用英文 enum
assert progress_entity.status == "IN_PROGRESS"

# ❌ 錯誤：使用中文
assert progress_entity.status == "進行中"
```

---

## Critical Rules

### R1: 使用 Repository 查詢
必須使用 Repository 的查詢方法，不直接使用 Session。

```python
# ✅ 正確：使用 Repository
progress_entity = repository.find_by_user_and_lesson(
    user_id=user_id,
    lesson_id=lesson_id
)

# ❌ 錯誤：直接使用 Session
progress_entity = context.db_session.query(LessonProgress).filter_by(...).first()
```

### R2: 只驗證 Gherkin 提到的欄位
只 assert Gherkin 中明確提到的屬性。

```python
# Gherkin: And 用戶 "Alice" 在課程 1 的進度應為 80%

# ✅ 正確：只驗證 progress
assert progress_entity.progress == 80

# ❌ 錯誤：驗證額外的欄位
assert progress_entity.progress == 80
assert progress_entity.updated_at is not None  # Gherkin 沒提到
```

### R3: 中文狀態映射到英文 enum
```python
# ✅ assert progress_entity.status == "IN_PROGRESS"
# ❌ assert progress_entity.status == "進行中"
```

### R4: 使用完整的查詢條件
根據 Gherkin 提到的所有條件進行查詢。

```python
# Gherkin: And 用戶 "Alice" 在課程 1 的進度應為 80%

# ✅ 正確：使用完整的查詢條件
repository.find_by_user_and_lesson(user_id=user_id, lesson_id=1)

# ❌ 錯誤：缺少查詢條件
repository.find_by_lesson(lesson_id=1)  # 沒有指定用戶
```

### R5: 驗證 Aggregate 存在性
如果 Gherkin 要求驗證存在或不存在，要明確檢查。

```python
# Gherkin: And 訂單 "ORDER-123" 應存在

# ✅ 正確：檢查不為 None
order = repository.find_by_id(order_id="ORDER-123")
assert order is not None, "訂單應該存在"

# ❌ 錯誤：沒有檢查存在性，直接訪問屬性可能報錯
order = repository.find_by_id(order_id="ORDER-123")
assert order.status == "PAID"  # 如果 order 是 None 會報錯
```

### R6: 從 context.db_session 取得 Session
必須從 context 取得 db_session。

```python
# ✅ 正確：從 context 取得
db_session = context.db_session
repository = LessonProgressRepository(db_session)

# ❌ 錯誤：自己創建 session
repository = LessonProgressRepository(Session())
```

### R7: 從 context.ids 取得用戶 ID
查詢時使用 context.ids 取得之前儲存的用戶 ID。

```python
# ✅ 正確：從 context.ids 取得
if user_name not in context.ids:
    raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
user_id = context.ids[user_name]

# ❌ 錯誤：直接使用用戶名稱
user_id = user_name  # 可能不是真正的 ID
```

### R8: 從資料庫查詢，不使用 API response
Aggregate-Then-Handler 驗證的是資料庫狀態，不是 API response。

```python
# ✅ 正確：從資料庫查詢
progress_entity = repository.find_by_user_and_lesson(user_id=user_id, lesson_id=1)
assert progress_entity.progress == 80

# ❌ 錯誤：使用 API response
response = context.last_response
data = response.json()
assert data["progress"] == 80  # 這是 ReadModel-Then-Handler 的工作
```

### R9: Assert 訊息要清晰
提供清晰的 assert 失敗訊息，方便除錯。

```python
# ✅ 正確：清晰的訊息
assert progress_entity.progress == progress, f"預期進度 {progress}%，實際 {progress_entity.progress}%"

# ❌ 錯誤：沒有訊息
assert progress_entity.progress == progress
```

---

## 與 ReadModel-Then-Handler 的區別

| 面向 | Aggregate-Then-Handler | ReadModel-Then-Handler |
|------|-------------------|----------------------|
| 驗證對象 | 資料庫中的 Aggregate | API response 的內容 |
| 資料來源 | SQLAlchemy Repository | context.last_response |
| 使用時機 | Command 操作後驗證狀態 | Query 操作後驗證回傳值 |
| 範例 | And 用戶 "Alice" 在課程 1 的進度應為 80% | And 查詢結果應包含進度 80% |

---

## 驗證列表（List）

如果 Aggregate 是列表（如「用戶的所有訂單」），使用 `find_all_*` 方法。

```gherkin
And 用戶 "Alice" 應有 2 個課程進度記錄
```

```python
@then('用戶 "{user_name}" 應有 {count:d} 個課程進度記錄')
def step_impl(context, user_name, count):
    db_session = context.db_session
    repository = LessonProgressRepository(db_session)

    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    progress_list = repository.find_all_by_user(user_id=user_id)
    assert len(progress_list) == count, f"預期 {count} 個記錄，實際 {len(progress_list)} 個"
```

---

**文件建立日期**：2025-01-20
**文件版本**：E2E Behave BDD Version 1.0
**適用框架**：Python + Behave + SQLAlchemy + Testcontainers
