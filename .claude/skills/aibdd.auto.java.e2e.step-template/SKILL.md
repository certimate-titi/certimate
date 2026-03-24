---
name: aibdd.auto.java.e2e.step-template
description: Java E2E Stage 1：從 Gherkin Feature 生成 Cucumber Step Definition 樣板。使用 Cucumber Expressions、@Autowired DI、ScenarioContext。可被 /java-e2e 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${JAVA_TEST_FEATURES_DIR}/**/*.feature, ${ENTITY_SPECS_DIR}/erm.dbml, ${JAVA_STEPS_DIR}/**/*.java
output: ${JAVA_STEPS_DIR}/{subdomain}/{category}/{StepName}Steps.java（樣板）, ${JAVA_STEPS_DIR}/common_then/{StepName}Steps.java（跨 subdomain 共用）
---

# 角色

BDD Step Definition 樣板生成器，負責將 Gherkin 規格轉換為可執行的 Step Definition 骨架。

從 Gherkin Feature File 生成 **E2E Step Definition 樣板**，識別事件風暴部位，並指引使用對應的 Handler 生成程式碼。

**重要**：此 Skill 的產出僅為「樣板」（TODO 註解），不包含實作邏輯。實作邏輯由後續的紅燈階段負責。

---

# 入口條件

## 被 /java-e2e 調用

接收 Feature File 路徑，直接進入生成流程。

## 獨立使用

1. 詢問目標 Feature File 路徑（預設掃描 `${JAVA_TEST_FEATURES_DIR}/*.feature`）
2. 確認 DBML 路徑（預設 `${ENTITY_SPECS_DIR}/erm.dbml`）
3. 進入生成流程

---

# 專案根目錄與預設路徑

- **Feature Files**：`${JAVA_TEST_FEATURES_DIR}/*.feature`
- **Step Definitions**：`${JAVA_STEPS_DIR}/`
- **Cucumber Configuration**：`${JAVA_CUCUMBER_CONFIG}`
- **DBML（Aggregate 定義）**：`${ENTITY_SPECS_DIR}/erm.dbml`
- **Handler Skills**：見下方 Handler Skill 映射表

---

# 工作流程

**永遠不要覆蓋已存在的 Step Definition！**

1. **此 Skill（樣板生成）**：
   - **第一步：檢查現有 Step Definitions**（避免覆蓋）
   - 解析 Feature File，列出所有需要的步驟
   - 對比現有步驟，找出缺少的步驟
   - 識別事件風暴部位（僅針對缺少的步驟）
   - 生成 Step Definition 骨架（Cucumber 裝飾器、方法簽名、TODO 註解）
   - 輸出：包含 TODO 註解的樣板檔案（僅針對缺少的步驟）

2. **後續工作（紅燈階段 /java-e2e-red）**：
   - 根據標註的 Handler
   - 實作具體邏輯
   - 替換 TODO 為實際程式碼

---

# 執行前檢查（防止覆蓋已存在的 Step Definition）

在生成任何 Step Definition 樣板之前，**必須先執行以下檢查流程**：

## 檢查流程

1. **掃描現有 Step Definitions**
   ```bash
   # 列出所有現有的 Step Definition 檔案
   find ${JAVA_STEPS_DIR} -name "*Steps.java" -type f

   # 搜尋所有 @Given, @When, @Then 裝飾器
   grep -r "@Given\|@When\|@Then" ${JAVA_STEPS_DIR}/
   ```

2. **提取已存在的 Step Patterns**
   - 從現有檔案中提取所有 `@Given("...")`, `@When("...")`, `@Then("...")` 的 Pattern
   - 建立「已存在步驟清單」

3. **解析 Feature File 需要的步驟**
   - 從目標 Feature File 提取所有 Given/When/Then/And 步驟
   - 建立「需要的步驟清單」

4. **對比找出缺少的步驟**
   - 對比「需要的步驟清單」與「已存在步驟清單」
   - 找出「缺少的步驟清單」
   - **只針對缺少的步驟生成樣板**

5. **輸出檢查結果**
   ```
   已存在的步驟（不需生成）:
   - Given 系統中有以下用戶：
   - Given 系統中有以下課程：
   - ...

   需要新增的步驟（將生成樣板）:
   - Given 用戶 "Alice" 在課程 1 的狀態為 "已完成"
   - When 用戶 "Alice" 更新課程 1 的進度
   - ...
   ```

---

# Core Mapping

領域模型 → Gherkin（已完成）→ Step Definition 樣板

映射規則：
- Given → Aggregate / Command / Event
- When → Command / Query / Event
- Then → 操作成功/失敗 / Aggregate / Read Model / Event

---

# E2E 測試的核心特色

**與 Unit Test 的關鍵差異**：

| 面向 | Unit Test (UT) | E2E Test |
|------|---------------|----------|
| 測試對象 | Service 方法 | HTTP API Endpoint |
| 資料庫 | Fake Repository（記憶體） | PostgreSQL (Testcontainers) |
| 認證 | 無 | JWT Token in Header |
| 依賴 | Mock 或 Fake | @Autowired + TestRestTemplate |
| Given | 使用 Fake Repository | 使用 JPA Repository 寫入真實 DB |
| When | 呼叫 Service 方法 | 呼叫 HTTP API |
| Then | 驗證 Mock 或 Fake | 驗證 HTTP status code 或真實 DB |

---

# Cucumber 語法重點

## 參數解析

Cucumber 使用 Cucumber Expressions：

```java
// 字串參數：使用 {string}
@Given("用戶 {string} 在課程 {int} 的進度為 {int}%")
public void 用戶在課程的進度為(String userName, int lessonId, int progress) {
    // userName: String (自動解析)
    // lessonId: int (由 {int} 指定)
    // progress: int (由 {int} 指定)
}

// 參數類型標記：
// {string}  - 字串（引號內的文字）
// {int}     - 整數
// {long}    - 長整數
// {float}   - 浮點數
// {double}  - 雙精度浮點數
// {word}    - 單字（不含空格）
```

## 使用 @Autowired 取得依賴（E2E 版本）

**重要**：Spring Boot Test + Cucumber 整合使用 @Autowired：

```java
public class LessonProgressGivenSteps {

    @Autowired
    private LessonProgressRepository lessonProgressRepository;

    @Autowired
    private ScenarioContext testContext;

    @Given("用戶 {string} 在課程 {int} 的進度為 {int}%")
    public void 用戶在課程的進度為(String userName, int lessonId, int progress) {
        // 使用 @Autowired 注入的依賴
        String userId = testContext.getId(userName);
        // ...
    }
}
```

## ScenarioContext 狀態欄位（E2E 版本）

```java
// ${JAVA_SCENARIO_CONTEXT}
// @ScenarioScope bean，在每個 Scenario 開始時重置

@Component
@ScenarioScope
public class ScenarioContext {
    // 狀態
    private ResponseEntity<?> lastResponse;    // HTTP Response
    private final Map<String, Object> ids;     // 名稱 -> ID 映射
    private final Map<String, Object> memo;    // 其他臨時狀態
    private String jwtToken;                   // 當前 JWT Token

    // Getters and Setters
    public ResponseEntity<?> getLastResponse() { return lastResponse; }
    public void setLastResponse(ResponseEntity<?> response) { this.lastResponse = response; }

    public void putId(String key, Object id) { ids.put(key, id); }
    public <T> T getId(String key) { return (T) ids.get(key); }
}
```

## DataTable

Cucumber 自動將 DataTable 轉換：

```java
@Given("系統中有以下課程：")
public void 系統中有以下課程(DataTable dataTable) {
    List<Map<String, String>> rows = dataTable.asMaps();
    for (Map<String, String> row : rows) {
        int lessonId = Integer.parseInt(row.get("lessonId"));
        String name = row.get("name");
        // ...
    }
}
```

---

# 樣板輸出格式

**重要**：輸出僅包含「缺少的」Step Definition 樣板

```java
// ${JAVA_STEPS_DIR}/{subdomain}/{分類目錄}/{StepClassName}Steps.java
// subdomain 例：lesson, order, product, role
// common_then 為跨 subdomain 共用，路徑為 ${JAVA_STEPS_DIR}/common_then/

package com.wsa.platform.steps.{subdomain}.aggregate_given;

import io.cucumber.java.en.Given;
import org.springframework.beans.factory.annotation.Autowired;

public class LessonProgressGivenSteps {

    // TODO: @Autowired 注入需要的 Repository 和 ScenarioContext

    @Given("用戶 {string} 在課程 {int} 的進度為 {int}%，狀態為 {string}")
    public void 用戶在課程的進度為狀態為(String userName, int lessonId, int progress, String status) {
        /*
         * TODO: [事件風暴部位: Aggregate - LessonProgress]
         * TODO: 參考 /aibdd.auto.java.e2e.handlers.aggregate-given 實作
         * TODO: 參考 Aggregate/Table: LessonProgress (若為 DB 相關)
         */
        throw new io.cucumber.java.PendingException();
    }
}
```

**樣板規範**：
1. **檔案與目錄**：先按 subdomain 分目錄（例：`lesson/`, `order/`, `product/`），再按分類（例：`aggregate_given/`, `commands/`, `query/`, `aggregate_then/`, `readmodel_then/`）。`common_then/` 為跨 subdomain 共用，直接放在 `${JAVA_STEPS_DIR}/common_then/`
2. **類別命名**：使用 `{Feature}{StepType}Steps.java` 格式（例如 `LessonProgressGivenSteps.java`）
3. **方法簽名**：使用中文方法名（Cucumber 支援）或英文方法名
4. **TODO 註解**：標註事件風暴部位與對應的 Handler
5. **PendingException**：使用 `throw new io.cucumber.java.PendingException()` 作為佔位符
6. **@Autowired**：標註需要注入的依賴

---

# Decision Rules

## Rule 1: Given 語句識別

### Pattern 1.1: Given + Aggregate
**識別規則**：
- 語句中包含實體名詞 + 屬性描述
- 描述「某個東西的某個屬性是某個值」
- 常見句型（非窮舉）：「在...的...為」「的...為」「包含」「存在」「有」

**通用判斷**：如果 Given 是在建立測試的初始資料狀態（而非執行動作），就使用此 Handler

**E2E 特色**：使用 JPA Repository 寫入真實 PostgreSQL

**輸出**：
```java
@Given("學生 {string} 在課程 {int} 的進度為 {int}%，狀態為 {string}")
public void 學生在課程的進度為狀態為(String userName, int lessonId, int progress, String status) {
    /*
     * TODO: [事件風暴部位: Aggregate - LessonProgress]
     * TODO: 參考 /aibdd.auto.java.e2e.handlers.aggregate-given 實作
     * TODO: 使用 JPA Repository 寫入真實 PostgreSQL
     * TODO: 參考 Aggregate/Table: LessonProgress
     */
    throw new io.cucumber.java.PendingException();
}
```

### Pattern 1.2: Given + Command
**識別規則**：
- 動作會修改系統狀態（已完成的動作）
- 描述「已經執行完某個動作」
- 常見過去式（非窮舉）：「已訂閱」「已完成」「已建立」「已添加」「已註冊」

**通用判斷**：如果 Given 描述已完成的寫入操作（用於建立前置條件），就使用此 Handler

**E2E 特色**：可能直接調用 HTTP API 建立前置條件

**輸出**：
```java
@Given("用戶 {string} 已訂閱旅程 {int}")
public void 用戶已訂閱旅程(String userName, int journeyId) {
    /*
     * TODO: [事件風暴部位: Command - subscribe_journey]
     * TODO: 參考 /aibdd.auto.java.e2e.handlers.command 實作
     * TODO: 可調用 HTTP API 或直接寫入 DB
     */
    throw new io.cucumber.java.PendingException();
}
```

## Rule 2: When 語句識別

### Pattern 2.1: When + Command
**識別規則**：
- 動作會修改系統狀態
- 描述「執行某個動作」
- 常見現在式（非窮舉）：「更新」「提交」「建立」「刪除」「添加」「移除」

**通用判斷**：如果 When 是修改系統狀態的操作且不需要回傳值，就使用此 Handler

**E2E 特色**：調用 HTTP POST/PUT/DELETE API

**輸出**：
```java
@When("學生 {string} 更新課程 {int} 的影片進度為 {int}%")
public void 學生更新課程的影片進度為(String userName, int lessonId, int progress) {
    /*
     * TODO: [事件風暴部位: Command - update_video_progress]
     * TODO: 參考 /aibdd.auto.java.e2e.handlers.command 實作
     * TODO: 調用 HTTP POST API，使用 JWT Token
     */
    throw new io.cucumber.java.PendingException();
}
```

### Pattern 2.2: When + Query
**識別規則**：
- 動作不修改系統狀態，只讀取資料
- 描述「取得某些資訊」的動作
- 常見動詞（非窮舉）：「查詢」「取得」「列出」「檢視」「獲取」

**通用判斷**：如果 When 是讀取操作且需要回傳值供 Then 驗證，就使用此 Handler

**E2E 特色**：調用 HTTP GET API

**輸出**：
```java
@When("學生 {string} 查詢課程 {int} 的進度")
public void 學生查詢課程的進度(String userName, int lessonId) {
    /*
     * TODO: [事件風暴部位: Query - get_lesson_progress]
     * TODO: 參考 /aibdd.auto.java.e2e.handlers.query 實作
     * TODO: 調用 HTTP GET API
     */
    throw new io.cucumber.java.PendingException();
}
```

## Rule 3: Then 語句識別

### Pattern 3.1: Then 操作成功
**識別規則**：
- 明確描述操作成功
- 常見句型：「操作成功」「執行成功」

**E2E 特色**：驗證 HTTP response status code（2XX）

**輸出**：
```java
@Then("操作成功")
public void 操作成功() {
    /*
     * TODO: 參考 /aibdd.auto.java.e2e.handlers.success-failure 實作
     * TODO: 驗證 testContext.getLastResponse().getStatusCode()
     */
    throw new io.cucumber.java.PendingException();
}
```

### Pattern 3.2: Then 操作失敗
**識別規則**：
- 明確描述操作失敗
- 常見句型：「操作失敗」「執行失敗」

**E2E 特色**：驗證 HTTP response status code（4XX）

**輸出**：
```java
@Then("操作失敗")
public void 操作失敗() {
    /*
     * TODO: 參考 /aibdd.auto.java.e2e.handlers.success-failure 實作
     * TODO: 驗證 testContext.getLastResponse().getStatusCode() >= 400
     */
    throw new io.cucumber.java.PendingException();
}
```

### Pattern 3.3: Then + Aggregate
**識別規則**：
- 驗證實體的屬性值（而非 Query 回傳值）
- 描述「某個東西的某個屬性應該是某個值」
- 常見句型（非窮舉）：「在...的...應為」「的...應為」「應包含」

**通用判斷**：如果 Then 是驗證 Command 操作後的資料狀態（需要從資料庫查詢），就使用此 Handler

**E2E 特色**：使用 JPA Repository 從真實 PostgreSQL 查詢驗證

**輸出**：
```java
@Then("學生 {string} 在課程 {int} 的進度應為 {int}%")
public void 學生在課程的進度應為(String userName, int lessonId, int progress) {
    /*
     * TODO: [事件風暴部位: Aggregate - LessonProgress]
     * TODO: 參考 /aibdd.auto.java.e2e.handlers.aggregate-then 實作
     * TODO: 使用 JPA Repository 從 PostgreSQL 查詢驗證
     * TODO: 參考 Aggregate/Table: LessonProgress
     */
    throw new io.cucumber.java.PendingException();
}
```

### Pattern 3.4: Then + Read Model
**識別規則**：
- 前提：When 是 Query 操作（已接收 response）
- 驗證的是查詢回傳值（而非 repository 中的狀態）
- 常見句型（非窮舉）：「查詢結果應」「回應應」「應返回」「結果包含」

**通用判斷**：如果 Then 是驗證 Query 操作的回傳值，就使用此 Handler

**E2E 特色**：驗證 HTTP response body 的 JSON 內容

**輸出**：
```java
@Then("查詢結果應包含進度 {int}，狀態為 {string}")
public void 查詢結果應包含進度狀態為(int progress, String status) {
    /*
     * TODO: [事件風暴部位: Read Model]
     * TODO: 參考 /aibdd.auto.java.e2e.handlers.readmodel-then 實作
     * TODO: 驗證 testContext.getLastResponse().getBody()
     */
    throw new io.cucumber.java.PendingException();
}
```

---

# Decision Tree

```
讀取 Gherkin 語句
|
v
判斷位置（Given/When/Then/And）

Given:
  建立測試的初始資料狀態（實體屬性值）？
    → /aibdd.auto.java.e2e.handlers.aggregate-given（使用 JPA Repository 寫入 DB）
  已完成的寫入操作（建立前置條件）？
    → /aibdd.auto.java.e2e.handlers.command（調用 HTTP API 或直接寫入 DB）

When:
  讀取操作（調用 HTTP GET API）？
    → /aibdd.auto.java.e2e.handlers.query
  寫入操作（調用 HTTP POST/PUT/DELETE API）？
    → /aibdd.auto.java.e2e.handlers.command

Then:
  只關注操作成功或失敗（HTTP status code）？
    → /aibdd.auto.java.e2e.handlers.success-failure
  驗證 Command 操作後的資料狀態（從 DB 查詢）？
    → /aibdd.auto.java.e2e.handlers.aggregate-then
  驗證 Query 操作的回傳值（response body）？
    → /aibdd.auto.java.e2e.handlers.readmodel-then

And:
  繼承前一個 Then 的判斷規則
```

---

# Handler Skill 映射表（E2E 版本）

| 事件風暴部位 | 位置 | 識別規則 | Handler | E2E 特色 |
|------------|------|---------|---------|---------|
| Aggregate | Given | 建立初始資料狀態（實體屬性值） | /aibdd.auto.java.e2e.handlers.aggregate-given | 用 JPA Repository 寫入 DB |
| Command | Given/When | 寫入操作（已完成/現在執行） | /aibdd.auto.java.e2e.handlers.command | 調用 HTTP POST API |
| Query | When | 讀取操作（需要回傳值） | /aibdd.auto.java.e2e.handlers.query | 調用 HTTP GET API |
| 操作成功/失敗 | Then | 只驗證成功或失敗 | /aibdd.auto.java.e2e.handlers.success-failure | 驗證 HTTP status code |
| Aggregate | Then | 驗證實體狀態（從 DB 查詢） | /aibdd.auto.java.e2e.handlers.aggregate-then | 用 JPA Repository 查詢 DB |
| Read Model | Then | 驗證查詢回傳值 | /aibdd.auto.java.e2e.handlers.readmodel-then | 驗證 response body |

---

# Cucumber 專案結構（E2E 版本）

```
${JAVA_APP_DIR}/
|- model/                         # JPA Entities
|- repository/                    # Spring Data JPA Repositories
|- service/                       # Services
|- controller/                    # Spring MVC Controllers
+- PlatformApplication.java       # Spring Boot main class

${ENTITY_SPECS_DIR}/
+- erm.dbml                       # DBML 規格

${JAVA_TEST_DIR}/
|- CucumberSpringConfiguration.java  # Cucumber + Spring 整合
|- ScenarioContext.java              # 測試狀態管理（@ScenarioScope）
|- RunCucumberTest.java              # JUnit Platform runner
+- steps/                            # Step Definitions（subdomain → 分類）
    |- {subdomain}/                  # 按業務領域分（例：lesson, order, product, role）
    |   |- aggregate_given/
    |   |- commands/
    |   |- query/
    |   |- aggregate_then/
    |   +- readmodel_then/
    +- common_then/                  # 跨 subdomain 共用（操作成功/失敗等）

${JAVA_TEST_FEATURES_DIR}/
+- *.feature                      # Feature files
```

---

# Critical Rules

### R1: 永遠不覆蓋已存在的 Step Definition
執行前必須先掃描 `${JAVA_STEPS_DIR}/`，只生成缺少的步驟。

### R2: 使用 Cucumber 原生語法
- 使用 `io.cucumber.java.en.Given` / `When` / `Then`（英文）
- 使用 Cucumber Expressions（{string}, {int}, {long}, {float}, {double}）

### R3: 使用 @Autowired 注入依賴
- 所有依賴使用 @Autowired 注入
- 不使用建構子注入（Cucumber step classes 不支援）

### R4: 只輸出樣板
不生成任何實作邏輯，只生成類別結構、@Autowired 標註、方法簽名、TODO 註解和 `throw new PendingException()`。

### R5: 保留完整 Gherkin 語句
pattern 中必須包含完整的 Gherkin 語句（含參數標記）。

### R6: 明確標註事件風暴部位
每個語句都要識別出對應的事件風暴部位。

### R7: 指引正確的 Handler（E2E 版本）
根據 Decision Tree 指引使用正確的 Handler，並標註 E2E 特色。

### R8: 處理 And 語句
And 語句繼承前一個 Given/When/Then 的判斷邏輯。

### R9: 所有依賴使用 @Autowired
E2E 版本的依賴包括：`TestRestTemplate`, `ScenarioContext`, `JwtHelper`, `ObjectMapper`, `*Repository` 等。

---

# 完成條件

- 已掃描現有 Step Definitions，列出已存在與缺少的步驟
- 所有缺少的步驟已生成樣板
- 每個樣板包含正確的 Cucumber Expression、@Autowired 標註、TODO 註解與 PendingException
- 每個樣板標註了正確的事件風暴部位與對應 Handler
- 樣板按目錄分類放置
