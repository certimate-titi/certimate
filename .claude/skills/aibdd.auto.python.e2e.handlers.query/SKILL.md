---
name: aibdd.auto.python.e2e.handlers.query
description: 當在 .isa.feature 這類 ISA Gherkin 中撰寫 Query API 呼叫步驟時，務必參考此規範。
user-invocable: false
---

# Query-Handler (E2E Behave Version)

## Trigger
When 語句執行**讀取操作**（Query）

**識別規則**:
- 動作不修改系統狀態，只讀取資料
- 描述「取得某些資訊」的動作
- 常見動詞（非窮舉）:「查詢」「取得」「列出」「檢視」「獲取」

**通用判斷**: 如果 When 是讀取操作且需要回傳值供 Then 驗證，就使用此 Handler

## Task
調用 HTTP GET API，將 response 存入 context.last_response

## Key Difference
- **Command**: 修改狀態，調用 HTTP POST/PUT/DELETE，不驗證 response
- **Query**: 讀取資料，調用 HTTP GET，需要驗證 response

## E2E 特色
- 從 context.ids 取得 user ID
- 使用 context.jwt_helper 生成 JWT token
- 使用 context.api_client 打真實的 HTTP GET API
- 將 response 存入 context.last_response 供 ReadModel-Then-Handler 驗證

---

## 實作流程

Query Handler 的任務是**透過 HTTP API 讀取資料**。

### 步驟

1. **從 context.ids 取得用戶 ID**
2. **使用 context.jwt_helper 生成 JWT Token**
3. **構建 URL（含 path/query parameters）**
4. **執行 HTTP GET 請求**（使用 context.api_client）
5. **儲存 response 到 context.last_response**（供 ReadModel-Then-Handler 驗證）

---

## 關鍵概念

### 1. 從 Context 取得 ID

```python
# 從 context.ids 取得用戶 ID
if user_name not in context.ids:
    raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
user_id = context.ids[user_name]
```

### 2. 產生 JWT Token

```python
# 使用 context.jwt_helper 產生 Token
token = context.jwt_helper.generate_token(user_id)
```

### 3. 構建 URL

**Path Parameters**：
- 在 URL 路徑中直接替換參數

```python
# 例如: /api/v1/lessons/{lesson_id}/progress
lesson_id = 1
url = f"/api/v1/lessons/{lesson_id}/progress"
```

**Query Parameters**：
- 使用 `params` 參數傳遞

```python
# 例如: /api/v1/journeys/{journey_id}/lessons?chapter_id={int}
journey_id = 1
chapter_id = 2
url = f"/api/v1/journeys/{journey_id}/lessons"
response = context.api_client.get(url, params={"chapter_id": chapter_id}, headers={...})
```

### 4. 執行 HTTP GET 請求

```python
response = context.api_client.get(
    url,
    headers={"Authorization": f"Bearer {token}"},
    params=params  # 如果有 query parameters
)
```

### 5. 儲存 response 到 context

```python
context.last_response = response
```

**重要**：不在 Query Handler 中驗證 response 內容，由 ReadModel-Then-Handler 處理

---

## Pattern Examples (Python Behave)

### Query 單一記錄

```gherkin
When 用戶 "Alice" 查詢課程 1 的進度
```

```python
from behave import when


@when('用戶 "{user_name}" 查詢課程 {lesson_id:d} 的進度')
def step_impl(context, user_name, lesson_id):
    # 1. 從 context.ids 取得 user_id
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    # 2. 產生 Token
    token = context.jwt_helper.generate_token(user_id)

    # 3. 構建 URL
    url = f"/api/v1/lessons/{lesson_id}/progress"

    # 4. 執行 HTTP GET 請求
    response = context.api_client.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )

    # 5. 儲存結果
    context.last_response = response
```

### Query 列表（無 Query Parameters）

```gherkin
When 用戶 "Alice" 查詢購物車中的所有商品
```

```python
from behave import when


@when('用戶 "{user_name}" 查詢購物車中的所有商品')
def step_impl(context, user_name):
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/cart/items",
        headers={"Authorization": f"Bearer {token}"}
    )

    context.last_response = response
```

### Query 列表（有 Query Parameters）

```gherkin
When 用戶 "Alice" 查詢類別為 "電子產品" 的商品列表
```

```python
from behave import when


@when('用戶 "{user_name}" 查詢類別為 "{category}" 的商品列表')
def step_impl(context, user_name, category):
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
        params={"category": category}
    )

    context.last_response = response
```

### Query 訂單詳情

```gherkin
When 用戶 "Alice" 查詢訂單 "ORDER-123" 的詳情
```

```python
from behave import when


@when('用戶 "{user_name}" 查詢訂單 "{order_id}" 的詳情')
def step_impl(context, user_name, order_id):
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    context.last_response = response
```

---

## Method Naming

**規則**:
- 單一記錄: `get_{entity}` 或 `get_{entity}_{aspect}`
- 列表: `list_{entities}` (複數形式)

| Gherkin 動作範例 | API Path 範例 |
|----------------|--------------|
| 查詢...詳情 | GET /orders/{orderId} |
| 取得...資訊 | GET /products/{productId} |
| 列出...列表 | GET /cart/items |
| 查詢...狀態 | GET /orders/{orderId}/status |

---

## Parameter Extraction

### Path Parameters

從 Gherkin 提取數值，替換到 URL 路徑中：

| Gherkin 片段範例 | Path Parameter | URL 範例 |
|----------------|---------------|---------|
| 訂單 "ORDER-123" | order_id="ORDER-123" | /orders/ORDER-123 |
| 商品 "PROD-001" | product_id="PROD-001" | /products/PROD-001 |
| 課程 1 | lesson_id=1 | /lessons/1 |

### Query Parameters

從 Gherkin 提取選填參數，放在 `params` dict 中：

| Gherkin 片段範例 | Query Parameter | params 範例 |
|----------------|----------------|------------|
| 類別為 "電子產品" | category="電子產品" | {"category": "電子產品"} |
| 狀態為 "已付款" | status="PAID" | {"status": "PAID"} |
| 頁碼 1，每頁 10 筆 | page=1, page_size=10 | {"page": 1, "page_size": 10} |

---

## Critical Rules

### R1: Query 必須儲存 response 到 context.last_response
Query 的 response 會在 ReadModel-Then-Handler 中被使用。

```python
# ✅ 正確：儲存 response
response = context.api_client.get(...)
context.last_response = response

# ❌ 錯誤：沒有儲存
response = context.api_client.get(...)
# 沒有存入 context，ReadModel-Then-Handler 無法驗證
```

### R2: 使用 HTTP GET method
Query 操作必須使用 GET method。

```python
# ✅ 正確：使用 GET
response = context.api_client.get(url, ...)

# ❌ 錯誤：使用 POST
response = context.api_client.post(url, ...)
```

### R3: 必須從 context.ids 取得 user_id
Query 需要認證時，必須從 context.ids 取得 user_id。

```python
# ✅ 正確：從 context.ids 取得
if user_name not in context.ids:
    raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
user_id = context.ids[user_name]
token = context.jwt_helper.generate_token(user_id)

# ❌ 錯誤：直接使用用戶名稱
token = context.jwt_helper.generate_token(user_name)
```

### R4: 必須產生 JWT Token（如果 API 需要認證）
大多數 API 需要認證，必須產生 token。

```python
# ✅ 正確：產生 token 並放在 header
token = context.jwt_helper.generate_token(user_id)
response = context.api_client.get(
    url,
    headers={"Authorization": f"Bearer {token}"}
)

# ❌ 錯誤：沒有 token
response = context.api_client.get(url)
```

### R5: 不在 Query Handler 中驗證 response 內容
Query Handler 只負責執行請求並儲存，不驗證 response 的內容。

```python
# ✅ 正確：不驗證內容
response = context.api_client.get(...)
context.last_response = response

# ❌ 錯誤：在 Query Handler 中驗證
response = context.api_client.get(...)
data = response.json()
assert data["progress"] == 80  # 應該在 ReadModel-Then-Handler 中驗證
```

### R6: Query Parameters 使用 params 參數
如果有 query parameters，使用 `params` 參數傳遞。

```python
# ✅ 正確：使用 params 參數
response = context.api_client.get(
    "/api/v1/journeys/1/lessons",
    params={"chapter_id": 2},
    headers={...}
)

# ❌ 錯誤：手動拼接 URL
response = context.api_client.get(
    "/api/v1/journeys/1/lessons?chapter_id=2",
    headers={...}
)
```

### R7: Path Parameters 使用 f-string
Path parameters 應該使用 f-string 嵌入 URL。

```python
# ✅ 正確：使用 f-string
lesson_id = 1
url = f"/api/v1/lessons/{lesson_id}/progress"

# ❌ 錯誤：使用字串拼接
url = "/api/v1/lessons/" + str(lesson_id) + "/progress"
```

### R8: 使用 context.api_client
必須使用 context 中的 api_client，不自己創建。

```python
# ✅ 正確：使用 context.api_client
response = context.api_client.get(...)

# ❌ 錯誤：自己創建 client
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.get(...)
```

---

## 不需要認證的 API

有些 Query API 不需要認證（如健康檢查、公開資料）。

```gherkin
When 我呼叫健康檢查 API
```

```python
from behave import when


@when('我呼叫健康檢查 API')
def step_impl(context):
    # 不需要 token
    response = context.api_client.get("/api/v1/health")
    context.last_response = response
```

---

## Optional Query Parameters

有些 query parameters 是選填的，根據 Gherkin 是否提到來決定是否傳遞。

```gherkin
# 範例 1: 沒有提到 category
When 用戶 "Alice" 查詢商品列表
```

```python
# 不傳遞 category
response = context.api_client.get("/api/v1/products", headers={...})
```

```gherkin
# 範例 2: 有提到 category
When 用戶 "Alice" 查詢類別為 "電子產品" 的商品列表
```

```python
# 傳遞 category
response = context.api_client.get(
    "/api/v1/products",
    params={"category": "電子產品"},
    headers={...}
)
```

---

## 與 Command-Handler 的區別

| 面向 | Query-Handler | Command-Handler |
|------|--------------|----------------|
| HTTP Method | GET | POST/PUT/PATCH/DELETE |
| 目的 | 讀取資料 | 修改系統狀態 |
| Request Body | 無 | 有 |
| 驗證方式 | ReadModel-Then-Handler | Success-Failure-Handler / Aggregate-Then-Handler |

---

**文件建立日期**：2025-01-20
**文件版本**：E2E Behave BDD Version 1.0
**適用框架**：Python + Behave + FastAPI TestClient
