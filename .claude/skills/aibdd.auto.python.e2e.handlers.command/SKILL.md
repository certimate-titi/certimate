---
name: aibdd.auto.python.e2e.handlers.command
description: 當在 .isa.feature 這類 ISA Gherkin 中撰寫 API 呼叫步驟（When ... call table）時，務必參考此規範來撰寫正確的語法。
user-invocable: false
---

# Command-Handler (E2E Behave Version)

## Trigger
Given/When 語句執行**寫入操作**（Command）

**識別規則**:
- 動作會修改系統狀態
- 描述「執行某個動作」或「已完成某個動作」
- Given 常見過去式（非窮舉）:「已訂閱」「已完成」「已建立」「已添加」「已註冊」
- When 常見現在式（非窮舉）:「更新」「提交」「建立」「刪除」「添加」「移除」

**通用判斷**: 如果語句是修改系統狀態的操作且不需要回傳值，就使用此 Handler

## Task
調用 HTTP POST/PUT/PATCH/DELETE API

## Key Difference
- **Command**: 修改狀態，調用 HTTP POST/PUT/PATCH/DELETE，不驗證 response
- **Query**: 讀取資料，調用 HTTP GET，需要驗證 response

## E2E 特色
- 從 context.ids 取得 user ID
- 使用 context.jwt_helper 生成 JWT token
- 使用 context.api_client 打真實的 HTTP API
- 將 response 存入 context.last_response 供 Then 驗證

---

## 實作流程

Command Handler 的任務是**透過 HTTP API 執行修改系統狀態的操作**。

### 步驟

1. **從 context.ids 取得用戶 ID**
2. **使用 context.jwt_helper 生成 JWT Token**
3. **構建 Request Body（使用 snake_case）**
4. **執行 HTTP POST/PUT/DELETE 請求**（使用 context.api_client）
5. **儲存 response 到 context.last_response**（不驗證，交給 Then）

---

## 關鍵概念

### 1. 從 Context 取得 ID

```python
# 從 context.ids 取得用戶 ID
if user_name not in context.ids:
    raise KeyError(f"找不到用戶 '{user_name}' 的 ID，請先在 Given 步驟中建立用戶")
user_id = context.ids[user_name]
```

### 2. 產生 JWT Token

```python
# 使用 context.jwt_helper 產生 Token
token = context.jwt_helper.generate_token(user_id)
```

### 3. 構建 Request Body

**重要**：使用 **snake_case** 命名（Python 慣例）

```python
request_body = {
    "lesson_id": 1,        # snake_case
    "progress": 80
}
```

### 4. 執行 HTTP POST 請求

```python
response = context.api_client.post(
    "/api/v1/lesson-progress/update-video-progress",
    headers={"Authorization": f"Bearer {token}"},
    json=request_body
)
```

### 5. 儲存 response 到 context

```python
context.last_response = response
```

**重要**：不驗證 Response（不使用 `assert`），由 Then 步驟處理

---

## Pattern Examples (Python Behave)

### When + Command (現在執行的動作)

```gherkin
When 用戶 "Alice" 更新課程 1 的影片進度為 80%
```

```python
from behave import when


@when('用戶 "{user_name}" 更新課程 {lesson_id:d} 的影片進度為 {progress:d}%')
def step_impl(context, user_name, lesson_id, progress):
    # 1. 從 context.ids 取得 user_id
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    # 2. 產生 Token
    token = context.jwt_helper.generate_token(user_id)

    # 3. 構建 Request Body（snake_case）
    request_body = {
        "lesson_id": lesson_id,
        "progress": progress
    }

    # 4. 執行 HTTP 請求
    response = context.api_client.post(
        "/api/v1/lesson-progress/update-video-progress",
        headers={"Authorization": f"Bearer {token}"},
        json=request_body
    )

    # 5. 儲存結果（不驗證）
    context.last_response = response
```

### 多參數 Command

```gherkin
When 用戶 "Alice" 建立訂單，配送地址為 "台北市信義區"，付款方式為 "信用卡"
```

```python
from behave import when


@when('用戶 "{user_name}" 建立訂單，配送地址為 "{address}"，付款方式為 "{payment_method}"')
def step_impl(context, user_name, address, payment_method):
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    token = context.jwt_helper.generate_token(user_id)

    request_body = {
        "shipping_address": address,
        "payment_method": payment_method
    }

    response = context.api_client.post(
        "/api/v1/orders",
        headers={"Authorization": f"Bearer {token}"},
        json=request_body
    )

    context.last_response = response
```

### 有 Path Variable 的 Command

```gherkin
When 用戶 "Alice" 取消訂單 "ORDER-123"
```

```python
from behave import when


@when('用戶 "{user_name}" 取消訂單 "{order_id}"')
def step_impl(context, user_name, order_id):
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.delete(
        f"/api/v1/orders/{order_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    context.last_response = response
```

### Given + Command (已完成的動作)

```gherkin
Given 用戶 "Alice" 已訂閱旅程 1
```

```python
from behave import given


@given('用戶 "{user_name}" 已訂閱旅程 {journey_id:d}')
def step_impl(context, user_name, journey_id):
    # 取得用戶 ID
    if user_name not in context.ids:
        raise KeyError(f"找不到用戶 '{user_name}' 的 ID")
    user_id = context.ids[user_name]

    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        "/api/v1/journey-subscriptions",
        headers={"Authorization": f"Bearer {token}"},
        json={"journey_id": journey_id}
    )

    # Given + Command 也儲存 response（以便需要時使用）
    context.last_response = response

    # 如果需要，可以從 response 中提取 ID
    if response.status_code in [200, 201]:
        data = response.json()
        # 儲存訂閱 ID（如果 API 有回傳）
        if "subscription_id" in data:
            context.ids[f"{user_name}_subscription_{journey_id}"] = data["subscription_id"]
```

---

## Given vs When Command

### 差異說明

**Given + Command (已完成的動作)**:
- 用於建立測試前置條件
- 描述過去已經發生的動作
- 常用過去式：「已訂閱」「已完成」「已建立」「已註冊」

**When + Command (現在執行的動作)**:
- 用於執行被測試的動作
- 描述現在要執行的動作
- 常用現在式：「更新」「提交」「建立」

### 範例對比

```gherkin
# Given: 建立前置條件
Given 用戶 "Alice" 已訂閱旅程 1

# When: 執行被測試動作
When 用戶 "Alice" 更新課程 1 的影片進度為 80%
```

**關鍵**: Given 和 When 的 Command 在程式碼層面類似，都是調用 HTTP API

---

## Critical Rules

### R1: Command 不驗證 Response
在 Command Handler 中只執行請求，不驗證 response（除非是從 response 提取 ID）。

```python
# ✅ 正確：不驗證，只儲存
response = context.api_client.post(...)
context.last_response = response

# ❌ 錯誤：在 Command 中驗證
response = context.api_client.post(...)
assert response.status_code == 200  # 應該在 Then 中驗證
```

### R2: 參數名稱使用 snake_case
Request body 的欄位名稱使用 snake_case（Python 慣例）。

```python
# ✅ 正確：使用 snake_case
json={"lesson_id": 1, "progress": 80}

# ❌ 錯誤：使用 camelCase
json={"lessonId": 1, "progress": 80}
```

### R3: 必須從 context.ids 取得 user_id
Command 需要認證時，必須從 context.ids 取得 user_id。

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
response = context.api_client.post(
    "/api/v1/...",
    headers={"Authorization": f"Bearer {token}"},
    json={...}
)

# ❌ 錯誤：沒有 token
response = context.api_client.post("/api/v1/...", json={...})
```

### R5: 必須儲存 response 到 context.last_response
每個 Command 執行後都要儲存 response 到 context。

```python
# ✅ 正確：儲存 response
context.last_response = response

# ❌ 錯誤：沒有儲存
response = context.api_client.post(...)
# 沒有存入 context，Then 無法驗證
```

### R6: 使用 context.api_client
必須使用 context 中的 api_client，不自己創建。

```python
# ✅ 正確：使用 context.api_client
response = context.api_client.post(...)

# ❌ 錯誤：自己創建 client
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.post(...)
```

### R7: 檢查 user_id 是否存在
在從 context.ids 取得 user_id 後，應檢查是否存在。

```python
# ✅ 正確：檢查是否存在
if user_name not in context.ids:
    raise KeyError(f"找不到用戶 '{user_name}' 的 ID，請先建立用戶")
user_id = context.ids[user_name]
```

### R8: HTTP Method 選擇
根據操作類型選擇正確的 HTTP method。

```python
# POST：創建資源
response = context.api_client.post("/api/v1/orders", ...)

# PUT：完整更新資源
response = context.api_client.put(f"/api/v1/orders/{order_id}", ...)

# PATCH：部分更新資源
response = context.api_client.patch(f"/api/v1/orders/{order_id}", ...)

# DELETE：刪除資源
response = context.api_client.delete(f"/api/v1/orders/{order_id}", ...)
```

### R9: API Endpoint Path 必須嚴格遵循 api.yml（Single Source of Truth）

`context.api_client` 的 URL path 必須嚴格遵循 `specs/api.yml` 定義的 endpoint paths。**`api.yml` 是 API endpoint path 的唯一來源（Single Source of Truth）**，不允許自行發明或變更 path。

#### 如何從 Gherkin 語句找到對應的 API endpoint

`api.yml` 中每個 endpoint 都有一個 `summary` 欄位，該 `summary` 與 Gherkin Feature File 中的語句嚴格對應。利用此對應關係，可以從 Gherkin 語句精確定位到 API endpoint 的 path 和 HTTP method。

**對應流程**：
1. 閱讀 Gherkin 語句（例如：`When 用戶 "Alice" 更新課程 1 的影片進度為 80%`）
2. 在 `specs/api.yml` 中搜尋 `summary` 欄位，找到語句模板相符的 endpoint
3. 使用該 endpoint 定義的 **HTTP method** 和 **path**

**範例**：

```yaml
# specs/api.yml
paths:
  /courses/{courseId}/progress:
    post:
      summary: 更新課程 {courseId} 的影片進度為 {progress}%
```

對應的 Gherkin 語句：
```gherkin
When 用戶 "Alice" 更新課程 1 的影片進度為 80%
```

因此 `context.api_client` 應該調用（加上應用程式配置的 prefix）：
```python
# ✅ 正確：path 來自 api.yml（/courses/{courseId}/progress）
response = context.api_client.post(
    f"/api/v1/courses/{course_id}/progress",
    headers={"Authorization": f"Bearer {token}"},
    json=request_body
)

# ❌ 錯誤：自行發明的 path
response = context.api_client.post(
    "/api/v1/lesson-progress/update-video-progress",
    headers={"Authorization": f"Bearer {token}"},
    json=request_body
)
```

**更多對應範例**：

| Gherkin 語句 | api.yml summary | api.yml path | HTTP Method |
|---|---|---|---|
| 用戶 "Alice" 建立訂單… | 建立訂單，商品 ID 為 {productId}… | `/orders` | POST |
| 用戶 "Alice" 對訂單 1 進行付款… | 對訂單 {orderId} 進行付款… | `/orders/{orderId}/payments` | POST |
| 用戶 "Alice" 取消訂單 1 | 取消訂單 {orderId} | `/orders/{orderId}/cancellations` | POST |
| 用戶 "Alice" 提交課程 3 的挑戰題作業 | 提交課程 {courseId} 的挑戰題作業 | `/courses/{courseId}/submissions` | POST |
| 用戶 "Alice" 交付課程 1 | 交付課程 {courseId} | `/courses/{courseId}/deliveries` | POST |

**規則**：
- ✅ 從 `specs/api.yml` 查找對應的 endpoint path 和 HTTP method
- ✅ 使用 `summary` 欄位與 Gherkin 語句的對應關係來定位 endpoint
- ❌ 不要自行發明 path
- ❌ 不要更改 api.yml 定義的 path 結構或資源命名

---

## 不需要認證的 API

有些 API 不需要認證（如註冊、登入）。

```gherkin
Given 用戶 "Alice" 已註冊，email 為 "alice@test.com"
```

```python
from behave import given


@given('用戶 "{user_name}" 已註冊，email 為 "{email}"')
def step_impl(context, user_name, email):
    # 不需要 token
    response = context.api_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123",
            "name": user_name
        }
    )
    context.last_response = response

    # 從 response 提取 user_id 並存入 context.ids
    if response.status_code in [200, 201]:
        data = response.json()
        context.ids[user_name] = data.get("user", {}).get("id", user_name)
```

---

## 與 Query-Handler 的區別

| 面向 | Command-Handler | Query-Handler |
|------|----------------|---------------|
| HTTP Method | POST/PUT/PATCH/DELETE | GET |
| 目的 | 修改系統狀態 | 讀取資料 |
| Response 處理 | 只儲存，不驗證 | 儲存後由 ReadModel-Then 驗證 |
| Request Body | 有 | 無（使用 Query Parameters） |

---

**文件建立日期**：2025-01-20
**文件版本**：E2E Behave BDD Version 1.0
**適用框架**：Python + Behave + FastAPI TestClient
