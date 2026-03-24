---
name: aibdd.auto.java.e2e.handlers.aggregate-then
description: 當在 .isa.feature 這類 ISA Gherkin 測試中驗證「資料庫中應存在某實體資料」，務必參考此規範。
user-invocable: false
---

# Aggregate-Then-Handler (E2E Cucumber Version)

## Trigger
Then 語句驗證**Aggregate 的屬性狀態**（從資料庫查詢）

**識別規則**：
- 驗證實體的屬性值（而非 API 回傳值）
- 描述「某個東西的某個屬性應該是某個值」
- 常見句型（非窮舉）：「在...的...應為」「的...應為」「應包含」

**通用判斷**：如果 Then 是驗證 Command 操作後的資料狀態（需要從資料庫查詢），就使用此 Handler

## Task
使用 Repository 從資料庫查詢 Aggregate → Assert 屬性值

## E2E 特色
- 使用 Spring Data JPA Repository 從真實 PostgreSQL 查詢
- 根據 Gherkin 明確提到的欄位進行查詢
- 驗證 Aggregate 的狀態（而非 API response）
- 使用 @Autowired 注入 Repository

---

## Steps

1. 使用 @Autowired 注入 Repository
2. 識別 Aggregate 名稱
3. 從 Gherkin 提取查詢條件（通常是複合主鍵）
4. 使用 Repository 查詢 Aggregate
5. 使用 AssertJ 或 JUnit Assert 驗證屬性值

---

## Pattern Examples (Java Cucumber)

### 驗證單一 Aggregate

```gherkin
And 用戶 "Alice" 的購物車中商品 "PROD-001" 的數量應為 2
```

```java
package com.wsa.platform.steps.aggregate_then;

import com.wsa.platform.model.CartItem;
import com.wsa.platform.repository.CartItemRepository;
import com.wsa.platform.steps.ScenarioContext;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;

import static org.assertj.core.api.Assertions.assertThat;

public class CartItemThenSteps {

    @Autowired
    private CartItemRepository cartItemRepository;

    @Autowired
    private ScenarioContext testContext;

    @Then("用戶 {string} 的購物車中商品 {string} 的數量應為 {int}")
    public void 用戶的購物車中商品的數量應為(String userName, String productId, int quantity) {
        // 取得用戶 ID
        String userId = testContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
        }

        // 使用 Repository 查詢 Aggregate
        CartItem cartItem = cartItemRepository
                .findByUserIdAndProductId(userId, productId)
                .orElse(null);

        // Assert 屬性值
        assertThat(cartItem)
                .as("找不到購物車項目")
                .isNotNull();
        assertThat(cartItem.getQuantity())
                .as("預期數量 %d，實際 %d", quantity, cartItem.getQuantity())
                .isEqualTo(quantity);
    }
}
```

### 驗證多個屬性

```gherkin
And 用戶 "Alice" 在課程 1 的進度應為 80%，狀態應為 "進行中"
```

```java
package com.wsa.platform.steps.aggregate_then;

import com.wsa.platform.model.LessonProgress;
import com.wsa.platform.model.ProgressStatus;
import com.wsa.platform.repository.LessonProgressRepository;
import com.wsa.platform.steps.ScenarioContext;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;

import static org.assertj.core.api.Assertions.assertThat;

public class LessonProgressThenSteps {

    @Autowired
    private LessonProgressRepository lessonProgressRepository;

    @Autowired
    private ScenarioContext testContext;

    @Then("用戶 {string} 在課程 {int} 的進度應為 {int}%，狀態應為 {string}")
    public void 用戶在課程的進度應為狀態應為(String userName, int lessonId, int progress, String status) {
        String userId = testContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
        }

        // 狀態映射（中文 → enum）
        ProgressStatus expectedStatus = mapStatus(status);

        // 查詢 Aggregate
        LessonProgress progressEntity = lessonProgressRepository
                .findByUserIdAndLessonId(userId, lessonId)
                .orElse(null);

        // Assert 多個屬性
        assertThat(progressEntity)
                .as("找不到課程進度")
                .isNotNull();
        assertThat(progressEntity.getProgress())
                .as("預期進度 %d%%，實際 %d%%", progress, progressEntity.getProgress())
                .isEqualTo(progress);
        assertThat(progressEntity.getStatus())
                .as("預期狀態 %s，實際 %s", expectedStatus, progressEntity.getStatus())
                .isEqualTo(expectedStatus);
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

### 驗證 Aggregate 存在

```gherkin
And 訂單 "ORDER-123" 應存在
```

```java
package com.wsa.platform.steps.aggregate_then;

import com.wsa.platform.model.Order;
import com.wsa.platform.repository.OrderRepository;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;

import static org.assertj.core.api.Assertions.assertThat;

public class OrderExistsThenSteps {

    @Autowired
    private OrderRepository orderRepository;

    @Then("訂單 {string} 應存在")
    public void 訂單應存在(String orderId) {
        Order order = orderRepository.findById(orderId).orElse(null);
        assertThat(order)
                .as("訂單 %s 應該存在但找不到", orderId)
                .isNotNull();
    }
}
```

### 驗證 Aggregate 不存在

```gherkin
And 購物車中應不存在商品 "PROD-001"
```

```java
package com.wsa.platform.steps.aggregate_then;

import com.wsa.platform.model.CartItem;
import com.wsa.platform.repository.CartItemRepository;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;

public class CartItemNotExistsThenSteps {

    @Autowired
    private CartItemRepository cartItemRepository;

    @Then("購物車中應不存在商品 {string}")
    public void 購物車中應不存在商品(String productId) {
        Optional<CartItem> cartItem = cartItemRepository.findByProductId(productId);
        assertThat(cartItem)
                .as("商品 %s 不應該存在但找到了", productId)
                .isEmpty();
    }
}
```

### 驗證進度（常見情境）

```gherkin
And 用戶 "Alice" 在課程 1 的進度應為 80%
```

```java
package com.wsa.platform.steps.aggregate_then;

import com.wsa.platform.model.LessonProgress;
import com.wsa.platform.repository.LessonProgressRepository;
import com.wsa.platform.steps.ScenarioContext;
import io.cucumber.java.en.Then;
import org.springframework.beans.factory.annotation.Autowired;

import static org.assertj.core.api.Assertions.assertThat;

public class LessonProgressOnlyThenSteps {

    @Autowired
    private LessonProgressRepository lessonProgressRepository;

    @Autowired
    private ScenarioContext testContext;

    @Then("用戶 {string} 在課程 {int} 的進度應為 {int}%")
    public void 用戶在課程的進度應為(String userName, int lessonId, int progress) {
        String userId = testContext.getId(userName);
        if (userId == null) {
            throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
        }

        // 查詢並驗證
        LessonProgress progressEntity = lessonProgressRepository
                .findByUserIdAndLessonId(userId, lessonId)
                .orElse(null);

        assertThat(progressEntity)
                .as("找不到課程進度")
                .isNotNull();
        assertThat(progressEntity.getProgress())
                .as("預期進度 %d%%，實際 %d%%", progress, progressEntity.getProgress())
                .isEqualTo(progress);
    }
}
```

---

## Query Strategy

### 根據 Gherkin 明確提到的欄位查詢

**規則**：只使用 Gherkin 中明確提到的欄位來查詢 Aggregate

**範例 1：複合主鍵查詢**

```gherkin
And 用戶 "Alice" 的購物車中商品 "PROD-001" 的數量應為 2
```

從 Gherkin 提取：
- 用戶: "Alice" → userId（從 ScenarioContext 取得）
- 商品: "PROD-001" → productId

查詢方法：
```java
cartItemRepository.findByUserIdAndProductId(userId, "PROD-001")
```

**範例 2：單一主鍵查詢**

```gherkin
And 訂單 "ORDER-123" 的狀態應為 "已付款"
```

從 Gherkin 提取：
- 訂單: "ORDER-123" → orderId

查詢方法：
```java
orderRepository.findById("ORDER-123")
```

---

## Repository Query Methods

### 命名規則

Repository 的查詢方法命名應該清晰表達查詢條件：

| Gherkin 查詢條件 | Repository 方法 |
|----------------|----------------|
| 用戶 "Alice" 在課程 1 | findByUserIdAndLessonId(userId, lessonId) |
| 訂單 "ORDER-123" | findById(orderId) |
| 商品 "PROD-001" | findByProductId(productId) |
| 用戶 "Alice" 的所有訂單 | findByUserId(userId) |

### Repository 介面範例

```java
// com/wsa/platform/repository/LessonProgressRepository.java

package com.wsa.platform.repository;

import com.wsa.platform.model.LessonProgress;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface LessonProgressRepository extends JpaRepository<LessonProgress, Integer> {

    Optional<LessonProgress> findByUserIdAndLessonId(String userId, Integer lessonId);

    List<LessonProgress> findByUserId(String userId);
}
```

---

## State Mapping

**目的**: 將 Gherkin 中的中文業務術語映射到 Java enum 值

| 中文範例 | Enum 範例 | 適用情境 |
|---------|----------|---------|
| 進行中 | IN_PROGRESS | 進度、狀態 |
| 已完成 | COMPLETED | 進度、狀態 |
| 未開始 | NOT_STARTED | 進度、狀態 |
| 已交付 | DELIVERED | 課程狀態 |
| 已付款 | PAID | 訂單、付款 |
| 待付款 | PENDING | 訂單、付款 |

```java
// ✅ 正確：使用 enum
assertThat(progressEntity.getStatus()).isEqualTo(ProgressStatus.IN_PROGRESS);

// ❌ 錯誤：使用中文字串
assertThat(progressEntity.getStatus()).isEqualTo("進行中");
```

---

## Critical Rules

### R1: 使用 Repository 查詢
必須使用 Repository 的查詢方法，不直接使用 EntityManager。

```java
// ✅ 正確：使用 Repository
LessonProgress progressEntity = lessonProgressRepository
        .findByUserIdAndLessonId(userId, lessonId)
        .orElse(null);

// ❌ 錯誤：直接使用 EntityManager
LessonProgress progressEntity = entityManager
        .createQuery("SELECT lp FROM LessonProgress lp WHERE ...")
        .getSingleResult();
```

### R2: 只驗證 Gherkin 提到的欄位
只 assert Gherkin 中明確提到的屬性。

```java
// Gherkin: And 用戶 "Alice" 在課程 1 的進度應為 80%

// ✅ 正確：只驗證 progress
assertThat(progressEntity.getProgress()).isEqualTo(80);

// ❌ 錯誤：驗證額外的欄位
assertThat(progressEntity.getProgress()).isEqualTo(80);
assertThat(progressEntity.getUpdatedAt()).isNotNull();  // Gherkin 沒提到
```

### R3: 中文狀態映射到 enum
```java
// ✅ assertThat(progressEntity.getStatus()).isEqualTo(ProgressStatus.IN_PROGRESS);
// ❌ assertThat(progressEntity.getStatus()).isEqualTo("進行中");
```

### R4: 使用完整的查詢條件
根據 Gherkin 提到的所有條件進行查詢。

```java
// Gherkin: And 用戶 "Alice" 在課程 1 的進度應為 80%

// ✅ 正確：使用完整的查詢條件
lessonProgressRepository.findByUserIdAndLessonId(userId, 1);

// ❌ 錯誤：缺少查詢條件
lessonProgressRepository.findByLessonId(1);  // 沒有指定用戶
```

### R5: 驗證 Aggregate 存在性
如果 Gherkin 要求驗證存在或不存在，要明確檢查。

```java
// Gherkin: And 訂單 "ORDER-123" 應存在

// ✅ 正確：檢查不為 null
Order order = orderRepository.findById("ORDER-123").orElse(null);
assertThat(order).as("訂單應該存在").isNotNull();

// ❌ 錯誤：沒有檢查存在性，直接訪問屬性可能 NPE
Order order = orderRepository.findById("ORDER-123").orElse(null);
assertThat(order.getStatus()).isEqualTo(OrderStatus.PAID);  // 如果 order 是 null 會 NPE
```

### R6: 使用 @Autowired 注入 Repository
必須使用 Spring 的依賴注入。

```java
// ✅ 正確：使用 @Autowired
@Autowired
private LessonProgressRepository lessonProgressRepository;

// ❌ 錯誤：自己創建
LessonProgressRepository repo = new LessonProgressRepository();
```

### R7: 從 ScenarioContext 取得用戶 ID
查詢時使用 ScenarioContext 取得之前儲存的用戶 ID。

```java
// ✅ 正確：從 ScenarioContext 取得
String userId = testContext.getId(userName);
if (userId == null) {
    throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
}

// ❌ 錯誤：直接使用用戶名稱
String userId = userName;  // 可能不是真正的 ID
```

### R8: 從資料庫查詢，不使用 API response
Aggregate-Then-Handler 驗證的是資料庫狀態，不是 API response。

```java
// ✅ 正確：從資料庫查詢
LessonProgress progressEntity = lessonProgressRepository
        .findByUserIdAndLessonId(userId, 1)
        .orElse(null);
assertThat(progressEntity.getProgress()).isEqualTo(80);

// ❌ 錯誤：使用 API response
ResponseEntity<?> response = testContext.getLastResponse();
// 這是 ReadModel-Then-Handler 的工作
```

### R9: 使用 AssertJ 提供清晰的錯誤訊息
使用 `.as()` 提供清晰的 assert 失敗訊息，方便除錯。

```java
// ✅ 正確：清晰的訊息
assertThat(progressEntity.getProgress())
        .as("預期進度 %d%%，實際 %d%%", progress, progressEntity.getProgress())
        .isEqualTo(progress);

// ❌ 錯誤：沒有訊息
assertThat(progressEntity.getProgress()).isEqualTo(progress);
```

---

## 與 ReadModel-Then-Handler 的區別

| 面向 | Aggregate-Then-Handler | ReadModel-Then-Handler |
|------|-------------------|----------------------|
| 驗證對象 | 資料庫中的 Aggregate | API response 的內容 |
| 資料來源 | JPA Repository | testContext.getLastResponse() |
| 使用時機 | Command 操作後驗證狀態 | Query 操作後驗證回傳值 |
| 範例 | And 用戶 "Alice" 在課程 1 的進度應為 80% | And 查詢結果應包含進度 80% |

---

## 驗證列表（List）

如果 Aggregate 是列表（如「用戶的所有訂單」），使用 `findAll*` 方法。

```gherkin
And 用戶 "Alice" 應有 2 個課程進度記錄
```

```java
@Then("用戶 {string} 應有 {int} 個課程進度記錄")
public void 用戶應有N個課程進度記錄(String userName, int count) {
    String userId = testContext.getId(userName);
    if (userId == null) {
        throw new IllegalStateException("找不到用戶 '" + userName + "' 的 ID");
    }

    List<LessonProgress> progressList = lessonProgressRepository.findByUserId(userId);
    assertThat(progressList)
            .as("預期 %d 個記錄，實際 %d 個", count, progressList.size())
            .hasSize(count);
}
```

---

**文件建立日期**：2025-01-20
**文件版本**：E2E Cucumber BDD Version 1.0
**適用框架**：Java 17 + Spring Boot 3.2 + Cucumber 7.15 + JPA + Testcontainers
