---
name: aibdd.auto.java.e2e.handlers.aggregate-given
description: 當在 .isa.feature 這類 ISA Gherkin 測試中進行「資料庫實體建立（for 測試情境的前置系統狀態設立）」，「只能」使用此指令。
user-invocable: false
---

# Aggregate-Given-Handler (E2E Cucumber Version)

## Trigger
Given 語句描述**Aggregate 的存在狀態**，即定義 Aggregate 的屬性值

**識別規則**：
- 語句中包含實體名詞 + 屬性描述
- 描述「某個東西的某個屬性是某個值」
- 常見句型（非窮舉）:「在...的...為」「的...為」「包含」「存在」「有」

**通用判斷**: 如果 Given 是在建立測試的初始資料狀態（而非執行動作），就使用此 Handler

## Task
創建 JPA Entity → 使用 Repository.save() → 儲存 ID 到 ScenarioContext

## E2E 特色
- 使用 JPA Entity（Hibernate ORM）
- 使用 Spring Data JPA Repository
- 寫入真實的 PostgreSQL 資料庫（Testcontainers）
- 將 Aggregate 的自然鍵（natural key）和 ID 存入 ScenarioContext.ids
- 使用 @Autowired 注入 Repository

---

## Steps

1. 使用 @Autowired 注入 Repository
2. 識別 Aggregate 名稱
3. 從 DBML 提取: 屬性、型別、複合 Key、enum
4. 從 Gherkin 提取: Key 值、屬性值
5. 創建 JPA Entity instance
6. 使用 Repository.save() 寫入資料庫
7. 將 ID 儲存到 ScenarioContext.ids（格式: `testContext.putId("{natural_key}", id)`）

---

## Pattern Examples (Java Cucumber)

### 單一 Aggregate

```gherkin
Given 用戶 "Alice" 的購物車中商品 "PROD-001" 的數量為 2
```

```java
package com.wsa.platform.steps.aggregate_given;

import com.wsa.platform.model.CartItem;
import com.wsa.platform.repository.CartItemRepository;
import com.wsa.platform.steps.ScenarioContext;
import io.cucumber.java.en.Given;
import org.springframework.beans.factory.annotation.Autowired;

public class CartItemSteps {

    @Autowired
    private CartItemRepository cartItemRepository;

    @Autowired
    private ScenarioContext testContext;

    @Given("用戶 {string} 的購物車中商品 {string} 的數量為 {int}")
    public void 用戶的購物車中商品的數量為(String userName, String productId, int quantity) {
        // 取得用戶 ID（應該在之前的 Given 中建立）
        String userId = testContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID，請先建立用戶");
        }

        // 創建 Entity
        CartItem cartItem = new CartItem();
        cartItem.setUserId(userId);
        cartItem.setProductId(productId);
        cartItem.setQuantity(quantity);

        // 儲存到資料庫
        cartItemRepository.save(cartItem);
    }
}
```

### 複合主鍵 Aggregate

```gherkin
Given 用戶 "Alice" 在課程 1 的進度為 70%，狀態為 "進行中"
```

```java
package com.wsa.platform.steps.aggregate_given;

import com.wsa.platform.model.LessonProgress;
import com.wsa.platform.model.ProgressStatus;
import com.wsa.platform.repository.LessonProgressRepository;
import com.wsa.platform.steps.ScenarioContext;
import io.cucumber.java.en.Given;
import org.springframework.beans.factory.annotation.Autowired;

public class LessonProgressSteps {

    @Autowired
    private LessonProgressRepository lessonProgressRepository;

    @Autowired
    private ScenarioContext testContext;

    @Given("用戶 {string} 在課程 {int} 的進度為 {int}%，狀態為 {string}")
    public void 用戶在課程的進度為狀態為(String userName, int lessonId, int progress, String status) {
        // 取得用戶 ID
        String userId = testContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
        }

        // 狀態映射（中文 → enum）
        ProgressStatus dbStatus = mapStatus(status);

        // 創建 Entity
        LessonProgress progressEntity = new LessonProgress();
        progressEntity.setUserId(userId);
        progressEntity.setLessonId(lessonId);
        progressEntity.setProgress(progress);
        progressEntity.setStatus(dbStatus);

        // 儲存到資料庫
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

### 建立用戶（DataTable）

```gherkin
Given 系統中有以下用戶：
  | userId | name  | email           |
  | 1      | Alice | alice@test.com  |
  | 2      | Bob   | bob@test.com    |
```

```java
package com.wsa.platform.steps.aggregate_given;

import com.wsa.platform.model.User;
import com.wsa.platform.repository.UserRepository;
import com.wsa.platform.steps.ScenarioContext;
import io.cucumber.datatable.DataTable;
import io.cucumber.java.en.Given;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.List;
import java.util.Map;

public class UserSteps {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private ScenarioContext testContext;

    @Given("系統中有以下用戶：")
    public void 系統中有以下用戶(DataTable dataTable) {
        List<Map<String, String>> rows = dataTable.asMaps();

        for (Map<String, String> row : rows) {
            User user = new User();
            user.setId(row.get("userId"));
            user.setName(row.get("name"));
            user.setEmail(row.get("email"));

            userRepository.save(user);

            // 儲存 ID 到 ScenarioContext（用名稱作為 key）
            testContext.putId(row.get("name"), user.getId());
        }
    }
}
```

---

## JPA Entity Pattern

### Entity 結構

```java
// com/wsa/platform/model/CartItem.java

package com.wsa.platform.model;

import jakarta.persistence.*;

@Entity
@Table(name = "cart_items")
public class CartItem {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "user_id", nullable = false)
    private String userId;

    @Column(name = "product_id", nullable = false)
    private String productId;

    @Column(nullable = false)
    private Integer quantity;

    // Getters and Setters
    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }

    public Integer getQuantity() { return quantity; }
    public void setQuantity(Integer quantity) { this.quantity = quantity; }
}
```

### Repository 結構

```java
// com/wsa/platform/repository/CartItemRepository.java

package com.wsa.platform.repository;

import com.wsa.platform.model.CartItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface CartItemRepository extends JpaRepository<CartItem, Integer> {
    Optional<CartItem> findByUserIdAndProductId(String userId, String productId);
}
```

---

## Key Patterns

**目的**: 從 Gherkin 的關係詞推斷 DBML 中的複合主鍵結構

**規則**: Gherkin 中的關係詞通常對應實體間的多對多或一對多關係

| 關係詞 | Gherkin 範例 | 複合 Key |
|-------|------------|---------|
| 在 | 用戶 "Alice" 在課程 1 | (user_id, lesson_id) |
| 對 | 用戶 "Alice" 對訂單 "ORDER-123" | (user_id, order_id) |
| 與 | 用戶 "Alice" 與用戶 "Bob" | (user_id_a, user_id_b) |
| 於 | 商品 "MacBook" 於商店 "台北店" | (product_id, store_id) |
| 中...在 | 訂單中商品在倉庫 | (order_id, product_id, warehouse_id) |

---

## State Mapping

**目的**: 將 Gherkin 中的中文業務術語映射到 Java enum 值

**規則**:
1. 查詢 DBML 中對應欄位的 `note` 定義
2. 根據語意將 Gherkin 的中文描述映射到 enum 值

| 中文範例 | Enum 範例 | 適用情境 |
|---------|----------|---------|
| 進行中 | IN_PROGRESS | 進度、狀態 |
| 已完成 | COMPLETED | 進度、狀態 |
| 未開始 | NOT_STARTED | 進度、狀態 |
| 已付款 | PAID | 訂單、付款 |
| 待付款 | PENDING | 訂單、付款 |
| 上架中 | ACTIVE | 商品、服務 |

---

## ScenarioContext ID Storage（Cucumber 版本）

### 儲存規則

將 Aggregate 的自然鍵（natural key）儲存到 `ScenarioContext`，格式：`testContext.putId("{natural_key}", id)`

**為什麼要這樣？**
- Command/Query Handler 需要知道哪個用戶在執行操作
- 自然鍵（如 "Alice"）更易讀
- 在 E2E 測試中，需要追蹤建立的實體 ID

### 範例

```java
// 儲存用戶 ID
testContext.putId("Alice", user.getId());
testContext.putId("Bob", user.getId());

// 取得用戶 ID
String userId = testContext.getId("Alice");
```

### 使用時機

在 Command-Handler 和 Query-Handler 中取用：

```java
// Command-Handler 中使用
String userId = testContext.getId("Alice");
String token = jwtHelper.generateToken(userId);
ResponseEntity<?> response = testRestTemplate.exchange(...);
```

---

## Critical Rules

### R1: 必須查詢 DBML
在實作 Aggregate 的時候不能憑空猜測屬性名稱和型別。必須從 DBML 讀取完整的 Aggregate 定義。

### R2: 使用 JPA Entity
必須使用 JPA Entity（@Entity 標註），不能使用 Map 或普通 POJO。

```java
// ✅ 正確：使用 JPA Entity
CartItem cartItem = new CartItem();
cartItem.setUserId("Alice");
cartItem.setProductId("PROD-001");

// ❌ 錯誤：使用 Map
Map<String, Object> cartItem = Map.of("userId", "Alice", "productId", "PROD-001");
```

### R3: 使用 Spring Data JPA Repository
必須透過 Repository 來操作資料庫，使用 @Autowired 注入。

```java
// ✅ 正確：使用 Repository
@Autowired
private CartItemRepository cartItemRepository;

cartItemRepository.save(cartItem);

// ❌ 錯誤：直接使用 EntityManager
entityManager.persist(cartItem);
```

### R4: 中文狀態映射到 enum
```java
// ✅ progressEntity.setStatus(ProgressStatus.IN_PROGRESS);
// ❌ progressEntity.setStatus("進行中");
```

### R5: 提供完整的複合 Key
```java
// ✅ cartItem.setUserId("Alice"); cartItem.setProductId("PROD-001");
// ❌ cartItem.setProductId("PROD-001");  // 缺少 userId
```

### R6: 儲存 ID 到 ScenarioContext
每個 Given 中創建的 Aggregate 都要將其 natural key 儲存到 ScenarioContext。

```java
// ✅ 正確：儲存到 ScenarioContext
testContext.putId("Alice", user.getId());

// ❌ 錯誤：沒有儲存
userRepository.save(user);
```

### R7: 使用 @Autowired 注入依賴
必須使用 Spring 的依賴注入，不自己創建 Repository。

```java
// ✅ 正確：使用 @Autowired
@Autowired
private LessonProgressRepository repository;

// ❌ 錯誤：自己創建
LessonProgressRepository repository = new LessonProgressRepository();
```

### R8: 檢查依賴的 ID 是否存在
在建立有外鍵關係的 Aggregate 時，先檢查依賴的 ID 是否存在於 ScenarioContext。

```java
// ✅ 正確：檢查依賴是否存在
String userId = testContext.getId(userName);
if (userId == null) {
    throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID，請先建立用戶");
}
```

---

## File Organization

### 建議的檔案結構

```
src/main/java/com/wsa/platform/
├── model/                       # JPA Entities
│   ├── CartItem.java
│   └── LessonProgress.java
└── repository/                  # Spring Data JPA Repositories
    ├── CartItemRepository.java
    └── LessonProgressRepository.java

src/test/java/com/wsa/platform/
├── CucumberSpringConfiguration.java   # Cucumber + Spring 整合
├── ScenarioContext.java                   # 測試狀態管理（@ScenarioScope）
└── steps/
    └── aggregate_given/               # Aggregate Given Step Definitions
        ├── CartItemSteps.java
        └── LessonProgressSteps.java
```

---

**文件建立日期**：2025-01-20
**文件版本**：E2E Cucumber BDD Version 1.0
**適用框架**：Java 17 + Spring Boot 3.2 + Cucumber 7.15 + JPA + Testcontainers
