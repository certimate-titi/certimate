---
name: aibdd.auto.python.e2e.handlers.readmodel-then
description: 當在 .isa.feature 這類 ISA Gherkin 測試中驗證「API 的回應結果應該有什麼內容」時，「只能」使用此指令。
user-invocable: false
---

# ReadModel-Then-Handler (E2E Behave Version)

## Trigger
Then 語句驗證**Query 的 API 回傳結果**

**識別規則**:
- 前提: When 是 Query 操作（已接收 response）
- 驗證的是 API 回傳值（而非資料庫中的狀態）
- 常見句型（非窮舉）:「查詢結果應」「回應應」「應返回」「結果包含」

**通用判斷**: 如果 Then 是驗證 Query 操作的回傳值，就使用此 Handler

## Task
從 context.last_response 取得 response → assert response.json() 的內容

## E2E 特色
- 從 context.last_response 取得 HTTP response
- 使用 response.json() 解析回傳的 JSON
- 驗證 API 回傳值（而非資料庫狀態）

## Critical Rule
不重新調用 API，使用 When 中儲存的 response

---

## Pattern Examples (Python Behave)

### 驗證單一記錄

```gherkin
When 用戶 "Alice" 查詢課程 1 的進度
Then 操作成功
And 查詢結果應包含進度 80，狀態為 "進行中"
```

```python
from behave import then


@then('查詢結果應包含進度 {progress:d}，狀態為 "{status}"')
def step_impl(context, progress, status):
    # 從 context.last_response 取得 response
    response = context.last_response
    data = response.json()

    # 狀態映射（中文 → 英文 enum）
    status_mapping = {
        "進行中": "IN_PROGRESS",
        "已完成": "COMPLETED",
        "未開始": "NOT_STARTED",
    }
    expected_status = status_mapping.get(status, status)

    # 驗證欄位
    assert data["progress"] == progress, f"預期進度 {progress}，實際 {data['progress']}"
    assert data["status"] == expected_status, f"預期狀態 {expected_status}，實際 {data['status']}"
```

### 驗證列表

```gherkin
When 用戶 "Alice" 查詢購物車中的所有商品
Then 操作成功
And 查詢結果應包含 2 個商品
And 第一個商品的 ID 應為 "PROD-001"，數量為 2
```

```python
from behave import then


@then('查詢結果應包含 {count:d} 個商品')
def step_impl(context, count):
    response = context.last_response
    data = response.json()

    items = data.get("items", [])
    assert len(items) == count, f"預期 {count} 個商品，實際 {len(items)} 個"


@then('第一個商品的 ID 應為 "{product_id}"，數量為 {quantity:d}')
def step_impl(context, product_id, quantity):
    response = context.last_response
    data = response.json()

    items = data.get("items", [])
    assert len(items) > 0, "商品列表為空"

    first_item = items[0]
    assert first_item["product_id"] == product_id, f"預期 {product_id}，實際 {first_item['product_id']}"
    assert first_item["quantity"] == quantity, f"預期數量 {quantity}，實際 {first_item['quantity']}"
```

### 驗證嵌套結構

```gherkin
When 用戶 "Alice" 查詢訂單 "ORDER-123" 的詳情
And 查詢結果應包含用戶名稱為 "Alice"
And 查詢結果應包含訂單狀態為 "已付款"
And 查詢結果應包含金額 1000
```

```python
from behave import then


@then('查詢結果應包含用戶名稱為 "{user_name}"')
def step_impl(context, user_name):
    response = context.last_response
    data = response.json()

    assert data["user_name"] == user_name, f"預期 {user_name}，實際 {data['user_name']}"


@then('查詢結果應包含訂單狀態為 "{status}"')
def step_impl(context, status):
    response = context.last_response
    data = response.json()

    # 狀態映射（中文 → 英文 enum）
    status_mapping = {
        "已付款": "PAID",
        "待付款": "PENDING",
        "已取消": "CANCELLED",
        "已完成": "COMPLETED",
    }
    expected_status = status_mapping.get(status, status)

    assert data["status"] == expected_status, f"預期 {expected_status}，實際 {data['status']}"


@then('查詢結果應包含金額 {amount:d}')
def step_impl(context, amount):
    response = context.last_response
    data = response.json()

    assert data["total_amount"] == amount, f"預期 {amount}，實際 {data['total_amount']}"
```

### 驗證空結果

```gherkin
When 用戶 "Bob" 查詢購物車中的所有商品
Then 操作成功
And 查詢結果應為空列表
```

```python
from behave import then


@then('查詢結果應為空列表')
def step_impl(context):
    response = context.last_response
    data = response.json()

    items = data.get("items", [])
    assert len(items) == 0, f"預期空列表，實際有 {len(items)} 個項目"
```

---

## Nested Structure

### 驗證嵌套物件

```gherkin
And 查詢結果的配送資訊應包含地址為 "台北市"，收件人為 "Alice"
```

```python
from behave import then


@then('查詢結果的配送資訊應包含地址為 "{address}"，收件人為 "{recipient}"')
def step_impl(context, address, recipient):
    response = context.last_response
    data = response.json()

    shipping = data.get("shipping", {})
    assert shipping["address"] == address, f"預期 {address}，實際 {shipping.get('address')}"
    assert shipping["recipient"] == recipient, f"預期 {recipient}，實際 {shipping.get('recipient')}"
```

### 驗證列表中的物件

```gherkin
And 查詢結果應包含 2 個商品
And 第一個商品的 ID 為 "PROD-001"，數量為 2
And 第二個商品的 ID 為 "PROD-002"，數量為 1
```

```python
from behave import then


@then('第{index:d}個商品的 ID 為 "{product_id}"，數量為 {quantity:d}')
def step_impl(context, index, product_id, quantity):
    response = context.last_response
    data = response.json()

    items = data.get("items", [])
    # index 從 1 開始（第一個、第二個），轉換為 0-based
    actual_index = index - 1
    assert actual_index < len(items), f"沒有第 {index} 個商品"

    item = items[actual_index]
    assert item["product_id"] == product_id, f"預期 {product_id}，實際 {item['product_id']}"
    assert item["quantity"] == quantity, f"預期數量 {quantity}，實際 {item['quantity']}"
```

---

## Query Failure

```gherkin
Given 用戶 "Alice" 未訂閱課程 1
When 用戶 "Alice" 查詢課程 1 的進度
Then 操作失敗
And 錯誤訊息應為 "無權限查詢此課程"
```

```python
from behave import then


@then('錯誤訊息應為 "{message}"')
def step_impl(context, message):
    response = context.last_response
    data = response.json()

    actual_message = data.get("message") or data.get("detail") or data.get("error")
    assert actual_message == message, f"預期錯誤訊息 '{message}'，實際 '{actual_message}'"
```

---

## Critical Rules

### R1: 使用 When 中的 response
不重新調用 API，使用 context.last_response 中儲存的 response。

```python
# ✅ 正確：使用 context.last_response
response = context.last_response
data = response.json()
assert data["progress"] == 80

# ❌ 錯誤：重新調用 API
response = context.api_client.get(...)  # 不應該重新調用
data = response.json()
```

### R2: 只驗證 Gherkin 提到的欄位
只 assert Gherkin 中明確提到的欄位。

```python
# Gherkin: And 查詢結果應包含進度 80

# ✅ 正確：只驗證 progress
assert data["progress"] == 80

# ❌ 錯誤：驗證額外的欄位
assert data["progress"] == 80
assert data["created_at"] is not None  # Gherkin 沒提到
```

### R3: 欄位名稱使用 snake_case
Response 的欄位名稱使用 snake_case（Python 慣例）。

```python
# ✅ 正確：使用 snake_case
assert data["user_name"] == "Alice"
assert data["total_amount"] == 1000

# ❌ 錯誤：使用 camelCase
assert data["userName"] == "Alice"
assert data["totalAmount"] == 1000
```

### R4: 列表索引注意
Gherkin 中「第一個」「第二個」是 1-based，程式碼中是 0-based。

```python
# Gherkin: And 第一個商品的 ID 為 "PROD-001"

# ✅ 正確：第一筆是 items[0]
assert items[0]["product_id"] == "PROD-001"

# 或使用 1-based 到 0-based 轉換
index = 1  # 第一個
assert items[index - 1]["product_id"] == "PROD-001"
```

### R5: 驗證列表長度
在驗證列表元素之前，先驗證長度。

```python
# ✅ 正確：先驗證長度
items = data.get("items", [])
assert len(items) == 2, f"預期 2 個商品，實際 {len(items)} 個"
assert items[0]["product_id"] == "PROD-001"

# ❌ 錯誤：沒有驗證長度（可能 IndexError）
items = data.get("items", [])
assert items[0]["product_id"] == "PROD-001"  # 如果 items 是空的會報錯
```

### R6: 可以合併多個 And 的驗證
如果多個 And 驗證同一個 response 的不同欄位，每個 step 都從 context.last_response 取得。

```python
# 每個 step 都可以從 context.last_response 取得
@then('查詢結果應包含用戶名稱為 "{user_name}"')
def step_impl(context, user_name):
    data = context.last_response.json()
    assert data["user_name"] == user_name


@then('查詢結果應包含訂單狀態為 "{status}"')
def step_impl(context, status):
    data = context.last_response.json()
    assert data["status"] == status
```

### R7: 使用 response.json() 解析 JSON
必須使用 response.json() 方法解析 JSON 回傳值。

```python
# ✅ 正確：使用 response.json()
data = response.json()
assert data["progress"] == 80

# ❌ 錯誤：使用其他方式
import json
data = json.loads(response.text)
```

### R8: 從 API response 驗證，不查詢資料庫
ReadModel-Then-Handler 驗證的是 API response，不是資料庫狀態。

```python
# ✅ 正確：驗證 API response
response = context.last_response
data = response.json()
assert data["total_amount"] == 1000

# ❌ 錯誤：查詢資料庫
order = repository.find_by_id(...)  # 這是 Aggregate-Then-Handler 的工作
assert order.total_amount == 1000
```

### R9: Assert 訊息要清晰
提供清晰的 assert 失敗訊息，方便除錯。

```python
# ✅ 正確：清晰的訊息
assert data["progress"] == progress, f"預期進度 {progress}，實際 {data['progress']}"

# ❌ 錯誤：沒有訊息
assert data["progress"] == progress
```

---

## 與 Aggregate-Then-Handler 的區別

| 面向 | ReadModel-Then-Handler | Aggregate-Then-Handler |
|------|----------------------|-------------------|
| 驗證對象 | API response 的內容 | 資料庫中的 Aggregate |
| 資料來源 | context.last_response | SQLAlchemy Repository |
| 使用時機 | Query 操作後驗證回傳值 | Command 操作後驗證狀態 |
| 範例 | And 查詢結果應包含進度 80% | And 用戶 "Alice" 在課程 1 的進度應為 80% |

---

## 驗證 DataTable

```gherkin
And 查詢結果應包含:
  | 用戶名稱 | 訂單ID      | 金額 | 狀態   |
  | Alice    | ORDER-123   | 1000 | 已付款 |
```

```python
from behave import then


@then('查詢結果應包含')
def step_impl(context):
    response = context.last_response
    data = response.json()

    # 狀態映射（中文 → 英文 enum）
    status_mapping = {
        "已付款": "PAID",
        "待付款": "PENDING",
        "已取消": "CANCELLED",
        "已完成": "COMPLETED",
    }

    for row in context.table:
        expected_status = status_mapping.get(row["狀態"], row["狀態"])
        assert data["user_name"] == row["用戶名稱"]
        assert data["order_id"] == row["訂單ID"]
        assert data["total_amount"] == int(row["金額"])
        assert data["status"] == expected_status
```

---

**文件建立日期**：2025-01-20
**文件版本**：E2E Behave BDD Version 1.0
**適用框架**：Python + Behave + FastAPI TestClient
