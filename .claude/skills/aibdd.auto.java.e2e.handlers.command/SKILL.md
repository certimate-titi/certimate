---
name: aibdd.auto.java.e2e.handlers.command
description: 當在 .isa.feature 這類 ISA Gherkin 中撰寫 API 呼叫步驟（When ... call table）時，務必參考此規範來撰寫正確的語法。
user-invocable: false
---

# Command-Handler (E2E Cucumber Version)

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
- 從 ScenarioContext 取得 user ID
- 使用 JwtHelper 生成 JWT token
- 使用 TestRestTemplate 打真實的 HTTP API
- 將 response 存入 ScenarioContext 供 Then 驗證

---

## 實作流程

Command Handler 的任務是**透過 HTTP API 執行修改系統狀態的操作**。

### 步驟

1. **從 ScenarioContext 取得用戶 ID**
2. **使用 JwtHelper 生成 JWT Token**
3. **構建 Request Body（使用 camelCase - Java 慣例）**
4. **執行 HTTP POST/PUT/DELETE 請求**（使用 TestRestTemplate）
5. **儲存 response 到 ScenarioContext**（不驗證，交給 Then）

---

## 關鍵概念

### 1. 從 ScenarioContext 取得 ID

```java
// 從 ScenarioContext 取得用戶 ID
String userId = testContext.getId(userName);
if (userId == null) {
    throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID，請先在 Given 步驟中建立用戶");
}
```

### 2. 產生 JWT Token

```java
// 使用 JwtHelper 產生 Token
String token = jwtHelper.generateToken(userId);
```

### 3. 構建 Request Body

**重要**：使用 **camelCase** 命名（Java 慣例）

```java
Map<String, Object> requestBody = Map.of(
    "lessonId", 1,        // camelCase
    "progress", 80
);
```

### 4. 執行 HTTP POST 請求

```java
HttpHeaders headers = new HttpHeaders();
headers.setContentType(MediaType.APPLICATION_JSON);
headers.setBearerAuth(token);

HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

ResponseEntity<String> response = testRestTemplate.exchange(
    "/api/v1/lesson-progress/update-video-progress",
    HttpMethod.POST,
    request,
    String.class
);
```

### 5. 儲存 response 到 ScenarioContext

```java
testContext.setLastResponse(response);
```

**重要**：不驗證 Response（不使用 `assertThat`），由 Then 步驟處理

---

## Pattern Examples (Java Cucumber)

### When + Command (現在執行的動作)

```gherkin
When 用戶 "Alice" 更新課程 1 的影片進度為 80%
```

```java
package com.wsa.platform.steps.commands;

import com.wsa.platform.steps.ScenarioContext;
import com.wsa.platform.util.JwtHelper;
import io.cucumber.java.en.When;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;

import java.util.Map;

public class VideoProgressSteps {

    @Autowired
    private TestRestTemplate testRestTemplate;

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private JwtHelper jwtHelper;

    @When("用戶 {string} 更新課程 {int} 的影片進度為 {int}%")
    public void 用戶更新課程的影片進度為(String userName, int lessonId, int progress) {
        // 1. 從 ScenarioContext 取得 user_id
        String userId = testContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
        }

        // 2. 產生 Token
        String token = jwtHelper.generateToken(userId);

        // 3. 構建 Request Body（camelCase）
        Map<String, Object> requestBody = Map.of(
            "lessonId", lessonId,
            "progress", progress
        );

        // 4. 執行 HTTP 請求
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setBearerAuth(token);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

        ResponseEntity<String> response = testRestTemplate.exchange(
            "/api/v1/lesson-progress/update-video-progress",
            HttpMethod.POST,
            request,
            String.class
        );

        // 5. 儲存結果（不驗證）
        testContext.setLastResponse(response);
    }
}
```

### 多參數 Command

```gherkin
When 用戶 "Alice" 建立訂單，配送地址為 "台北市信義區"，付款方式為 "信用卡"
```

```java
package com.wsa.platform.steps.commands;

import com.wsa.platform.steps.ScenarioContext;
import com.wsa.platform.util.JwtHelper;
import io.cucumber.java.en.When;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;

import java.util.Map;

public class CreateOrderSteps {

    @Autowired
    private TestRestTemplate testRestTemplate;

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private JwtHelper jwtHelper;

    @When("用戶 {string} 建立訂單，配送地址為 {string}，付款方式為 {string}")
    public void 用戶建立訂單(String userName, String address, String paymentMethod) {
        String userId = testContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
        }

        String token = jwtHelper.generateToken(userId);

        Map<String, Object> requestBody = Map.of(
            "shippingAddress", address,
            "paymentMethod", paymentMethod
        );

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setBearerAuth(token);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

        ResponseEntity<String> response = testRestTemplate.exchange(
            "/api/v1/orders",
            HttpMethod.POST,
            request,
            String.class
        );

        testContext.setLastResponse(response);
    }
}
```

### 有 Path Variable 的 Command

```gherkin
When 用戶 "Alice" 取消訂單 "ORDER-123"
```

```java
package com.wsa.platform.steps.commands;

import com.wsa.platform.steps.ScenarioContext;
import com.wsa.platform.util.JwtHelper;
import io.cucumber.java.en.When;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;

public class CancelOrderSteps {

    @Autowired
    private TestRestTemplate testRestTemplate;

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private JwtHelper jwtHelper;

    @When("用戶 {string} 取消訂單 {string}")
    public void 用戶取消訂單(String userName, String orderId) {
        String userId = testContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
        }

        String token = jwtHelper.generateToken(userId);

        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);

        HttpEntity<Void> request = new HttpEntity<>(headers);

        ResponseEntity<String> response = testRestTemplate.exchange(
            "/api/v1/orders/" + orderId,
            HttpMethod.DELETE,
            request,
            String.class
        );

        testContext.setLastResponse(response);
    }
}
```

### Given + Command (已完成的動作)

```gherkin
Given 用戶 "Alice" 已訂閱旅程 1
```

```java
package com.wsa.platform.steps.commands;

import com.wsa.platform.steps.ScenarioContext;
import com.wsa.platform.util.JwtHelper;
import io.cucumber.java.en.Given;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;

import java.util.Map;

public class SubscribeJourneySteps {

    @Autowired
    private TestRestTemplate testRestTemplate;

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private JwtHelper jwtHelper;

    @Given("用戶 {string} 已訂閱旅程 {int}")
    public void 用戶已訂閱旅程(String userName, int journeyId) {
        // 取得用戶 ID
        String userId = testContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
        }

        String token = jwtHelper.generateToken(userId);

        Map<String, Object> requestBody = Map.of("journeyId", journeyId);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setBearerAuth(token);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

        ResponseEntity<String> response = testRestTemplate.exchange(
            "/api/v1/journey-subscriptions",
            HttpMethod.POST,
            request,
            String.class
        );

        // Given + Command 也儲存 response（以便需要時使用）
        testContext.setLastResponse(response);

        // 如果需要，可以從 response 中提取 ID（使用 Jackson）
        // ObjectMapper objectMapper = new ObjectMapper();
        // JsonNode root = objectMapper.readTree(response.getBody());
        // String subscriptionId = root.get("subscriptionId").asText();
        // testContext.putId(userName + "_subscription_" + journeyId, subscriptionId);
    }
}
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

```java
// ✅ 正確：不驗證，只儲存
ResponseEntity<String> response = testRestTemplate.exchange(...);
testContext.setLastResponse(response);

// ❌ 錯誤：在 Command 中驗證
ResponseEntity<String> response = testRestTemplate.exchange(...);
assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);  // 應該在 Then 中驗證
```

### R2: 參數名稱使用 camelCase
Request body 的欄位名稱使用 camelCase（Java 慣例）。

```java
// ✅ 正確：使用 camelCase
Map.of("lessonId", 1, "progress", 80)

// ❌ 錯誤：使用 snake_case
Map.of("lesson_id", 1, "progress", 80)
```

### R3: 必須從 ScenarioContext 取得 userId
Command 需要認證時，必須從 ScenarioContext 取得 userId。

```java
// ✅ 正確：從 ScenarioContext 取得
String userId = testContext.getId(userName);
if (userId == null) {
    throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
}
String token = jwtHelper.generateToken(userId);

// ❌ 錯誤：直接使用用戶名稱
String token = jwtHelper.generateToken(userName);
```

### R4: 必須產生 JWT Token（如果 API 需要認證）
大多數 API 需要認證，必須產生 token。

```java
// ✅ 正確：產生 token 並放在 header
String token = jwtHelper.generateToken(userId);
headers.setBearerAuth(token);

// ❌ 錯誤：沒有 token
testRestTemplate.exchange("/api/v1/...", HttpMethod.POST, request, String.class);
```

### R5: 必須儲存 response 到 ScenarioContext
每個 Command 執行後都要儲存 response 到 ScenarioContext。

```java
// ✅ 正確：儲存 response
testContext.setLastResponse(response);

// ❌ 錯誤：沒有儲存
ResponseEntity<String> response = testRestTemplate.exchange(...);
// 沒有存入 ScenarioContext，Then 無法驗證
```

### R6: 使用 TestRestTemplate
必須使用 Spring Boot Test 的 TestRestTemplate。

```java
// ✅ 正確：使用 @Autowired TestRestTemplate
@Autowired
private TestRestTemplate testRestTemplate;

ResponseEntity<String> response = testRestTemplate.exchange(...);

// ❌ 錯誤：自己創建 RestTemplate
RestTemplate restTemplate = new RestTemplate();
```

### R7: 檢查 userId 是否存在
在從 ScenarioContext 取得 userId 後，應檢查是否存在。

```java
// ✅ 正確：檢查是否存在
String userId = testContext.getId(userName);
if (userId == null) {
    throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID，請先建立用戶");
}
```

### R8: HTTP Method 選擇
根據操作類型選擇正確的 HTTP method。

```java
// POST：創建資源
testRestTemplate.exchange("/api/v1/orders", HttpMethod.POST, request, String.class);

// PUT：完整更新資源
testRestTemplate.exchange("/api/v1/orders/" + orderId, HttpMethod.PUT, request, String.class);

// PATCH：部分更新資源
testRestTemplate.exchange("/api/v1/orders/" + orderId, HttpMethod.PATCH, request, String.class);

// DELETE：刪除資源
testRestTemplate.exchange("/api/v1/orders/" + orderId, HttpMethod.DELETE, request, String.class);
```

### R9: API Endpoint Path 必須嚴格遵循 api.yml（Single Source of Truth）

TestRestTemplate 的 URL path 必須嚴格遵循 `specs/api.yml` 定義的 endpoint paths。**`api.yml` 是 API endpoint path 的唯一來源（Single Source of Truth）**，不允許自行發明或變更 path。

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

因此 TestRestTemplate 應該調用（加上應用程式配置的 prefix）：
```java
// ✅ 正確：path 來自 api.yml（/courses/{courseId}/progress）
testRestTemplate.exchange(
    "/api/v1/courses/" + courseId + "/progress",
    HttpMethod.POST,
    request,
    String.class
);

// ❌ 錯誤：自行發明的 path
testRestTemplate.exchange(
    "/api/v1/lesson-progress/update-video-progress",
    HttpMethod.POST,
    request,
    String.class
);
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

```java
package com.wsa.platform.steps.commands;

import com.wsa.platform.steps.ScenarioContext;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.cucumber.java.en.Given;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;

import java.util.Map;

public class RegisterSteps {

    @Autowired
    private TestRestTemplate testRestTemplate;

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private ObjectMapper objectMapper;

    @Given("用戶 {string} 已註冊，email 為 {string}")
    public void 用戶已註冊email為(String userName, String email) throws Exception {
        // 不需要 token
        Map<String, Object> requestBody = Map.of(
            "email", email,
            "password", "Password123",
            "name", userName
        );

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

        ResponseEntity<String> response = testRestTemplate.exchange(
            "/api/v1/auth/register",
            HttpMethod.POST,
            request,
            String.class
        );

        testContext.setLastResponse(response);

        // 從 response 提取 user_id 並存入 ScenarioContext
        if (response.getStatusCode().is2xxSuccessful()) {
            JsonNode root = objectMapper.readTree(response.getBody());
            String userId = root.path("user").path("id").asText(userName);
            testContext.putId(userName, userId);
        }
    }
}
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
**文件版本**：E2E Cucumber BDD Version 1.0
**適用框架**：Java 17 + Spring Boot 3.2 + Cucumber 7.15 + TestRestTemplate
