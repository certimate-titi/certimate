---
name: aibdd.auto.java.e2e.handlers.readmodel-then
description: 當在 .isa.feature 這類 ISA Gherkin 測試中驗證「API 的回應結果應該有什麼內容」時，「只能」使用此指令。
user-invocable: false
---

# ReadModel-Then-Handler (E2E Cucumber Version)

## Trigger
Then 語句驗證**Query 的 API 回傳結果**

**識別規則**:
- 前提: When 是 Query 操作（已接收 response）
- 驗證的是 API 回傳值（而非資料庫中的狀態）
- 常見句型（非窮舉）:「查詢結果應」「回應應」「應返回」「結果包含」

**通用判斷**: 如果 Then 是驗證 Query 操作的回傳值，就使用此 Handler

## Task
從 ScenarioContext 取得 response → 使用 Jackson 解析 JSON → assert 內容

## E2E 特色
- 從 ScenarioContext 取得 HTTP response
- 使用 Jackson ObjectMapper 解析回傳的 JSON
- 驗證 API 回傳值（而非資料庫狀態）

## Critical Rule
不重新調用 API，使用 When 中儲存的 response

---

## Pattern Examples (Java Cucumber)

### 驗證單一記錄

```gherkin
When 用戶 "Alice" 查詢課程 1 的進度
Then 操作成功
And 查詢結果應包含進度 80，狀態為 "進行中"
```

```java
package com.wsa.platform.steps.readmodel_then;

import com.wsa.platform.steps.ScenarioContext;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;

import static org.assertj.core.api.Assertions.assertThat;

public class LessonProgressResultSteps {

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private ObjectMapper objectMapper;

    @Then("查詢結果應包含進度 {int}，狀態為 {string}")
    public void 查詢結果應包含進度狀態為(int progress, String status) throws Exception {
        // 從 ScenarioContext 取得 response
        String responseBody = testContext.getLastResponse().getBody();
        JsonNode data = objectMapper.readTree(responseBody);

        // 狀態映射（中文 → 英文 enum）
        String expectedStatus = mapStatus(status);

        // 驗證欄位
        assertThat(data.get("progress").asInt())
                .as("預期進度 %d，實際 %d", progress, data.get("progress").asInt())
                .isEqualTo(progress);
        assertThat(data.get("status").asText())
                .as("預期狀態 %s，實際 %s", expectedStatus, data.get("status").asText())
                .isEqualTo(expectedStatus);
    }

    private String mapStatus(String status) {
        return switch (status) {
            case "進行中" -> "IN_PROGRESS";
            case "已完成" -> "COMPLETED";
            case "未開始" -> "NOT_STARTED";
            default -> status;
        };
    }
}
```

### 驗證列表

```gherkin
When 用戶 "Alice" 查詢購物車中的所有商品
Then 操作成功
And 查詢結果應包含 2 個商品
And 第一個商品的 ID 應為 "PROD-001"，數量為 2
```

```java
package com.wsa.platform.steps.readmodel_then;

import com.wsa.platform.steps.ScenarioContext;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;

import static org.assertj.core.api.Assertions.assertThat;

public class CartResultSteps {

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private ObjectMapper objectMapper;

    @Then("查詢結果應包含 {int} 個商品")
    public void 查詢結果應包含N個商品(int count) throws Exception {
        String responseBody = testContext.getLastResponse().getBody();
        JsonNode data = objectMapper.readTree(responseBody);

        JsonNode items = data.get("items");
        assertThat(items.size())
                .as("預期 %d 個商品，實際 %d 個", count, items.size())
                .isEqualTo(count);
    }

    @Then("第一個商品的 ID 應為 {string}，數量為 {int}")
    public void 第一個商品的ID應為數量為(String productId, int quantity) throws Exception {
        String responseBody = testContext.getLastResponse().getBody();
        JsonNode data = objectMapper.readTree(responseBody);

        JsonNode items = data.get("items");
        assertThat(items.size()).as("商品列表為空").isGreaterThan(0);

        JsonNode firstItem = items.get(0);
        assertThat(firstItem.get("productId").asText())
                .as("預期 %s，實際 %s", productId, firstItem.get("productId").asText())
                .isEqualTo(productId);
        assertThat(firstItem.get("quantity").asInt())
                .as("預期數量 %d，實際 %d", quantity, firstItem.get("quantity").asInt())
                .isEqualTo(quantity);
    }
}
```

### 驗證嵌套結構

```gherkin
When 用戶 "Alice" 查詢訂單 "ORDER-123" 的詳情
And 查詢結果應包含用戶名稱為 "Alice"
And 查詢結果應包含訂單狀態為 "已付款"
And 查詢結果應包含金額 1000
```

```java
package com.wsa.platform.steps.readmodel_then;

import com.wsa.platform.steps.ScenarioContext;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;

import static org.assertj.core.api.Assertions.assertThat;

public class OrderResultSteps {

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private ObjectMapper objectMapper;

    @Then("查詢結果應包含用戶名稱為 {string}")
    public void 查詢結果應包含用戶名稱為(String userName) throws Exception {
        String responseBody = testContext.getLastResponse().getBody();
        JsonNode data = objectMapper.readTree(responseBody);

        assertThat(data.get("userName").asText())
                .as("預期 %s，實際 %s", userName, data.get("userName").asText())
                .isEqualTo(userName);
    }

    @Then("查詢結果應包含訂單狀態為 {string}")
    public void 查詢結果應包含訂單狀態為(String status) throws Exception {
        String responseBody = testContext.getLastResponse().getBody();
        JsonNode data = objectMapper.readTree(responseBody);

        // 狀態映射（中文 → 英文 enum）
        String expectedStatus = mapOrderStatus(status);

        assertThat(data.get("status").asText())
                .as("預期 %s，實際 %s", expectedStatus, data.get("status").asText())
                .isEqualTo(expectedStatus);
    }

    @Then("查詢結果應包含金額 {int}")
    public void 查詢結果應包含金額(int amount) throws Exception {
        String responseBody = testContext.getLastResponse().getBody();
        JsonNode data = objectMapper.readTree(responseBody);

        assertThat(data.get("totalAmount").asInt())
                .as("預期 %d，實際 %d", amount, data.get("totalAmount").asInt())
                .isEqualTo(amount);
    }

    private String mapOrderStatus(String status) {
        return switch (status) {
            case "已付款" -> "PAID";
            case "待付款" -> "PENDING";
            case "已取消" -> "CANCELLED";
            case "已完成" -> "COMPLETED";
            default -> status;
        };
    }
}
```

### 驗證空結果

```gherkin
When 用戶 "Bob" 查詢購物車中的所有商品
Then 操作成功
And 查詢結果應為空列表
```

```java
package com.wsa.platform.steps.readmodel_then;

import com.wsa.platform.steps.ScenarioContext;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;

import static org.assertj.core.api.Assertions.assertThat;

public class EmptyResultSteps {

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private ObjectMapper objectMapper;

    @Then("查詢結果應為空列表")
    public void 查詢結果應為空列表() throws Exception {
        String responseBody = testContext.getLastResponse().getBody();
        JsonNode data = objectMapper.readTree(responseBody);

        JsonNode items = data.get("items");
        assertThat(items.size())
                .as("預期空列表，實際有 %d 個項目", items.size())
                .isEqualTo(0);
    }
}
```

---

## Nested Structure

### 驗證嵌套物件

```gherkin
And 查詢結果的配送資訊應包含地址為 "台北市"，收件人為 "Alice"
```

```java
@Then("查詢結果的配送資訊應包含地址為 {string}，收件人為 {string}")
public void 查詢結果的配送資訊應包含(String address, String recipient) throws Exception {
    String responseBody = testContext.getLastResponse().getBody();
    JsonNode data = objectMapper.readTree(responseBody);

    JsonNode shipping = data.get("shipping");
    assertThat(shipping.get("address").asText())
            .as("預期 %s，實際 %s", address, shipping.get("address").asText())
            .isEqualTo(address);
    assertThat(shipping.get("recipient").asText())
            .as("預期 %s，實際 %s", recipient, shipping.get("recipient").asText())
            .isEqualTo(recipient);
}
```

### 驗證列表中的物件

```gherkin
And 查詢結果應包含 2 個商品
And 第一個商品的 ID 為 "PROD-001"，數量為 2
And 第二個商品的 ID 為 "PROD-002"，數量為 1
```

```java
@Then("第{int}個商品的 ID 為 {string}，數量為 {int}")
public void 第N個商品的ID為數量為(int index, String productId, int quantity) throws Exception {
    String responseBody = testContext.getLastResponse().getBody();
    JsonNode data = objectMapper.readTree(responseBody);

    JsonNode items = data.get("items");
    // index 從 1 開始（第一個、第二個），轉換為 0-based
    int actualIndex = index - 1;
    assertThat(items.size())
            .as("沒有第 %d 個商品", index)
            .isGreaterThan(actualIndex);

    JsonNode item = items.get(actualIndex);
    assertThat(item.get("productId").asText())
            .as("預期 %s，實際 %s", productId, item.get("productId").asText())
            .isEqualTo(productId);
    assertThat(item.get("quantity").asInt())
            .as("預期數量 %d，實際 %d", quantity, item.get("quantity").asInt())
            .isEqualTo(quantity);
}
```

---

## Query Failure

```gherkin
Given 用戶 "Alice" 未訂閱課程 1
When 用戶 "Alice" 查詢課程 1 的進度
Then 操作失敗
And 錯誤訊息應為 "無權限查詢此課程"
```

```java
package com.wsa.platform.steps.readmodel_then;

import com.wsa.platform.steps.ScenarioContext;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;

import static org.assertj.core.api.Assertions.assertThat;

public class ErrorMessageSteps {

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private ObjectMapper objectMapper;

    @Then("錯誤訊息應為 {string}")
    public void 錯誤訊息應為(String message) throws Exception {
        String responseBody = testContext.getLastResponse().getBody();
        JsonNode data = objectMapper.readTree(responseBody);

        // 嘗試不同的錯誤訊息欄位名稱
        String actualMessage = null;
        if (data.has("message")) {
            actualMessage = data.get("message").asText();
        } else if (data.has("detail")) {
            actualMessage = data.get("detail").asText();
        } else if (data.has("error")) {
            actualMessage = data.get("error").asText();
        }

        assertThat(actualMessage)
                .as("預期錯誤訊息 '%s'，實際 '%s'", message, actualMessage)
                .isEqualTo(message);
    }
}
```

---

## Critical Rules

### R1: 使用 When 中的 response
不重新調用 API，使用 ScenarioContext 中儲存的 response。

```java
// ✅ 正確：使用 ScenarioContext
String responseBody = testContext.getLastResponse().getBody();
JsonNode data = objectMapper.readTree(responseBody);
assertThat(data.get("progress").asInt()).isEqualTo(80);

// ❌ 錯誤：重新調用 API
ResponseEntity<String> response = testRestTemplate.exchange(...);  // 不應該重新調用
```

### R2: 只驗證 Gherkin 提到的欄位
只 assert Gherkin 中明確提到的欄位。

```java
// Gherkin: And 查詢結果應包含進度 80

// ✅ 正確：只驗證 progress
assertThat(data.get("progress").asInt()).isEqualTo(80);

// ❌ 錯誤：驗證額外的欄位
assertThat(data.get("progress").asInt()).isEqualTo(80);
assertThat(data.get("createdAt")).isNotNull();  // Gherkin 沒提到
```

### R3: 欄位名稱使用 camelCase
Response 的欄位名稱使用 camelCase（Java 慣例）。

```java
// ✅ 正確：使用 camelCase
assertThat(data.get("userName").asText()).isEqualTo("Alice");
assertThat(data.get("totalAmount").asInt()).isEqualTo(1000);

// ❌ 錯誤：使用 snake_case
assertThat(data.get("user_name").asText()).isEqualTo("Alice");
assertThat(data.get("total_amount").asInt()).isEqualTo(1000);
```

### R4: 列表索引注意
Gherkin 中「第一個」「第二個」是 1-based，程式碼中是 0-based。

```java
// Gherkin: And 第一個商品的 ID 為 "PROD-001"

// ✅ 正確：第一筆是 items.get(0)
assertThat(items.get(0).get("productId").asText()).isEqualTo("PROD-001");

// 或使用 1-based 到 0-based 轉換
int index = 1;  // 第一個
assertThat(items.get(index - 1).get("productId").asText()).isEqualTo("PROD-001");
```

### R5: 驗證列表長度
在驗證列表元素之前，先驗證長度。

```java
// ✅ 正確：先驗證長度
JsonNode items = data.get("items");
assertThat(items.size()).as("預期 2 個商品").isEqualTo(2);
assertThat(items.get(0).get("productId").asText()).isEqualTo("PROD-001");

// ❌ 錯誤：沒有驗證長度（可能 IndexOutOfBounds 或 NPE）
JsonNode items = data.get("items");
assertThat(items.get(0).get("productId").asText()).isEqualTo("PROD-001");  // items 可能是空的
```

### R6: 可以合併多個 And 的驗證
如果多個 And 驗證同一個 response 的不同欄位，每個 step 都從 ScenarioContext 取得。

```java
// 每個 step 都可以從 ScenarioContext 取得
@Then("查詢結果應包含用戶名稱為 {string}")
public void 查詢結果應包含用戶名稱為(String userName) throws Exception {
    String responseBody = testContext.getLastResponse().getBody();
    JsonNode data = objectMapper.readTree(responseBody);
    assertThat(data.get("userName").asText()).isEqualTo(userName);
}

@Then("查詢結果應包含訂單狀態為 {string}")
public void 查詢結果應包含訂單狀態為(String status) throws Exception {
    String responseBody = testContext.getLastResponse().getBody();
    JsonNode data = objectMapper.readTree(responseBody);
    assertThat(data.get("status").asText()).isEqualTo(mapStatus(status));
}
```

### R7: 使用 Jackson ObjectMapper 解析 JSON
必須使用 Jackson 的 ObjectMapper 解析 JSON 回傳值。

```java
// ✅ 正確：使用 ObjectMapper
@Autowired
private ObjectMapper objectMapper;

JsonNode data = objectMapper.readTree(responseBody);
assertThat(data.get("progress").asInt()).isEqualTo(80);
```

### R8: 從 API response 驗證，不查詢資料庫
ReadModel-Then-Handler 驗證的是 API response，不是資料庫狀態。

```java
// ✅ 正確：驗證 API response
String responseBody = testContext.getLastResponse().getBody();
JsonNode data = objectMapper.readTree(responseBody);
assertThat(data.get("totalAmount").asInt()).isEqualTo(1000);

// ❌ 錯誤：查詢資料庫
Order order = orderRepository.findById(...);  // 這是 Aggregate-Then-Handler 的工作
assertThat(order.getTotalAmount()).isEqualTo(1000);
```

### R9: 使用 AssertJ 提供清晰的錯誤訊息
使用 `.as()` 提供清晰的 assert 失敗訊息，方便除錯。

```java
// ✅ 正確：清晰的訊息
assertThat(data.get("progress").asInt())
        .as("預期進度 %d，實際 %d", progress, data.get("progress").asInt())
        .isEqualTo(progress);

// ❌ 錯誤：沒有訊息
assertThat(data.get("progress").asInt()).isEqualTo(progress);
```

---

## 與 Aggregate-Then-Handler 的區別

| 面向 | ReadModel-Then-Handler | Aggregate-Then-Handler |
|------|----------------------|-------------------|
| 驗證對象 | API response 的內容 | 資料庫中的 Aggregate |
| 資料來源 | ScenarioContext.getLastResponse() | JPA Repository |
| 使用時機 | Query 操作後驗證回傳值 | Command 操作後驗證狀態 |
| 範例 | And 查詢結果應包含進度 80% | And 用戶 "Alice" 在課程 1 的進度應為 80% |

---

## 驗證 DataTable

```gherkin
And 查詢結果應包含:
  | 用戶名稱 | 訂單ID      | 金額 | 狀態   |
  | Alice    | ORDER-123   | 1000 | 已付款 |
```

```java
@Then("查詢結果應包含:")
public void 查詢結果應包含(DataTable dataTable) throws Exception {
    String responseBody = testContext.getLastResponse().getBody();
    JsonNode data = objectMapper.readTree(responseBody);

    List<Map<String, String>> rows = dataTable.asMaps();

    for (Map<String, String> row : rows) {
        String expectedStatus = mapOrderStatus(row.get("狀態"));

        assertThat(data.get("userName").asText()).isEqualTo(row.get("用戶名稱"));
        assertThat(data.get("orderId").asText()).isEqualTo(row.get("訂單ID"));
        assertThat(data.get("totalAmount").asInt()).isEqualTo(Integer.parseInt(row.get("金額")));
        assertThat(data.get("status").asText()).isEqualTo(expectedStatus);
    }
}

private String mapOrderStatus(String status) {
    return switch (status) {
        case "已付款" -> "PAID";
        case "待付款" -> "PENDING";
        case "已取消" -> "CANCELLED";
        case "已完成" -> "COMPLETED";
        default -> status;
    };
}
```

---

**文件建立日期**：2025-01-20
**文件版本**：E2E Cucumber BDD Version 1.0
**適用框架**：Java 17 + Spring Boot 3.2 + Cucumber 7.15 + Jackson
