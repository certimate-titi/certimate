---
name: aibdd.auto.java.e2e.handlers.query
description: 當在 .isa.feature 這類 ISA Gherkin 中撰寫 Query API 呼叫步驟時，務必參考此規範。
user-invocable: false
---

# Query-Handler (E2E Cucumber Version)

## Trigger
When 語句執行**讀取操作**（Query）

**識別規則**:
- 動作不修改系統狀態，只讀取資料
- 描述「取得某些資訊」的動作
- 常見動詞（非窮舉）:「查詢」「取得」「列出」「檢視」「獲取」

**通用判斷**: 如果 When 是讀取操作且需要回傳值供 Then 驗證，就使用此 Handler

## Task
調用 HTTP GET API，將 response 存入 ScenarioContext

## Key Difference
- **Command**: 修改狀態，調用 HTTP POST/PUT/DELETE，不驗證 response
- **Query**: 讀取資料，調用 HTTP GET，需要驗證 response

## E2E 特色
- 從 ScenarioContext 取得 user ID
- 使用 JwtHelper 生成 JWT token
- 使用 TestRestTemplate 打真實的 HTTP GET API
- 將 response 存入 ScenarioContext 供 ReadModel-Then-Handler 驗證

---

## 實作流程

Query Handler 的任務是**透過 HTTP API 讀取資料**。

### 步驟

1. **從 ScenarioContext 取得用戶 ID**
2. **使用 JwtHelper 生成 JWT Token**
3. **構建 URL（含 path/query parameters）**
4. **執行 HTTP GET 請求**（使用 TestRestTemplate）
5. **儲存 response 到 ScenarioContext**（供 ReadModel-Then-Handler 驗證）

---

## 關鍵概念

### 1. 從 ScenarioContext 取得 ID

```java
// 從 ScenarioContext 取得用戶 ID
String userId = testContext.getId(userName);
if (userId == null) {
    throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
}
```

### 2. 產生 JWT Token

```java
// 使用 JwtHelper 產生 Token
String token = jwtHelper.generateToken(userId);
```

### 3. 構建 URL

**Path Parameters**：
- 在 URL 路徑中直接替換參數

```java
// 例如: /api/v1/lessons/{lessonId}/progress
int lessonId = 1;
String url = "/api/v1/lessons/" + lessonId + "/progress";
```

**Query Parameters**：
- 使用 UriComponentsBuilder 或直接拼接

```java
// 例如: /api/v1/journeys/{journeyId}/lessons?chapterId={int}
String url = UriComponentsBuilder
    .fromPath("/api/v1/journeys/" + journeyId + "/lessons")
    .queryParam("chapterId", chapterId)
    .toUriString();
```

### 4. 執行 HTTP GET 請求

```java
HttpHeaders headers = new HttpHeaders();
headers.setBearerAuth(token);

HttpEntity<Void> request = new HttpEntity<>(headers);

ResponseEntity<String> response = testRestTemplate.exchange(
    url,
    HttpMethod.GET,
    request,
    String.class
);
```

### 5. 儲存 response 到 ScenarioContext

```java
testContext.setLastResponse(response);
```

**重要**：不在 Query Handler 中驗證 response 內容，由 ReadModel-Then-Handler 處理

---

## Pattern Examples (Java Cucumber)

### Query 單一記錄

```gherkin
When 用戶 "Alice" 查詢課程 1 的進度
```

```java
package com.wsa.platform.steps.query;

import com.wsa.platform.steps.ScenarioContext;
import com.wsa.platform.util.JwtHelper;
import io.cucumber.java.en.When;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;

public class LessonProgressQuerySteps {

    @Autowired
    private TestRestTemplate testRestTemplate;

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private JwtHelper jwtHelper;

    @When("用戶 {string} 查詢課程 {int} 的進度")
    public void 用戶查詢課程的進度(String userName, int lessonId) {
        // 1. 從 ScenarioContext 取得 user_id
        String userId = testContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
        }

        // 2. 產生 Token
        String token = jwtHelper.generateToken(userId);

        // 3. 構建 URL
        String url = "/api/v1/lessons/" + lessonId + "/progress";

        // 4. 執行 HTTP GET 請求
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);

        HttpEntity<Void> request = new HttpEntity<>(headers);

        ResponseEntity<String> response = testRestTemplate.exchange(
            url,
            HttpMethod.GET,
            request,
            String.class
        );

        // 5. 儲存結果
        testContext.setLastResponse(response);
    }
}
```

### Query 列表（無 Query Parameters）

```gherkin
When 用戶 "Alice" 查詢購物車中的所有商品
```

```java
package com.wsa.platform.steps.query;

import com.wsa.platform.steps.ScenarioContext;
import com.wsa.platform.util.JwtHelper;
import io.cucumber.java.en.When;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;

public class CartQuerySteps {

    @Autowired
    private TestRestTemplate testRestTemplate;

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private JwtHelper jwtHelper;

    @When("用戶 {string} 查詢購物車中的所有商品")
    public void 用戶查詢購物車中的所有商品(String userName) {
        String userId = testContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
        }

        String token = jwtHelper.generateToken(userId);

        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);

        HttpEntity<Void> request = new HttpEntity<>(headers);

        ResponseEntity<String> response = testRestTemplate.exchange(
            "/api/v1/cart/items",
            HttpMethod.GET,
            request,
            String.class
        );

        testContext.setLastResponse(response);
    }
}
```

### Query 列表（有 Query Parameters）

```gherkin
When 用戶 "Alice" 查詢類別為 "電子產品" 的商品列表
```

```java
package com.wsa.platform.steps.query;

import com.wsa.platform.steps.ScenarioContext;
import com.wsa.platform.util.JwtHelper;
import io.cucumber.java.en.When;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;
import org.springframework.web.util.UriComponentsBuilder;

public class ProductQuerySteps {

    @Autowired
    private TestRestTemplate testRestTemplate;

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private JwtHelper jwtHelper;

    @When("用戶 {string} 查詢類別為 {string} 的商品列表")
    public void 用戶查詢類別的商品列表(String userName, String category) {
        String userId = testContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
        }

        String token = jwtHelper.generateToken(userId);

        String url = UriComponentsBuilder
            .fromPath("/api/v1/products")
            .queryParam("category", category)
            .toUriString();

        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);

        HttpEntity<Void> request = new HttpEntity<>(headers);

        ResponseEntity<String> response = testRestTemplate.exchange(
            url,
            HttpMethod.GET,
            request,
            String.class
        );

        testContext.setLastResponse(response);
    }
}
```

### Query 訂單詳情

```gherkin
When 用戶 "Alice" 查詢訂單 "ORDER-123" 的詳情
```

```java
package com.wsa.platform.steps.query;

import com.wsa.platform.steps.ScenarioContext;
import com.wsa.platform.util.JwtHelper;
import io.cucumber.java.en.When;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;

public class OrderQuerySteps {

    @Autowired
    private TestRestTemplate testRestTemplate;

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private JwtHelper jwtHelper;

    @When("用戶 {string} 查詢訂單 {string} 的詳情")
    public void 用戶查詢訂單的詳情(String userName, String orderId) {
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
            HttpMethod.GET,
            request,
            String.class
        );

        testContext.setLastResponse(response);
    }
}
```

---

## Method Naming

**規則**:
- 單一記錄: `get{Entity}` 或 `get{Entity}{Aspect}`
- 列表: `list{Entities}` (複數形式)

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
| 訂單 "ORDER-123" | orderId="ORDER-123" | /orders/ORDER-123 |
| 商品 "PROD-001" | productId="PROD-001" | /products/PROD-001 |
| 課程 1 | lessonId=1 | /lessons/1 |

### Query Parameters

從 Gherkin 提取選填參數，使用 UriComponentsBuilder 添加：

| Gherkin 片段範例 | Query Parameter | UriComponentsBuilder |
|----------------|----------------|---------------------|
| 類別為 "電子產品" | category="電子產品" | .queryParam("category", "電子產品") |
| 狀態為 "已付款" | status="PAID" | .queryParam("status", "PAID") |
| 頁碼 1，每頁 10 筆 | page=1, pageSize=10 | .queryParam("page", 1).queryParam("pageSize", 10) |

---

## Critical Rules

### R1: Query 必須儲存 response 到 ScenarioContext
Query 的 response 會在 ReadModel-Then-Handler 中被使用。

```java
// ✅ 正確：儲存 response
ResponseEntity<String> response = testRestTemplate.exchange(...);
testContext.setLastResponse(response);

// ❌ 錯誤：沒有儲存
ResponseEntity<String> response = testRestTemplate.exchange(...);
// 沒有存入 ScenarioContext，ReadModel-Then-Handler 無法驗證
```

### R2: 使用 HTTP GET method
Query 操作必須使用 GET method。

```java
// ✅ 正確：使用 GET
testRestTemplate.exchange(url, HttpMethod.GET, request, String.class);

// ❌ 錯誤：使用 POST
testRestTemplate.exchange(url, HttpMethod.POST, request, String.class);
```

### R3: 必須從 ScenarioContext 取得 userId
Query 需要認證時，必須從 ScenarioContext 取得 userId。

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
testRestTemplate.exchange(url, HttpMethod.GET, request, String.class);
```

### R5: 不在 Query Handler 中驗證 response 內容
Query Handler 只負責執行請求並儲存，不驗證 response 的內容。

```java
// ✅ 正確：不驗證內容
ResponseEntity<String> response = testRestTemplate.exchange(...);
testContext.setLastResponse(response);

// ❌ 錯誤：在 Query Handler 中驗證
ResponseEntity<String> response = testRestTemplate.exchange(...);
JsonNode data = objectMapper.readTree(response.getBody());
assertThat(data.get("progress").asInt()).isEqualTo(80);  // 應該在 ReadModel-Then-Handler 中驗證
```

### R6: Query Parameters 使用 UriComponentsBuilder
如果有 query parameters，使用 UriComponentsBuilder 構建 URL。

```java
// ✅ 正確：使用 UriComponentsBuilder
String url = UriComponentsBuilder
    .fromPath("/api/v1/journeys/1/lessons")
    .queryParam("chapterId", 2)
    .toUriString();

// ❌ 錯誤：手動拼接可能導致編碼問題
String url = "/api/v1/journeys/1/lessons?chapterId=2";
```

### R7: Path Parameters 使用字串拼接
Path parameters 應該直接拼接到 URL。

```java
// ✅ 正確：直接拼接
int lessonId = 1;
String url = "/api/v1/lessons/" + lessonId + "/progress";

// 也可以用 String.format
String url = String.format("/api/v1/lessons/%d/progress", lessonId);
```

### R8: 使用 TestRestTemplate
必須使用 Spring Boot Test 的 TestRestTemplate。

```java
// ✅ 正確：使用 @Autowired TestRestTemplate
@Autowired
private TestRestTemplate testRestTemplate;

ResponseEntity<String> response = testRestTemplate.exchange(...);

// ❌ 錯誤：自己創建 RestTemplate
RestTemplate restTemplate = new RestTemplate();
```

---

## 不需要認證的 API

有些 Query API 不需要認證（如健康檢查、公開資料）。

```gherkin
When 我呼叫健康檢查 API
```

```java
package com.wsa.platform.steps.query;

import com.wsa.platform.steps.ScenarioContext;
import io.cucumber.java.en.When;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;

public class HealthCheckSteps {

    @Autowired
    private TestRestTemplate testRestTemplate;

    @Autowired
    private ScenarioContext testContext;

    @When("我呼叫健康檢查 API")
    public void 我呼叫健康檢查API() {
        // 不需要 token
        ResponseEntity<String> response = testRestTemplate.getForEntity(
            "/api/v1/health",
            String.class
        );
        testContext.setLastResponse(response);
    }
}
```

---

## Optional Query Parameters

有些 query parameters 是選填的，根據 Gherkin 是否提到來決定是否傳遞。

```gherkin
# 範例 1: 沒有提到 category
When 用戶 "Alice" 查詢商品列表
```

```java
// 不傳遞 category
ResponseEntity<String> response = testRestTemplate.exchange(
    "/api/v1/products",
    HttpMethod.GET,
    request,
    String.class
);
```

```gherkin
# 範例 2: 有提到 category
When 用戶 "Alice" 查詢類別為 "電子產品" 的商品列表
```

```java
// 傳遞 category
String url = UriComponentsBuilder
    .fromPath("/api/v1/products")
    .queryParam("category", "電子產品")
    .toUriString();

ResponseEntity<String> response = testRestTemplate.exchange(
    url,
    HttpMethod.GET,
    request,
    String.class
);
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
**文件版本**：E2E Cucumber BDD Version 1.0
**適用框架**：Java 17 + Spring Boot 3.2 + Cucumber 7.15 + TestRestTemplate
