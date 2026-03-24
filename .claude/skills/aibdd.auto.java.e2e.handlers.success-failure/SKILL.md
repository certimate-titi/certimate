---
name: aibdd.auto.java.e2e.handlers.success-failure
description: 當在 .isa.feature 這類 ISA Gherkin 測試中驗證操作成功或失敗時，參考此規範。
user-invocable: false
---

# Success-Failure-Handler (E2E Cucumber Version)

## Trigger
Then 語句描述**操作的成功或失敗結果**（驗證 HTTP status code）

**識別規則**:
- 明確描述操作結果（成功/失敗）
- 常見句型:「操作成功」「操作失敗」「執行成功」「執行失敗」

**通用判斷**: 如果 Then 只關注操作是否成功（HTTP 2XX）或失敗（HTTP 4XX），就使用此 Handler

## Task
從 ScenarioContext 取得 response，驗證 HTTP status code

## E2E 特色
- 從 ScenarioContext 取得 HTTP response
- 驗證 response.getStatusCode()
- 成功：HTTP 2XX（200, 201, 204）
- 失敗：HTTP 4XX（400, 401, 403, 404, 409 等）

---

## Pattern 1: 操作成功 (Java Cucumber)

```gherkin
When 用戶 "Alice" 更新課程 1 的影片進度為 80%
Then 操作成功
```

```java
package com.wsa.platform.steps.common_then;

import com.wsa.platform.steps.ScenarioContext;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;

public class SuccessSteps {

    @Autowired
    private ScenarioContext testContext;

    private static final Set<HttpStatus> SUCCESS_STATUSES = Set.of(
            HttpStatus.OK,
            HttpStatus.CREATED,
            HttpStatus.NO_CONTENT
    );

    @Then("操作成功")
    public void 操作成功() {
        ResponseEntity<?> response = testContext.getLastResponse();

        // 驗證 HTTP status code 為 2XX
        assertThat(SUCCESS_STATUSES)
                .as("預期成功（2XX），實際 %s: %s",
                        response.getStatusCode(),
                        response.getBody())
                .contains(response.getStatusCode());
    }
}
```

---

## Pattern 2: 操作失敗 (Java Cucumber)

```gherkin
When 用戶 "Alice" 更新課程 1 的影片進度為 60%
Then 操作失敗
```

```java
package com.wsa.platform.steps.common_then;

import com.wsa.platform.steps.ScenarioContext;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import static org.assertj.core.api.Assertions.assertThat;

public class FailureSteps {

    @Autowired
    private ScenarioContext testContext;

    @Then("操作失敗")
    public void 操作失敗() {
        ResponseEntity<?> response = testContext.getLastResponse();

        // 驗證 HTTP status code 為 4XX
        int statusCode = response.getStatusCode().value();
        assertThat(statusCode)
                .as("預期失敗（4XX），實際 %d: %s",
                        statusCode,
                        response.getBody())
                .isBetween(400, 499);
    }
}
```

---

## 更精確的 Status 驗證

如果需要驗證特定的 status code，可以提供更精確的步驟：

---

## Error Message Verification

除了驗證 status code，還可以驗證錯誤訊息：

```gherkin
When 用戶 "Alice" 更新課程 1 的影片進度為 60%
Then 操作失敗
And 錯誤訊息應為 "進度不可倒退"
```

```java
package com.wsa.platform.steps.common_then;

import com.wsa.platform.steps.ScenarioContext;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;

import static org.assertj.core.api.Assertions.assertThat;

public class ErrorMessageSteps {

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private ObjectMapper objectMapper;

    @Then("錯誤訊息應為 {string}")
    public void 錯誤訊息應為(String message) throws Exception {
        ResponseEntity<?> response = testContext.getLastResponse();
        String body = (String) response.getBody();
        JsonNode data = objectMapper.readTree(body);

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

```java
// src/test/java/com/wsa/platform/steps/common_then/SuccessSteps.java

package com.wsa.platform.steps.common_then;

import com.wsa.platform.steps.ScenarioContext;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;

public class SuccessSteps {

    @Autowired
    private ScenarioContext testContext;

    private static final Set<HttpStatus> SUCCESS_STATUSES = Set.of(
            HttpStatus.OK,
            HttpStatus.CREATED,
            HttpStatus.NO_CONTENT
    );

    @Then("操作成功")
    public void 操作成功() {
        ResponseEntity<?> response = testContext.getLastResponse();
        assertThat(SUCCESS_STATUSES)
                .as("預期成功（2XX），實際 %s: %s",
                        response.getStatusCode(),
                        response.getBody())
                .contains(response.getStatusCode());
    }
}
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

```java
// src/test/java/com/wsa/platform/steps/common_then/FailureSteps.java

package com.wsa.platform.steps.common_then;

import com.wsa.platform.steps.ScenarioContext;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;

import static org.assertj.core.api.Assertions.assertThat;

public class FailureSteps {

    @Autowired
    private ScenarioContext testContext;

    @Then("操作失敗")
    public void 操作失敗() {
        ResponseEntity<?> response = testContext.getLastResponse();
        int statusCode = response.getStatusCode().value();
        assertThat(statusCode)
                .as("預期失敗（4XX），實際 %d: %s",
                        statusCode,
                        response.getBody())
                .isBetween(400, 499);
    }
}
```

---

## Critical Rules

### R1: 從 ScenarioContext 取得 response
不重新調用 API，使用 ScenarioContext 中儲存的 response。

```java
// ✅ 正確：從 ScenarioContext 取得
ResponseEntity<?> response = testContext.getLastResponse();
assertThat(SUCCESS_STATUSES).contains(response.getStatusCode());

// ❌ 錯誤：重新調用 API
ResponseEntity<String> response = testRestTemplate.exchange(...);
assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
```

### R2: 成功使用 2XX 範圍驗證
操作成功時，接受 200, 201, 204 等成功狀態碼。

```java
// ✅ 正確：接受多個成功狀態碼
Set<HttpStatus> successStatuses = Set.of(HttpStatus.OK, HttpStatus.CREATED, HttpStatus.NO_CONTENT);
assertThat(successStatuses).contains(response.getStatusCode());

// ⚠️ 也可以（如果確定只會回傳特定 code）
assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
```

### R3: 失敗使用 4XX 範圍驗證
操作失敗時，驗證狀態碼在 400-499 範圍內。

```java
// ✅ 正確：驗證 4XX 範圍
int statusCode = response.getStatusCode().value();
assertThat(statusCode).isBetween(400, 499);

// ⚠️ 也可以（如果確定只會回傳特定 code）
assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
```

### R4: 提供清晰的錯誤訊息
assert 失敗時提供清晰的訊息，包含實際的 status code 和 response body。

```java
// ✅ 正確：清晰的錯誤訊息
assertThat(SUCCESS_STATUSES)
        .as("預期成功（2XX），實際 %s: %s",
                response.getStatusCode(),
                response.getBody())
        .contains(response.getStatusCode());

// ❌ 錯誤：沒有訊息
assertThat(SUCCESS_STATUSES).contains(response.getStatusCode());
```

### R5: 不在 Success-Failure-Handler 中驗證 response 內容
只驗證 status code，不驗證 response body（那是 ReadModel-Then-Handler 的工作）。

```java
// ✅ 正確：只驗證 status code
ResponseEntity<?> response = testContext.getLastResponse();
assertThat(SUCCESS_STATUSES).contains(response.getStatusCode());

// ❌ 錯誤：驗證 response 內容
ResponseEntity<?> response = testContext.getLastResponse();
JsonNode data = objectMapper.readTree((String) response.getBody());
assertThat(data.get("progress").asInt()).isEqualTo(80);  // 這是 ReadModel-Then-Handler 的工作
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

```java
@Then("操作失敗")
public void 操作失敗() {
    ResponseEntity<?> response = testContext.getLastResponse();
    int statusCode = response.getStatusCode().value();
    assertThat(statusCode).isBetween(400, 499);
}
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

在這種情況下，ReadModel-Then-Handler 會隱含地驗證成功（因為如果失敗，JSON 解析會報錯）。

---

## File Organization

建議將 Success 和 Failure 的 step definitions 放在 `common_then/` 目錄：

```
src/test/java/com/wsa/platform/steps/
└── common_then/
    ├── SuccessSteps.java      # @Then("操作成功")
    ├── FailureSteps.java      # @Then("操作失敗")
```
