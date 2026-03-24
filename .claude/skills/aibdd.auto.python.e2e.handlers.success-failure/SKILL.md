---
name: aibdd.auto.python.e2e.handlers.success-failure
description: 當在 .isa.feature 這類 ISA Gherkin 測試中驗證操作成功或失敗時，參考此規範。
user-invocable: false
---

# Success-Failure-Handler (E2E Behave Version)

## Trigger
Then 語句描述**操作的成功或失敗結果**（驗證 HTTP status code）

**識別規則**:
- 明確描述操作結果（成功/失敗）
- 常見句型:「操作成功」「操作失敗」「執行成功」「執行失敗」

**通用判斷**: 如果 Then 只關注操作是否成功（HTTP 2XX）或失敗（HTTP 4XX），就使用此 Handler

## Task
從 context.last_response 取得 response，驗證 HTTP status code

## E2E 特色
- 從 context.last_response 取得 HTTP response
- 驗證 response.status_code
- 成功：HTTP 2XX（200, 201, 204）
- 失敗：HTTP 4XX（400, 401, 403, 404, 409 等）

---

## Pattern 1: 操作成功 (Python Behave)

```gherkin
When 用戶 "Alice" 更新課程 1 的影片進度為 80%
Then 操作成功
```

```python
from behave import then


@then("操作成功")
def step_impl(context):
    response = context.last_response

    # 驗證 HTTP status code 為 2XX
    assert response.status_code in [200, 201, 204], \
        f"預期成功（2XX），實際 {response.status_code}: {response.text}"
```

---

## Pattern 2: 操作失敗 (Python Behave)

```gherkin
When 用戶 "Alice" 更新課程 1 的影片進度為 60%
Then 操作失敗
```

```python
from behave import then


@then("操作失敗")
def step_impl(context):
    response = context.last_response

    # 驗證 HTTP status code 為 4XX
    assert response.status_code >= 400 and response.status_code < 500, \
        f"預期失敗（4XX），實際 {response.status_code}: {response.text}"
```

---

## 更精確的 Status 驗證

## Error Message Verification

除了驗證 status code，還可以驗證錯誤訊息：

```gherkin
When 用戶 "Alice" 更新課程 1 的影片進度為 60%
Then 操作失敗
And 錯誤訊息應為 "進度不可倒退"
```

```python
from behave import then


@then('錯誤訊息應為 "{message}"')
def step_impl(context, message):
    response = context.last_response
    data = response.json()

    # 嘗試不同的錯誤訊息欄位名稱
    actual_message = data.get("message") or data.get("detail") or data.get("error")
    assert actual_message == message, \
        f"預期錯誤訊息 '{message}'，實際 '{actual_message}'"
```

---

## Complete Examples

### Example 1: 成功場景

```gherkin
Feature: 課程平台 - 增加影片進度

Rule: 影片進度必須單調遞增

  Example: 成功增加影片進度
    Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"
    When 用戶 "Alice" 更新課程 1 的影片進度為 80%
    Then 操作成功
    And 用戶 "Alice" 在課程 1 的進度應為 80%
```

```python
# tests/features/steps/common_then/success.py

from behave import then


@then("操作成功")
def step_impl(context):
    response = context.last_response
    assert response.status_code in [200, 201, 204], \
        f"預期成功（2XX），實際 {response.status_code}: {response.text}"
```

### Example 2: 失敗場景

```gherkin
Feature: 課程平台 - 增加影片進度

Rule: 影片進度必須單調遞增

  Example: 進度不可倒退
    Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"
    When 用戶 "Alice" 更新課程 1 的影片進度為 60%
    Then 操作失敗
    And 用戶 "Alice" 在課程 1 的進度應為 70%
```

```python
# tests/features/steps/common_then/failure.py

from behave import then


@then("操作失敗")
def step_impl(context):
    response = context.last_response
    assert response.status_code >= 400 and response.status_code < 500, \
        f"預期失敗（4XX），實際 {response.status_code}: {response.text}"
```

---

## Critical Rules

### R1: 從 context.last_response 取得 response
不重新調用 API，使用 context 中儲存的 response。

```python
# ✅ 正確：從 context.last_response 取得
response = context.last_response
assert response.status_code in [200, 201, 204]

# ❌ 錯誤：重新調用 API
response = context.api_client.post(...)
assert response.status_code == 200
```

### R2: 成功使用 2XX 範圍驗證
操作成功時，接受 200, 201, 204 等成功狀態碼。

```python
# ✅ 正確：接受多個成功狀態碼
assert response.status_code in [200, 201, 204]

# ⚠️ 也可以（如果確定只會回傳特定 code）
assert response.status_code == 200
```

### R3: 失敗使用 4XX 範圍驗證
操作失敗時，驗證狀態碼在 400-499 範圍內。

```python
# ✅ 正確：驗證 4XX 範圍
assert response.status_code >= 400 and response.status_code < 500

# ⚠️ 也可以（如果確定只會回傳特定 code）
assert response.status_code == 400
```

### R4: 提供清晰的錯誤訊息
assert 失敗時提供清晰的訊息，包含實際的 status code 和 response body。

```python
# ✅ 正確：清晰的錯誤訊息
assert response.status_code in [200, 201, 204], \
    f"預期成功（2XX），實際 {response.status_code}: {response.text}"

# ❌ 錯誤：沒有訊息
assert response.status_code in [200, 201, 204]
```

### R5: 不在 Success-Failure-Handler 中驗證 response 內容
只驗證 status code，不驗證 response body（那是 ReadModel-Then-Handler 的工作）。

```python
# ✅ 正確：只驗證 status code
response = context.last_response
assert response.status_code in [200, 201, 204]

# ❌ 錯誤：驗證 response 內容
response = context.last_response
assert response.status_code == 200
data = response.json()
assert data["progress"] == 80  # 這是 ReadModel-Then-Handler 的工作
```

### R6: 失敗時資料狀態不應改變
失敗場景中，通常需要在另一個 Then 步驟驗證資料狀態未被修改。

```gherkin
Then 操作失敗
And 用戶 "Alice" 在課程 1 的進度應為 70%  # Aggregate-Then-Handler 驗證狀態未改變
```

### R7: 錯誤訊息驗證是選填的
驗證錯誤訊息不是必須的，取決於 Gherkin 是否明確要求。

```gherkin
# 只驗證失敗
Then 操作失敗
```

```python
@then("操作失敗")
def step_impl(context):
    response = context.last_response
    assert response.status_code >= 400 and response.status_code < 500
```

```gherkin
# 驗證失敗 + 錯誤訊息
Then 操作失敗
And 錯誤訊息應為 "進度不可倒退"
```

---

## 不需要 Success-Failure-Handler 的情況

有些測試不需要明確的「操作成功」或「操作失敗」，而是直接驗證資料或回傳值：

```gherkin
# 不需要「Then 操作成功」
Example: 查詢課程進度
  Given 用戶 "Alice" 在課程 1 的進度為 80%，狀態為 "進行中"
  When 用戶 "Alice" 查詢課程 1 的進度
  And 查詢結果應包含進度 80，狀態為 "進行中"
```

在這種情況下，ReadModel-Then-Handler 會隱含地驗證成功（因為如果失敗，response.json() 會報錯）。

---

## File Organization

建議將 Success 和 Failure 的 step definitions 放在 `common_then/` 目錄：

```
tests/features/steps/
└── common_then/
    ├── success.py      # @then("操作成功")
    └── failure.py      # @then("操作失敗")
```

---

**文件建立日期**：2025-01-20
**文件版本**：E2E Behave BDD Version 1.0
**適用框架**：Python + Behave + FastAPI TestClient
