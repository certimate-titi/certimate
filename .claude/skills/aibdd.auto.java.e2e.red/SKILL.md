---
name: aibdd.auto.java.e2e.red
description: Java E2E Stage 2：紅燈生成器。將 Step Definition 樣板轉換為完整 E2E 測試程式碼 + JPA Entity + Spring Data JPA Repository。預期失敗：HTTP 404。可被 /java-e2e 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${JAVA_STEPS_DIR}/**/*.java（樣板）, ${ENTITY_SPECS_DIR}/erm.dbml, handler skills
output: ${JAVA_STEPS_DIR}/**/*.java（完整）, ${JAVA_MODEL_DIR}/**/*.java, ${JAVA_REPOSITORY_DIR}/**/*.java
---

# 角色

E2E 紅燈生成器。將 Step Definition 樣板（純註解）轉換為可執行的 E2E 測試程式碼，依照註解中的 Handler 指引生成對應的程式碼，生成紅燈測試。

---

# 入口條件

## 被 /java-e2e 調用

接收 Step Definition 樣板路徑，直接進入生成流程。

## 獨立使用

1. 詢問目標 Step Definition 樣板路徑（預設掃描 `${JAVA_STEPS_DIR}/**/*Steps.java`）
2. 確認 DBML 路徑（預設 `${ENTITY_SPECS_DIR}/erm.dbml`）
3. 進入生成流程

---

# Core Task

E2E Step Definition 樣板（註解）→ 可執行 E2E 測試程式碼（紅燈）

---

# Input

1. Step Definition 樣板（包含 TODO 註解，來自 /java-e2e-step-template）
2. DBML（Aggregate 定義）：`${ENTITY_SPECS_DIR}/erm.dbml`
3. Tech Stack：Java 17 + Spring Boot 3.2 + Cucumber 7.15 + JPA + TestRestTemplate + Testcontainers + PostgreSQL
4. Handler Skills：`對應的 handler skills

---

# Output

## 1. Step Definition 程式碼

完整的 E2E Step Definition 程式碼，包含：
- 必要的 import
- @Autowired 注入依賴
- 完整的測試邏輯實作
- 所有測試邏輯完整實作（無 PendingException）

## 2. 基礎設施定義

**如果測試中需要用到的基礎設施尚不存在**，則按以下規則定義：

### 生產環境基礎設施（在 src/main/java/ 中定義）
- **JPA Entities**：放在 `${JAVA_MODEL_DIR}/`
- **Repositories**：放在 `${JAVA_REPOSITORY_DIR}/`

### 測試專用基礎設施（在 src/test/java/ 中定義）
- **CucumberSpringConfiguration**：管理 Testcontainers + PostgreSQL + Spring Context
- **ScenarioContext**：@ScenarioScope bean 管理測試狀態
- **JwtHelper**：JWT Token 生成輔助工具

**為什麼要放在 src/main/java/?**
- 這些是生產環境也需要的程式碼
- 綠燈階段實作 API 時，Controller/Service 會直接使用這些 Entities 和 Repositories
- 測試只是使用它們，不應該擁有它們

**關鍵原則：僅定義介面和基礎設施，不實作後端業務邏輯**
- JPA Entity 和 Repository 介面定義完整（放在 src/main/java/）
- 後端 API (Controller/Service) 不實作
- E2E 測試會因為 HTTP 404 而失敗（後端 API 尚未實作）

---

# API JSON 欄位命名規則

- 所有 API Request/Response 的 JSON 欄位使用 **camelCase**（Java 慣例）
- Gherkin Feature File 使用自然語言，不受此限制

```java
// 正確
Map.of("lessonId", 1, "progress", 80)
assertThat(data.get("userId").asText()).isEqualTo("Alice");

// 錯誤
Map.of("lesson_id", 1, "progress", 80)
assertThat(data.get("user_id").asText()).isEqualTo("Alice");
```

---

# 紅燈階段的核心原則

## E2E 測試的紅燈特色（Cucumber 版本）

| 面向 | Unit Test 紅燈 | E2E Test 紅燈 |
|------|---------------|--------------|
| 測試失敗原因 | Service 方法拋出異常 | HTTP 404 Not Found |
| 需要定義的東西 | Entity, Repository, Service 介面 | JPA Entity, Repository 介面 |
| 不需要定義的東西 | 業務邏輯 | 後端 API (Controller/Service) |
| 資料庫 | Mock 或 Fake | 真實 PostgreSQL（Testcontainers） |
| 測試框架 | Cucumber + Mock | Cucumber + TestRestTemplate |

## 要做的事
1. **完整實作 Step Definition 程式碼**：測試邏輯必須完整且正確
2. **定義 JPA Entities**：在 `${JAVA_MODEL_DIR}/` 中創建 Entity
3. **定義 Repository 介面**：在 `${JAVA_REPOSITORY_DIR}/` 中創建 Spring Data JPA Repository
4. **確保 CucumberSpringConfiguration 正確設定**：Testcontainers + PostgreSQL + Spring Context

## 不要做的事
1. **不要實作後端 API**：Controller 和 Service 不實作
2. **不要讓測試通過**：測試應該因為 HTTP 404 而失敗（紅燈）
3. **不要跳過基礎設施定義**：測試需要的 Entity、Repository 必須定義

## 為什麼要這樣？

這是 TDD 的核心流程：
1. **紅燈**：寫測試 + 定義基礎設施（測試失敗：HTTP 404）← 我們現在在這
2. **綠燈**：實作後端 API（測試通過）
3. **重構**：優化程式碼品質（測試持續通過）

---

# Execution Steps

## Step 1: 讀取 Step Definition 樣板

識別每個 step 中的 TODO 註解及其對應的 Handler

```java
@Given("用戶 {string} 在課程 {int} 的進度為 {int}%，狀態為 {string}")
public void 用戶在課程的進度為狀態為(String userName, int lessonId, int progress, String status) {
    /*
     * TODO: [事件風暴部位: Aggregate - LessonProgress]
     * TODO: 參考 /aibdd.auto.java.e2e.handlers.aggregate-given 實作
     */
    throw new io.cucumber.java.PendingException();
}
```

## Step 2: 逐步生成程式碼

根據每個 TODO 的 Handler 生成對應的程式碼

### 範例流程

**Given 區塊（/aibdd.auto.java.e2e.handlers.aggregate-given）**：
- 使用 @Autowired 注入 Repository
- 創建 JPA Entity instance
- 使用 repository.save() 寫入 DB
- 儲存 ID 到 ScenarioContext

**When 區塊（/aibdd.auto.java.e2e.handlers.command）**：
- 從 ScenarioContext 取得 userId
- 使用 JwtHelper 生成 token
- 構建 request body（camelCase 欄位名）
- 使用 TestRestTemplate 發送請求
- 儲存 response 到 ScenarioContext

**Then 區塊（/aibdd.auto.java.e2e.handlers.success-failure）**：
- 從 ScenarioContext 取得 response
- 驗證 response.getStatusCode()

**Then + Aggregate（/aibdd.auto.java.e2e.handlers.aggregate-then）**：
- 使用 @Autowired 注入 Repository
- 使用 repository 查詢 entity
- assertThat(entity.getField()).isEqualTo(expected)

## Step 3: 生成測試基礎設施

包含必要的 Entities、Repositories

---

# Complete Example

## Input（Step Definition 樣板）

```java
// ${JAVA_STEPS_DIR}/lesson/aggregate_given/LessonProgressGivenSteps.java

package com.wsa.platform.steps.lesson.aggregate_given;

import io.cucumber.java.en.Given;

public class LessonProgressGivenSteps {

    @Given("用戶 {string} 在課程 {int} 的進度為 {int}%，狀態為 {string}")
    public void 用戶在課程的進度為狀態為(String userName, int lessonId, int progress, String status) {
        /*
         * TODO: [事件風暴部位: Aggregate - LessonProgress]
         * TODO: 參考 /aibdd.auto.java.e2e.handlers.aggregate-given 實作
         */
        throw new io.cucumber.java.PendingException();
    }
}
```

## Output 1（Step Definition 程式碼）

```java
// ${JAVA_STEPS_DIR}/lesson/aggregate_given/LessonProgressGivenSteps.java

package com.wsa.platform.steps.lesson.aggregate_given;

import com.wsa.platform.model.LessonProgress;
import com.wsa.platform.model.ProgressStatus;
import com.wsa.platform.repository.LessonProgressRepository;
import com.wsa.platform.steps.ScenarioContext;
import io.cucumber.java.en.Given;
import org.springframework.beans.factory.annotation.Autowired;

public class LessonProgressGivenSteps {

    @Autowired
    private LessonProgressRepository lessonProgressRepository;

    @Autowired
    private ScenarioContext testContext;

    @Given("用戶 {string} 在課程 {int} 的進度為 {int}%，狀態為 {string}")
    public void 用戶在課程的進度為狀態為(String userName, int lessonId, int progress, String status) {
        ProgressStatus dbStatus = mapStatus(status);

        String userId = testContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID，請先在 Given 步驟中建立用戶");
        }

        LessonProgress progressEntity = new LessonProgress();
        progressEntity.setUserId(userId);
        progressEntity.setLessonId(lessonId);
        progressEntity.setProgress(progress);
        progressEntity.setStatus(dbStatus);

        lessonProgressRepository.save(progressEntity);
    }

    private ProgressStatus mapStatus(String status) {
        return switch (status) {
            case "進行中" -> ProgressStatus.IN_PROGRESS;
            case "已完成" -> ProgressStatus.COMPLETED;
            case "未開始" -> ProgressStatus.NOT_STARTED;
            default -> ProgressStatus.valueOf(status);
        };
    }
}
```

## Output 2（JPA Entity）

```java
// ${JAVA_MODEL_DIR}/LessonProgress.java

package com.wsa.platform.model;

import jakarta.persistence.*;

@Entity
@Table(name = "lesson_progress")
public class LessonProgress {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "user_id", nullable = false)
    private String userId;

    @Column(name = "lesson_id", nullable = false)
    private Integer lessonId;

    @Column(nullable = false)
    private Integer progress = 0;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private ProgressStatus status;

    // Getters and Setters
    // ...
}
```

## Output 3（Repository）

```java
// ${JAVA_REPOSITORY_DIR}/LessonProgressRepository.java

package com.wsa.platform.repository;

import com.wsa.platform.model.LessonProgress;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface LessonProgressRepository extends JpaRepository<LessonProgress, Integer> {
    Optional<LessonProgress> findByUserIdAndLessonId(String userId, Integer lessonId);
}
```

## 預期結果：測試執行會失敗（紅燈）

```bash
$ mvn clean test -Dtest=RunCucumberTest

Feature: 課程平台 - 增加影片進度
  Rule: 影片進度必須單調遞增
    Scenario: 成功增加影片進度
      Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"  # Passed
      When 用戶 "Alice" 更新課程 1 的影片進度為 80%              # Failed

java.lang.AssertionError: 預期成功（2XX），實際 404 NOT_FOUND
```

**這就是紅燈**：
- Step Definition 程式碼完整且正確
- JPA Entity 定義完整
- Repository 介面定義完整並使用真實資料庫
- 測試基礎設施（CucumberSpringConfiguration）設定完成
- 後端 API 未實作（HTTP 404）
- 測試執行會失敗

---

# 步驟 7: 移除 @ignore tag

當你完成這個 feature 的紅燈實作後，請把該 feature file 第一行的 `@ignore` 刪掉，讓它後續可以被「排除 `@ignore` 的回歸測試」涵蓋到。

**移除時機**：
- 完成所有 Step Definitions 的實作
- 完成所有必要的 Entities 和 Repositories
- 確認測試執行後達到預期的紅燈狀態（HTTP 404）

**移除後驗證**：
```bash
# 執行該 feature 的測試，確認達到紅燈狀態
mvn clean test -Dtest=RunCucumberTest -Dcucumber.features=${JAVA_TEST_FEATURES_DIR}/01-增加影片進度.feature

# 執行所有未標記 @ignore 的測試
mvn clean test -Dtest=RunCucumberTest -Dcucumber.filter.tags="not @ignore"
```

---

# Critical Rules

### R1: Step Definition 程式碼必須完整
測試邏輯必須完整實作，不能有 `throw new PendingException()` 或空方法。

```java
// 正確：完整的測試邏輯
@When("用戶 {string} 更新課程 {int} 的影片進度為 {int}%")
public void 用戶更新課程的影片進度為(String userName, int lessonId, int progress) {
    String userId = testContext.getId(userName);
    String token = jwtHelper.generateToken(userId);

    Map<String, Object> requestBody = Map.of("lessonId", lessonId, "progress", progress);

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

    testContext.setLastResponse(response);
}

// 錯誤：測試邏輯不完整
@When("用戶 {string} 更新課程 {int} 的影片進度為 {int}%")
public void 用戶更新課程的影片進度為(String userName, int lessonId, int progress) {
    throw new io.cucumber.java.PendingException();
}
```

### R2: 所有依賴使用 @Autowired
必須使用 @Autowired 注入所有依賴。

```java
// 正確：使用 @Autowired
public class VideoProgressSteps {

    @Autowired
    private TestRestTemplate testRestTemplate;

    @Autowired
    private ScenarioContext testContext;

    @Autowired
    private JwtHelper jwtHelper;
}

// 錯誤：手動建構
public class VideoProgressSteps {
    private TestRestTemplate testRestTemplate = new TestRestTemplate();  // 錯誤
}
```

### R3: JPA Entity 必須完整定義且放在 src/main/java/ 中
Entity 定義必須包含所有欄位、型別、主鍵，並放在 `${JAVA_MODEL_DIR}/` 中。

### R4: Repository 必須使用 Spring Data JPA 且放在 src/main/java/ 中
Repository 介面必須繼承 JpaRepository，並放在 `${JAVA_REPOSITORY_DIR}/` 中。

### R5: 不實作後端 API
紅燈階段不建立 Controller 和 Service。

### R6: 測試會失敗（紅燈）
紅燈階段的測試執行後應該失敗（HTTP 404），這是預期的結果。

### R7: 使用 Testcontainers 啟動真實資料庫
CucumberSpringConfiguration 必須使用 Testcontainers 啟動 PostgreSQL。

### R8: ScenarioContext 用於跨步驟傳遞資料
使用 ScenarioContext（@ScenarioScope）在 Given/When/Then 之間傳遞資料。

```java
// 正確：使用 ScenarioContext 傳遞資料
// Given
testContext.putId(userName, userId);

// When
String userId = testContext.getId(userName);
String token = jwtHelper.generateToken(userId);
ResponseEntity<String> response = testRestTemplate.exchange(...);
testContext.setLastResponse(response);

// Then
ResponseEntity<?> response = testContext.getLastResponse();
assertThat(response.getStatusCode()).isIn(HttpStatus.OK, HttpStatus.CREATED);
```

### R9: 使用 camelCase 構建 Request
Request body 的欄位名稱使用 camelCase。

```java
// 正確：使用 camelCase
Map.of("lessonId", 1, "progress", 80)

// 錯誤：使用 snake_case
Map.of("lesson_id", 1, "progress", 80)
```

---

# 完成條件

- 所有 Step Definition 的 PendingException 已替換為完整的測試邏輯
- 所有必要的 JPA Entities 已定義（放在 `${JAVA_MODEL_DIR}/`）
- 所有必要的 Repository 介面已定義（放在 `${JAVA_REPOSITORY_DIR}/`）
- CucumberSpringConfiguration 正確設定
- 測試執行達到紅燈狀態（HTTP 404，後端 API 未實作）
- 該 Feature File 的 `@ignore` tag 已移除
