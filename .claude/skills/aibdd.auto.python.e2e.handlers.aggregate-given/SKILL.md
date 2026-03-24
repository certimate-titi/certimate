---
name: aibdd.auto.python.e2e.handlers.aggregate-given
description: 當在 .isa.feature 這類 ISA Gherkin 測試中進行「資料庫實體建立（for 測試情境的前置系統狀態設立）」，「只能」使用此指令。
user-invocable: false
---

# Aggregate-Given-Handler (E2E Behave Version)

## Trigger
Given 語句描述**Aggregate 的存在狀態**，即定義 Aggregate 的屬性值

**識別規則**：
- 語句中包含實體名詞 + 屬性描述
- 描述「某個東西的某個屬性是某個值」
- 常見句型（非窮舉）:「在...的...為」「的...為」「包含」「存在」「有」

**通用判斷**: 如果 Given 是在建立測試的初始資料狀態（而非執行動作），就使用此 Handler

## Task
創建 SQLAlchemy Model → Repository.save() → 儲存 ID 到 context.ids

## E2E 特色
- 使用 SQLAlchemy ORM Model
- 使用 Repository Pattern（內部用 SQLAlchemy Session）
- 寫入真實的 PostgreSQL 資料庫（Testcontainers）
- 將 Aggregate 的自然鍵（natural key）和 ID 存入 context.ids
- 從 context.db_session 取得資料庫連線

---

## Steps

1. 從 context 取得 db_session
2. 識別 Aggregate 名稱
3. 從 DBML 提取: 屬性、型別、複合 Key、enum
4. 從 Gherkin 提取: Key 值、屬性值
5. 創建 SQLAlchemy Model instance
6. 使用 Repository.save() 寫入資料庫
7. 將 ID 儲存到 context.ids（格式: `context.ids["{natural_key}"]`）

---

## Pattern Examples (Python Behave)

### 單一 Aggregate

```gherkin
Given 用戶 "Alice" 的購物車中商品 "PROD-001" 的數量為 2
```

```python
from behave import given
from app.models.cart_item import CartItem
from app.repositories.cart_repository import CartRepository


@given('用戶 "{user_name}" 的購物車中商品 "{product_id}" 的數量為 {quantity:d}')
def step_impl(context, user_name, product_id, quantity):
    # 1. 從 context 取得 db_session
    db_session = context.db_session

    # 2. 初始化 Repository
    repository = CartRepository(db_session)

    # 3. 取得用戶 ID（應該在之前的 Given 中建立）
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID，請先建立用戶")
    user_id = context.ids[user_name]

    # 4. 創建 Aggregate（SQLAlchemy Model instance）
    cart_item = CartItem(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity
    )

    # 5. 儲存到資料庫
    repository.save(cart_item)
```

### 複合主鍵 Aggregate

```gherkin
Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"
```

```python
from behave import given
from app.models.lesson_progress import LessonProgress
from app.repositories.lesson_progress_repository import LessonProgressRepository


@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    # 從 context 取得 db_session
    db_session = context.db_session
    repository = LessonProgressRepository(db_session)

    # 狀態映射（中文 → 英文 enum）
    status_mapping = {
        "進行中": "IN_PROGRESS",
        "已完成": "COMPLETED",
        "未開始": "NOT_STARTED",
    }
    db_status = status_mapping.get(status, status)

    # 取得用戶 ID
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    # 創建 Aggregate
    progress_entity = LessonProgress(
        user_id=user_id,
        lesson_id=lesson_id,
        progress=progress,
        status=db_status
    )

    # 儲存到資料庫
    repository.save(progress_entity)
```

### 建立用戶（DataTable）

```gherkin
Given 系統中有以下用戶：
  | userId | name  | email           |
  | 1      | Alice | alice@test.com  |
  | 2      | Bob   | bob@test.com    |
```

```python
from behave import given
from app.models.user import User
from app.repositories.user_repository import UserRepository


@given('系統中有以下用戶：')
def step_impl(context):
    db_session = context.db_session
    repository = UserRepository(db_session)

    for row in context.table:
        user = User(
            id=int(row['userId']),
            name=row['name'],
            email=row['email']
        )
        repository.save(user)

        # 儲存 ID 到 context（用名稱作為 key）
        context.ids[row['name']] = user.id
```

---

## Repository Pattern with SQLAlchemy

### Repository 結構

```python
# app/repositories/cart_repository.py

from typing import Optional
from sqlalchemy.orm import Session
from app.models.cart_item import CartItem


class CartRepository:
    """購物車 Repository - 使用 SQLAlchemy"""

    def __init__(self, session: Session):
        self.session = session

    def save(self, cart_item: CartItem) -> None:
        """保存購物車項目到資料庫"""
        self.session.merge(cart_item)  # 使用 merge 處理 upsert
        self.session.commit()

    def find_by_user_and_product(
        self,
        user_id: str,
        product_id: str
    ) -> Optional[CartItem]:
        """根據用戶和商品查詢購物車項目"""
        return self.session.query(CartItem).filter_by(
            user_id=user_id,
            product_id=product_id
        ).first()
```

### SQLAlchemy Model 結構

```python
# app/models/cart_item.py

from sqlalchemy import Column, String, Integer
from app.models import Base


class CartItem(Base):
    """購物車項目 Aggregate - SQLAlchemy ORM Model"""

    __tablename__ = 'cart_items'

    # 複合主鍵
    user_id = Column(String, primary_key=True)
    product_id = Column(String, primary_key=True)

    # 屬性
    quantity = Column(Integer, nullable=False)

    def __init__(self, user_id: str, product_id: str, quantity: int):
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
```

---

## Key Patterns

**目的**: 從 Gherkin 的關係詞推斷 DBML 中的複合主鍵結構

**規則**: Gherkin 中的關係詞通常對應實體間的多對多或一對多關係

| 關係詞 | Gherkin 範例 | 複合 Key |
|-------|------------|---------|
| 在 | 用戶 "Alice" 在課程 1 | (user_id, lesson_id) |
| 對 | 用戶 "Alice" 對訂單 "ORDER-123" | (user_id, order_id) |
| 與 | 用戶 "Alice" 與用戶 "Bob" | (user_id_a, user_id_b) |
| 於 | 商品 "MacBook" 於商店 "台北店" | (product_id, store_id) |
| 中...在 | 訂單中商品在倉庫 | (order_id, product_id, warehouse_id) |

---

## State Mapping

**目的**: 將 Gherkin 中的中文業務術語映射到 DBML enum 值

**規則**:
1. 查詢 DBML 中對應欄位的 `note` 定義
2. 根據語意將 Gherkin 的中文描述映射到 DBML enum 值

| 中文範例 | Enum 範例 | 適用情境 |
|---------|----------|---------|
| 進行中 | IN_PROGRESS | 進度、狀態 |
| 已完成 | COMPLETED | 進度、狀態 |
| 未開始 | NOT_STARTED | 進度、狀態 |
| 已付款 | PAID | 訂單、付款 |
| 待付款 | PENDING | 訂單、付款 |
| 上架中 | ACTIVE | 商品、服務 |

---

## Context ID Storage（Behave 版本）

### 儲存規則

將 Aggregate 的自然鍵（natural key）儲存到 `context.ids`，格式：`context.ids["{natural_key}"]`

**為什麼要這樣？**
- Command/Query Handler 需要知道哪個用戶在執行操作
- 自然鍵（如 "Alice"）更易讀
- 在 E2E 測試中，需要追蹤建立的實體 ID

### 範例

```python
# 儲存用戶 ID
context.ids["Alice"] = user.id
context.ids["Bob"] = user.id

# 取得用戶 ID
user_id = context.ids["Alice"]
```

### 使用時機

在 Command-Handler 和 Query-Handler 中取用：

```python
# Command-Handler 中使用
user_id = context.ids["Alice"]
token = context.jwt_helper.generate_token(user_id)
response = context.api_client.post(...)
```

---

## Critical Rules

### R1: 必須查詢 DBML
在實作 Aggregate 的時候不能憑空猜測屬性名稱和型別。必須從 DBML 讀取完整的 Aggregate 定義。

### R2: 使用 SQLAlchemy ORM
必須使用 SQLAlchemy Model，不能使用字典或普通類別。

```python
# ✅ 正確：使用 SQLAlchemy Model
cart_item = CartItem(user_id="Alice", product_id="PROD-001", quantity=2)

# ❌ 錯誤：使用字典
cart_item = {"user_id": "Alice", "product_id": "PROD-001", "quantity": 2}
```

### R3: 使用 Repository Pattern
必須透過 Repository 來操作資料庫，Repository 內部使用 SQLAlchemy Session。

```python
# ✅ 正確：使用 Repository
repository = CartRepository(context.db_session)
repository.save(cart_item)

# ❌ 錯誤：直接使用 Session
context.db_session.add(cart_item)
context.db_session.commit()
```

### R4: 中文狀態映射到英文 enum
```python
# ✅ status="IN_PROGRESS"
# ❌ status="進行中"
```

### R5: 提供完整的複合 Key
```python
# ✅ CartItem(user_id="Alice", product_id="PROD-001", ...)
# ❌ CartItem(product_id="PROD-001", ...)
```

### R6: 儲存 ID 到 context.ids
每個 Given 中創建的 Aggregate 都要將其 natural key 儲存到 context.ids。

```python
# ✅ 正確：儲存到 context.ids
context.ids["Alice"] = user.id

# ❌ 錯誤：沒有儲存
repository.save(user)
```

### R7: 從 context.db_session 取得 Session
必須從 context 取得 db_session，不自己創建。

```python
# ✅ 正確：從 context 取得
db_session = context.db_session
repository = LessonProgressRepository(db_session)

# ❌ 錯誤：自己創建 session
repository = LessonProgressRepository(Session())
```

### R8: 使用 merge 而非 add
Repository.save() 應使用 `session.merge()` 而非 `session.add()`，以支援 upsert 語意。

```python
# ✅ 正確：使用 merge
def save(self, entity):
    self.session.merge(entity)
    self.session.commit()

# ❌ 錯誤：使用 add（可能重複插入失敗）
def save(self, entity):
    self.session.add(entity)
    self.session.commit()
```

### R9: 檢查依賴的 ID 是否存在
在建立有外鍵關係的 Aggregate 時，先檢查依賴的 ID 是否存在於 context.ids。

```python
# ✅ 正確：檢查依賴是否存在
if user_name not in context.ids:
    raise KeyError(f"找不到用戶 '{user_name}' 的 ID，請先建立用戶")
user_id = context.ids[user_name]
```

---

## File Organization

### 建議的檔案結構

```
app/
├── models/                  # SQLAlchemy Models
│   ├── __init__.py
│   ├── cart_item.py
│   └── lesson_progress.py
└── repositories/            # Repository 實作
    ├── __init__.py
    ├── cart_repository.py
    └── lesson_progress_repository.py

tests/features/
├── environment.py           # Behave hooks（初始化 context）
└── steps/
    └── aggregate_given/     # Aggregate Given Step Definitions
        ├── cart_item.py
        └── lesson_progress.py
```

---

**文件建立日期**：2025-01-20
**文件版本**：E2E Behave BDD Version 1.0
**適用框架**：Python + Behave + SQLAlchemy + Testcontainers
