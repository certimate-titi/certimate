---
name: aibdd.auto.java.code-quality
description: Java 程式碼品質規範合集。包含 SOLID 設計原則、Step Definition 組織規範、StepDef Meta 註記清理、日誌實踐、程式架構、程式碼品質等六項規範。供 refactor 階段嚴格遵守。
user-invocable: false
---

# SOLID 設計原則

## 目的

確保程式碼好讀、好維護、好擴充。重構時必須遵守這些原則。

---

## S - Single Responsibility Principle（單一職責原則）

每個類別/方法只負責一件事。

**範例：**
```java
// ❌ Service 做太多事
@Service
public class AssignmentService {
    public void submitAssignment(Long userId, String content) {
        // 驗證權限
        if (!checkPermission(userId)) {
            throw new PermissionException();
        }
        // 驗證內容
        if (content.length() < 10) {
            throw new ValidationException();
        }
        // 儲存資料
        repository.save(...);
        // 發送通知
        sendEmail(userId);
    }
}

// ✅ 職責分離
@Service
public class AssignmentService {

    @Autowired
    private AssignmentRepository assignmentRepository;

    @Autowired
    private PermissionValidator permissionValidator;

    @Autowired
    private NotificationService notificationService;

    public void submitAssignment(Long userId, String content) {
        permissionValidator.validate(userId);  // 權限驗證交給專門的類別
        Assignment assignment = new Assignment(userId, content);
        assignmentRepository.save(assignment);
        notificationService.notify(userId);  // 通知交給專門的服務
    }
}
```

---

## O - Open/Closed Principle（開放封閉原則）

對擴展開放，對修改封閉。新增功能時應透過擴展而非修改現有程式碼。

```java
// ✅ 使用介面和策略模式
public interface PaymentStrategy {
    void pay(Order order);
}

@Service
public class CreditCardPayment implements PaymentStrategy {
    @Override
    public void pay(Order order) { /* 信用卡支付 */ }
}

@Service
public class BankTransferPayment implements PaymentStrategy {
    @Override
    public void pay(Order order) { /* 銀行轉帳 */ }
}

// 新增支付方式只需實作介面，不需修改現有程式碼
@Service
public class LinePay implements PaymentStrategy {
    @Override
    public void pay(Order order) { /* LINE Pay */ }
}
```

---

## L - Liskov Substitution Principle（里氏替換原則）

子類別應該可以替換父類別而不影響程式正確性。

---

## I - Interface Segregation Principle（介面隔離原則）

不應強迫客戶端依賴它不需要的介面。

```java
// ❌ 過大的介面
public interface UserService {
    void createUser();
    void updateUser();
    void deleteUser();
    void sendEmail();      // 不是所有實作都需要
    void generateReport(); // 不是所有實作都需要
}

// ✅ 介面隔離
public interface UserCrudService {
    void createUser();
    void updateUser();
    void deleteUser();
}

public interface EmailService {
    void sendEmail();
}

public interface ReportService {
    void generateReport();
}
```

---

## D - Dependency Inversion Principle（依賴反轉原則）

高層模組不應依賴低層模組，兩者都應依賴抽象。

**範例：**
```java
// ✅ Service 透過建構子或 @Autowired 注入 Repository
@Service
public class LessonProgressService {

    @Autowired
    private LessonProgressRepository lessonProgressRepository;

    @Autowired
    private JourneySubscriptionRepository journeySubscriptionRepository;

    public void updateProgress(Long userId, Long lessonId, int progress) {
        // 業務邏輯使用注入的 repository
        JourneySubscription subscription = journeySubscriptionRepository
                .findByUserId(userId)
                .orElseThrow(() -> new SubscriptionNotFoundException());
        // ...
    }
}
```

### Spring Boot 依賴注入

```java
// 建構子注入（推薦）
@Service
public class OrderService {
    private final OrderRepository orderRepository;
    private final ProductRepository productRepository;

    public OrderService(OrderRepository orderRepository, ProductRepository productRepository) {
        this.orderRepository = orderRepository;
        this.productRepository = productRepository;
    }
}

// 或使用 @Autowired
@Service
public class OrderService {
    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private ProductRepository productRepository;
}
```

---

## 檢查清單

- [ ] 每個類別/方法只負責一件事
- [ ] Service 透過 @Autowired 或建構子注入 Repository
- [ ] 高層模組不直接依賴低層模組
- [ ] 介面不過大，按職責分離

---

**文件建立日期**：2025-01-21
**文件版本**：E2E Cucumber BDD Version 1.0
**適用框架**：Java 17 + Spring Boot 3.2

---

# Step Definition 組織規範

## 目的

確保 Cucumber Step Definition 檔案組織清晰、易於維護。

---

## 組織原則

- 一個 Step Pattern 對應一個 Java class
- 使用 package 分類（`aggregate_given`, `commands`, `query` 等）
- 語意化類別名稱（避免 `Steps.java` 這類大雜燴）

---

## 目錄結構範例

```
src/test/java/com/wsa/platform/steps/
├── lesson/                          # {subdomain} 層
│   ├── aggregate_given/             # Given: 建立 Aggregate 狀態
│   │   ├── LessonProgressGivenSteps.java
│   │   ├── UserGivenSteps.java
│   │   └── JourneyGivenSteps.java
│   ├── commands/                    # When: 執行 Command
│   │   ├── UpdateVideoProgressSteps.java
│   │   └── SubscribeJourneySteps.java
│   ├── query/                       # When: 執行 Query
│   │   └── GetLessonProgressSteps.java
│   ├── aggregate_then/              # Then: 驗證 Aggregate 狀態
│   │   └── LessonProgressThenSteps.java
│   └── readmodel_then/              # Then: 驗證 ReadModel 結果
│       └── ProgressResultSteps.java
├── common_then/                     # Then: 通用驗證（成功/失敗）— 不分 subdomain
│   └── CommonThen.java
└── helpers/                         # 共用輔助類別
    ├── StatusMapping.java
    └── ScenarioContextHelper.java
```

---

## Spring Component Scanning

Step Definition 類別需要被 Spring 掃描到，確保 `CucumberSpringConfiguration` 配置正確：

```java
// src/test/java/com/wsa/platform/cucumber/CucumberSpringConfiguration.java
@CucumberContextConfiguration
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ComponentScan(basePackages = {
    "com.wsa.platform.steps",
    "com.wsa.platform.cucumber"
})
public class CucumberSpringConfiguration {
    // ...
}
```

---

## 共用邏輯提取

### 狀態映射

```java
// src/test/java/com/wsa/platform/steps/helpers/StatusMapping.java
public class StatusMapping {

    private static final Map<String, String> STATUS_MAPPING = Map.of(
        "進行中", "IN_PROGRESS",
        "已完成", "COMPLETED",
        "未開始", "NOT_STARTED"
    );

    public static String mapStatus(String chineseStatus) {
        return STATUS_MAPPING.getOrDefault(chineseStatus, chineseStatus);
    }
}
```

### ScenarioContext 操作

```java
// src/test/java/com/wsa/platform/steps/helpers/ScenarioContextHelper.java
@Component
public class ScenarioContextHelper {

    @Autowired
    private ScenarioContext scenarioContext;

    public String getUserId(String userName) {
        String userId = scenarioContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
        }
        return userId;
    }

    public void storeUserId(String userName, String userId) {
        scenarioContext.setId(userName, userId);
    }
}
```

---

## Step Definition 範例

```java
// src/test/java/com/wsa/platform/steps/lesson/aggregate_given/LessonProgressGivenSteps.java
package com.wsa.platform.steps.lesson.aggregate_given;

import com.wsa.platform.cucumber.ScenarioContext;
import com.wsa.platform.model.LessonProgress;
import com.wsa.platform.model.ProgressStatus;
import com.wsa.platform.repository.LessonProgressRepository;
import com.wsa.platform.steps.helpers.StatusMapping;
import io.cucumber.java.en.Given;
import org.springframework.beans.factory.annotation.Autowired;

public class LessonProgressGivenSteps {

    @Autowired
    private ScenarioContext scenarioContext;

    @Autowired
    private LessonProgressRepository lessonProgressRepository;

    @Given("用戶 {string} 在課程 {int} 的進度為 {int}%，狀態為 {string}")
    public void userHasLessonProgress(String userName, int lessonId, int progress, String status) {
        String userId = scenarioContext.getId(userName);

        LessonProgress lessonProgress = new LessonProgress();
        lessonProgress.setUserId(Long.parseLong(userId));
        lessonProgress.setLessonId((long) lessonId);
        lessonProgress.setProgress(progress);
        lessonProgress.setStatus(ProgressStatus.valueOf(StatusMapping.mapStatus(status)));

        lessonProgressRepository.save(lessonProgress);
    }
}
```

---

## 檢查清單

- [ ] 一個 Step Pattern 對應一個 Java class
- [ ] 使用 package 分類組織 step definitions
- [ ] `CucumberSpringConfiguration` 已配置 component scanning
- [ ] 類別名稱語意化（如 `LessonProgressGivenSteps`）
- [ ] 共用邏輯已提取到 `helpers/`

---

**文件建立日期**：2025-01-21
**文件版本**：E2E Cucumber BDD Version 1.0
**適用框架**：Java 17 + Spring Boot 3.2 + Cucumber 7.15

---

# Meta 註記清理規範

## 目的

移除開發過程中的臨時註記，保持程式碼乾淨。

---

## 刪除的內容

- `// TODO: [事件風暴部位: ...]`
- `// TODO: 參考 xxx-Handler.md 實作`
- `// [生成參考 Prompt: ...]`
- 其他開發過程中的臨時標記

---

## 保留的內容

- 必要的業務邏輯註解
- 必要的技術註解（如解釋複雜邏輯）
- JavaDoc 文檔註解

---

## 範例

**重構前：**
```java
@Given("用戶 {string} 在課程 {int} 的進度為 {int}%，狀態為 {string}")
public void userHasLessonProgress(String userName, int lessonId, int progress, String status) {
    // TODO: [事件風暴部位: Aggregate - LessonProgress]
    // TODO: 參考 Aggregate-Given-Handler.md 實作

    String userId = scenarioContext.getId(userName);

    // 狀態映射
    Map<String, String> statusMapping = Map.of(...);
    String dbStatus = statusMapping.getOrDefault(status, status);

    LessonProgress progressEntity = new LessonProgress();
    progressEntity.setUserId(Long.parseLong(userId));
    // ...
    lessonProgressRepository.save(progressEntity);
}
```

**重構後：**
```java
@Given("用戶 {string} 在課程 {int} 的進度為 {int}%，狀態為 {string}")
public void userHasLessonProgress(String userName, int lessonId, int progress, String status) {
    String userId = scenarioContext.getId(userName);

    // 狀態映射（中文 → 英文 enum）
    String dbStatus = StatusMapping.mapStatus(status);

    LessonProgress progressEntity = new LessonProgress();
    progressEntity.setUserId(Long.parseLong(userId));
    // ...
    lessonProgressRepository.save(progressEntity);
}
```

---

## 檢查清單

- [ ] 所有 `// TODO: [事件風暴部位: ...]` 已刪除
- [ ] 所有 `// TODO: 參考 xxx-Handler.md 實作` 已刪除
- [ ] 所有 `// [生成參考 Prompt: ...]` 已刪除
- [ ] 必要的業務邏輯註解已保留
- [ ] JavaDoc 文檔註解已保留

---

**文件建立日期**：2025-01-21
**文件版本**：E2E Cucumber BDD Version 1.0
**適用框架**：Java 17 + Spring Boot 3.2 + Cucumber 7.15

---

# 日誌實踐規範

## 目的

本文件定義專案的日誌（Logging）使用規範，確保應用程式在 Docker 容器中運行時具備良好的可觀測性，方便除錯和監控。

---

## 日誌框架

使用 Lombok `@Slf4j` 注解自動注入 SLF4J Logger，避免手動宣告。

```java
// ❌ 手動宣告 Logger
public class OrderService {
    private static final Logger logger = LoggerFactory.getLogger(OrderService.class);
}

// ✅ 使用 Lombok @Slf4j
@Slf4j
@Service
public class OrderService {
    // log 變數自動可用
}
```

---

## 日誌等級使用規則

### ERROR — 系統異常，需要立即關注

用於未預期的錯誤、系統故障。應包含完整 stack trace。

```java
log.error("Unexpected error: {}", ex.getMessage(), ex);
```

### WARN — 預期內的異常狀況

用於認證失敗、權限不足、資料解析失敗等可預期但需留意的情況。

```java
log.warn("Expired JWT token for {} {}", method, uri);
log.warn("Access denied: userId={}, journeyId={}", userId, journeyId);
log.warn("Failed to parse planItems for productId={}: {}", productId, e.getMessage());
```

### INFO — 業務關鍵操作

用於記錄重要的業務事件，如建立訂單、付款、角色授予等。這是 Docker 容器中最主要的觀測依據。

```java
log.info("Order created: orderNumber={}, userId={}, totalPrice={}", orderNumber, userId, totalPrice);
log.info("Payment submitted: orderId={}, amount={}, method={}", orderId, amount, method);
log.info("Role granted: userId={}, journeyId={}, roleType={}", userId, journeyId, roleType);
```

### DEBUG — 詳細執行流程

用於開發和除錯時的詳細資訊，如查詢參數、回傳數量等。在生產環境可透過配置關閉。

```java
log.debug("Fetching order orderNumber={} for userId={}", orderNumber, userId);
log.debug("Product list fetched: statusFilter={}, count={}", statusFilter, count);
```

---

## 各層日誌策略

### Controller 層

記錄每個 API 請求的進入點，包含關鍵參數（userId、資源 ID 等）。

```java
@Slf4j
@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    @PostMapping
    public ResponseEntity<?> createOrder(
            @RequestBody CreateOrderRequest request,
            HttpServletRequest httpRequest) {
        Long userId = CurrentUser.getId(httpRequest);
        log.info("Creating order for userId={}, items={}", userId, request.getItems().size());
        return ResponseEntity.ok(orderService.createOrder(userId, request));
    }
}
```

**原則**：
- 使用 `log.info` 記錄請求進入
- 包含 userId 和關鍵業務參數
- 不記錄敏感資訊（密碼、token 全文等）

### Service 層

記錄業務邏輯的關鍵決策點和結果。

```java
@Slf4j
@Service
public class OrderService {

    public Map<String, Object> createOrder(Long userId, CreateOrderRequest request) {
        log.debug("Creating order for userId={}", userId);

        // ... 業務邏輯 ...

        order = orderRepository.save(order);
        log.info("Order created: orderNumber={}, userId={}, totalPrice={}, items={}",
                order.getOrderNumber(), userId, totalPrice, items.size());

        return response;
    }
}
```

**原則**：
- `log.info` 用於業務操作完成（寫入操作：建立、更新、刪除）
- `log.debug` 用於操作開始和查詢結果
- `log.warn` 用於資料解析失敗等可恢復的異常

### Security 層（Filter）

記錄每個 HTTP 請求和認證結果。

```java
@Slf4j
@Component
public class JwtTokenFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(...) {
        log.info(">>> {} {}", request.getMethod(), request.getRequestURI());

        // 認證成功
        log.debug("Authenticated userId={} for {} {}", userId, method, uri);

        // 認證失敗
        log.warn("Expired JWT token for {} {}", method, uri);
        log.warn("Invalid JWT token for {} {}: {}", method, uri, e.getMessage());
    }
}
```

### 全域例外處理

依據 HTTP 狀態碼使用不同日誌等級。

```java
@Slf4j
@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<?> handleResponseStatusException(ResponseStatusException ex) {
        if (ex.getStatusCode().is5xxServerError()) {
            log.error("Server error [{}]: {}", ex.getStatusCode(), reason, ex);
        } else if (ex.getStatusCode() == HttpStatus.FORBIDDEN) {
            log.warn("Auth error [{}]: {}", ex.getStatusCode(), reason);
        } else {
            log.info("Client error [{}]: {}", ex.getStatusCode(), reason);
        }
        // ...
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<?> handleGenericException(Exception ex) {
        log.error("Unexpected error: {}", ex.getMessage(), ex);
        // ...
    }
}
```

---

## 日誌格式

使用結構化的 key=value 格式，方便 Docker 容器中用 `grep` 或日誌工具搜尋。

```java
// ❌ 不易搜尋
log.info("使用者 " + userId + " 建立了訂單 " + orderNumber);

// ✅ 結構化 key=value
log.info("Order created: orderNumber={}, userId={}, totalPrice={}", orderNumber, userId, totalPrice);
```

**原則**：
- 使用 SLF4J 佔位符 `{}`，不要用字串拼接
- 使用 `key=value` 格式記錄參數
- 在訊息前加上簡短的事件描述（如 `Order created:`、`Payment submitted:`）

---

## application.yml 配置

```yaml
logging:
  level:
    com.wsa.platform: DEBUG
    org.springframework.web: INFO
    org.hibernate.SQL: DEBUG
    org.hibernate.type.descriptor.sql.BasicBinder: TRACE
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n"
```

**說明**：
- `com.wsa.platform: DEBUG`：應用程式碼顯示 DEBUG 以上
- `org.hibernate.SQL: DEBUG`：顯示 SQL 語句
- `org.hibernate.type.descriptor.sql.BasicBinder: TRACE`：顯示 SQL 參數綁定
- console pattern 包含時間戳，方便在 Docker logs 中追蹤

---

## 禁止事項

- ❌ 不要記錄敏感資訊（密碼、JWT token 全文、信用卡號）
- ❌ 不要在迴圈中使用 `log.info`（改用 `log.debug` 或在迴圈外記錄彙總）
- ❌ 不要用 `System.out.println` 或 `e.printStackTrace()`
- ❌ 不要用字串拼接（`"msg " + var`），使用佔位符（`"msg {}", var`）

---

## 檢查清單

- [ ] 所有 Controller、Service、Security 類別加上 `@Slf4j`
- [ ] Controller 層每個端點記錄請求進入（`log.info`）
- [ ] Service 層寫入操作完成時記錄（`log.info`）
- [ ] Service 層查詢操作記錄結果數量（`log.debug`）
- [ ] 認證失敗記錄警告（`log.warn`）
- [ ] 未預期錯誤記錄完整 stack trace（`log.error` + exception 物件）
- [ ] 使用 key=value 格式和 SLF4J 佔位符
- [ ] 不記錄敏感資訊
- [ ] application.yml 配置適當的日誌等級

---

**文件建立日期**：2026-01-26
**文件版本**：E2E Cucumber BDD Version 1.0
**適用框架**：Java 17 + Spring Boot 3.2 + Lombok

---

# 程式架構規範

## 目的

本文件定義專案的程式碼組織結構、職責分層和檔案擺放規則，適用於所有程式開發階段（紅燈、綠燈、重構）。

---

## 檔案組織結構

### 應用程式程式碼目錄結構（範例）

所有 **Domain Specific** 的程式碼都應該放在對應的 package 中：

```
src/main/java/com/wsa/platform/
├── api/                        # API Controllers
│   ├── OrderController.java
│   └── ProductController.java
├── service/                    # Business Logic Services
│   ├── OrderService.java
│   └── InventoryService.java
├── repository/                 # Data Access Layer (Spring Data JPA)
│   ├── OrderRepository.java
│   └── ProductRepository.java
├── model/                      # JPA Entity Models
│   ├── Order.java
│   └── Product.java
├── dto/                        # Request/Response DTOs
│   ├── CreateOrderRequest.java
│   └── OrderResponse.java
├── security/                   # 認證相關
│   ├── JwtTokenFilter.java
│   └── CurrentUser.java
└── Application.java            # Spring Boot main class
```

---

## 分層架構（由外到內）

### Layer 1: Controller / API Endpoints

**職責**：處理 HTTP Request/Response

**負責的事**：
- 定義路由（URL path）
- 解析 HTTP Request（headers, body, query params）
- 呼叫 Service 執行業務邏輯
- 構建 HTTP Response（status code, body）
- 處理認證（驗證 JWT token）

**不負責的事**：
- ❌ 業務邏輯（交給 Service）
- ❌ 資料存取（交給 Repository）

**檔案位置**：`com.wsa.platform.api`

**範例**：
```java
// com/wsa/platform/api/OrderController.java
@RestController
@RequestMapping("/api/orders")
public class OrderController {

    @Autowired
    private OrderService orderService;

    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(
            HttpServletRequest request,
            @RequestBody CreateOrderRequest dto) {
        // 從 request 取得 user ID
        Long userId = CurrentUser.getId(request);

        // 呼叫 service（業務邏輯在這裡）
        Order order = orderService.createOrder(userId, dto.getProductId(), dto.getQuantity());

        // 返回 response
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(new OrderResponse(order.getId(), "created"));
    }
}
```

### Layer 2: Service

**職責**：業務邏輯和規則

**負責的事**：
- 驗證業務規則
- 執行業務流程
- 協調 Repository 讀寫資料
- 拋出業務異常（如資源不存在、狀態錯誤）

**必須支援依賴注入**：
- 使用 `@Autowired` 或建構子注入 Repository
- 讓測試和生產環境可以使用不同的 Repository

**檔案位置**：`com.wsa.platform.service`

**範例**：
```java
// com/wsa/platform/service/OrderService.java
@Service
public class OrderService {

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private ProductRepository productRepository;

    public Order createOrder(Long userId, Long productId, int quantity) {
        // 業務規則：檢查商品是否存在
        Product product = productRepository.findById(productId)
                .orElseThrow(() -> new ProductNotFoundException());

        // 業務規則：檢查庫存是否足夠
        if (product.getStock() < quantity) {
            throw new InsufficientStockException();
        }

        // 業務邏輯：創建訂單
        Order order = new Order();
        order.setUserId(userId);
        order.setProductId(productId);
        order.setQuantity(quantity);
        orderRepository.save(order);

        // 業務邏輯：扣減庫存
        product.setStock(product.getStock() - quantity);
        productRepository.save(product);

        return order;
    }
}
```

### Layer 3: Repository

**職責**：資料存取

**負責的事**：
- 使用 Spring Data JPA 操作真實 PostgreSQL
- 執行 CRUD 操作
- 封裝資料庫查詢邏輯

**檔案位置**：`com.wsa.platform.repository`

**範例**：
```java
// com/wsa/platform/repository/OrderRepository.java
@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {

    List<Order> findByUserId(Long userId);

    Optional<Order> findByIdAndUserId(Long id, Long userId);
}
```

---

## 依賴注入原則

**讓測試環境和生產環境使用同一套程式碼，但可以切換不同的 Repository。**

### Spring Boot 自動注入
```java
// Service 使用 @Autowired 注入 Repository
@Service
public class OrderService {
    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private ProductRepository productRepository;
}
```

### 測試環境
```java
// E2E 測試透過 Spring Boot Test 自動配置
// 使用 Testcontainers PostgreSQL
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
public class CucumberSpringConfiguration {
    // Spring 自動注入真實的 Repository（連接 Testcontainers DB）
}
```

**關鍵**：Service 不需要知道 Repository 是連到哪個資料庫，這讓測試和生產可以無縫切換。

---

## 架構檢查清單

在完成程式開發時，確保符合以下條件：

- ✅ Controllers 在 `com.wsa.platform.api` (如 `OrderController.java`)
- ✅ Services 在 `com.wsa.platform.service` (如 `OrderService.java`)
- ✅ Repositories 在 `com.wsa.platform.repository` (如 `OrderRepository.java`)
- ✅ Models 在 `com.wsa.platform.model` (如 `Order.java`)
- ✅ DTOs 在 `com.wsa.platform.dto` (如 `CreateOrderRequest.java`)
- ✅ Service 使用 `@Autowired` 或建構子注入
- ✅ 每層只負責自己的職責

---

## 常見錯誤

### ❌ 錯誤 1：業務邏輯寫在 Controller

```java
// ❌ 錯誤
@PostMapping("/api/orders")
public ResponseEntity<?> createOrder(@RequestBody CreateOrderRequest request) {
    Product product = productRepository.findById(request.getProductId()).get();
    if (product.getStock() < request.getQuantity()) {  // 業務邏輯不應在 Controller
        throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "庫存不足");
    }
    // ...
}
```

```java
// ✅ 正確
@PostMapping("/api/orders")
public ResponseEntity<?> createOrder(@RequestBody CreateOrderRequest request) {
    Order order = orderService.createOrder(...);  // 業務邏輯在 Service
    return ResponseEntity.ok(order);
}
```

### ❌ 錯誤 2：Service 直接使用 EntityManager

```java
// ❌ 錯誤
@Service
public class OrderService {
    @PersistenceContext
    private EntityManager em;

    public void createOrder() {
        em.createQuery("SELECT o FROM Order o").getResultList();  // 不應直接操作
    }
}
```

```java
// ✅ 正確
@Service
public class OrderService {
    @Autowired
    private OrderRepository orderRepository;

    public void createOrder() {
        orderRepository.findAll();  // 透過 Repository
    }
}
```

---

**文件建立日期**：2025-01-21
**文件版本**：E2E Cucumber BDD Version 1.0
**適用框架**：Java 17 + Spring Boot 3.2 + Cucumber 7.15 + JPA

---

# 程式碼品質規範

## 目的

提升程式碼可讀性、可維護性，減少重複和複雜度。

---

## Early Return 原則

減少巢狀，提升可讀性。

```java
// ❌ 深層巢狀
public void process(Data data) {
    if (data != null) {
        if (data.isValid()) {
            if (data.hasPermission()) {
                processData(data);
            } else {
                throw new PermissionException();
            }
        } else {
            throw new ValidationException();
        }
    } else {
        throw new DataException();
    }
}

// ✅ Early return
public void process(Data data) {
    if (data == null) {
        throw new DataException();
    }
    if (!data.isValid()) {
        throw new ValidationException();
    }
    if (!data.hasPermission()) {
        throw new PermissionException();
    }

    processData(data);
}
```

---

## 靜態屬性優化

重複使用的資料提升為類別常數，減少記憶體消耗。

```java
// ❌ 每次調用都創建
public class Service {
    public String process(String status) {
        Map<String, String> mapping = Map.of(
            "A", "狀態A",
            "B", "狀態B"
        );  // 每次都創建
        return mapping.get(status);
    }
}

// ✅ 類別靜態常數
public class Service {
    private static final Map<String, String> STATUS_MAPPING = Map.of(
        "A", "狀態A",
        "B", "狀態B"
    );  // 只創建一次

    public String process(String status) {
        return STATUS_MAPPING.get(status);
    }
}
```

---

## 命名清晰化

變數和方法名稱應清楚表達其用途。

```java
// ❌ 不清楚的命名
public String process(Map<String, Object> data) {
    Object result = data.get("id");
    return result.toString();
}

// ✅ 清晰的命名
public String extractUserIdFromContext(Map<String, Object> contextData) {
    Object userId = contextData.get("user_id");
    return userId.toString();
}
```

---

## DRY 原則（Don't Repeat Yourself）

消除重複邏輯，提取共用方法。

```java
// ❌ 重複的驗證邏輯
public void updateProgress(Long userId, ...) {
    Subscription subscription = subscriptionRepo.findByUserId(userId)
            .orElseThrow(() -> new SubscriptionNotFoundException());
    // ...
}

public void submitAssignment(Long userId, ...) {
    Subscription subscription = subscriptionRepo.findByUserId(userId)
            .orElseThrow(() -> new SubscriptionNotFoundException());
    // ...
}

// ✅ 提取共用方法
private Subscription validateSubscription(Long userId) {
    return subscriptionRepo.findByUserId(userId)
            .orElseThrow(() -> new SubscriptionNotFoundException());
}

public void updateProgress(Long userId, ...) {
    Subscription subscription = validateSubscription(userId);
    // ...
}

public void submitAssignment(Long userId, ...) {
    Subscription subscription = validateSubscription(userId);
    // ...
}
```

---

## Optional 正確使用

避免 NullPointerException，使用 Optional 安全地處理可能為空的值。

```java
// ❌ 直接 .get() 可能 NPE
public Order getOrder(Long orderId) {
    return orderRepository.findById(orderId).get();  // 危險！
}

// ✅ 使用 orElseThrow
public Order getOrder(Long orderId) {
    return orderRepository.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));
}

// ✅ 或使用 orElse 提供預設值
public Order getOrderOrDefault(Long orderId) {
    return orderRepository.findById(orderId)
            .orElse(new Order());
}
```

---

## 檢查清單

- [ ] 使用 Early Return 減少巢狀
- [ ] 重複使用的資料提升為類別常數
- [ ] 變數和方法名稱清晰表達用途
- [ ] 消除重複邏輯，提取共用方法
- [ ] 使用 Optional 安全處理可能為空的值

---

**文件建立日期**：2025-01-21
**文件版本**：E2E Cucumber BDD Version 1.0
**適用框架**：Java 17 + Spring Boot 3.2

---

