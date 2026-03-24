---
name: aibdd.auto.java.e2e.green
description: Java E2E Stage 3：綠燈階段。Trial-and-error 循環讓測試通過，實作後端 API（DTO → Service → Controller → 路由註冊）。可被 /java-e2e 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${JAVA_TEST_FEATURES_DIR}/**/*.feature, ${JAVA_STEPS_DIR}/**/*.java, ${JAVA_MODEL_DIR}/**/*.java
output: ${JAVA_SERVICE_DIR}/**/*.java, ${JAVA_CONTROLLER_DIR}/**/*.java
---

# 角色

TDD 綠燈實作者。在紅燈階段已經寫好 E2E 測試並確認失敗後，進入綠燈階段：

**寫最少的程式碼讓測試通過，實作後端 API，不斷 trial-and-error 直到所有測試變綠。**

---

# 入口條件

## 被 /java-e2e 調用

接收 Feature File 路徑，直接進入 trial-and-error 流程。

## 獨立使用

1. 詢問目標 Feature File 路徑（預設掃描 `${JAVA_TEST_FEATURES_DIR}/*.feature`）
2. 確認目前是紅燈狀態（HTTP 404）
3. 進入 trial-and-error 流程

---

# 核心原則

## 0. 測試驅動開發的鐵律

**必須透過執行自動化測試來驗證實作是否完成，絕不猜測。**

- 每完成一個步驟，立即執行測試
- 無需詢問使用者，直接下達 `mvn clean test` 指令
- 根據測試結果決定下一步行動
- 絕不假設測試會通過
- 絕不詢問「測試通過了嗎？」

## 測試執行策略

1. **開發階段：先跑目標情境的特定測試**
   - 快速驗證當前實作
   - 縮短反饋循環
   - 專注於正在開發的功能

2. **完成階段：執行總回歸測試**
   - 確保沒有破壞既有功能
   - 驗證系統整體穩定性
   - 必須通過所有測試才算完成

**測試指令**：

```bash
# 1. 開發階段：執行特定 Feature 檔案（快速迭代）
mvn clean test -Dtest=RunCucumberTest -Dcucumber.features=${JAVA_TEST_FEATURES_DIR}/xxx.feature

# 2. 開發階段：執行特定 Scenario（最快）
mvn clean test -Dtest=RunCucumberTest -Dcucumber.features=${JAVA_TEST_FEATURES_DIR}/xxx.feature -Dcucumber.filter.name="scenario name"

# 3. 完成階段：執行所有已完成紅燈的測試（總回歸測試）
mvn clean test -Dtest=RunCucumberTest -Dcucumber.filter.tags="not @ignore"
```

**為什麼使用 `not @ignore`？**
- 只執行已完成紅燈實作的 features（已移除 `@ignore` 標籤）
- 避免執行尚未實作的 features 造成混淆
- 確保回歸測試的範圍清晰明確

## 1. 最小增量開發原則

只寫讓測試通過所需的最少程式碼，不要多做。

```java
// 做太多了（測試沒要求）
@PostMapping("/lesson-progress/update-video-progress")
public ResponseEntity<?> updateVideoProgress(@RequestBody UpdateVideoProgressRequest request) {
    validateInventory();      // 沒測試
    sendEmailNotification();  // 沒測試
    logAuditTrail();         // 沒測試
    return updateProgressLogic(request);
}

// 剛好夠（只實作測試要求的）
@PostMapping("/lesson-progress/update-video-progress")
public ResponseEntity<?> updateVideoProgress(@RequestBody UpdateVideoProgressRequest request) {
    return updateProgressLogic(request);
}
```

## 2. Trial-and-Error 流程

**核心流程**：測試 → 看錯誤 → 修正 → 再測試（循環直到通過）

```
開發循環（快速迭代）：
1. 執行特定測試 → mvn clean test -Dcucumber.features=xxx.feature
2. 看錯誤訊息 → 理解失敗原因
3. 寫最少的程式碼修正這個錯誤
4. 再次執行特定測試 → mvn clean test -Dcucumber.features=xxx.feature
5. 還有錯誤？回到步驟 2
6. 特定測試通過？進入完成驗證

完成驗證（回歸測試）：
7. 執行所有已完成紅燈的測試 → mvn clean test -Dcucumber.filter.tags="not @ignore"
8. 所有測試通過？完成綠燈！
9. 有測試失敗？回到步驟 2，修復破壞的測試
```

**重要**：
- 開發時：頻繁執行特定測試（快速反饋，節省時間）
- 完成前：必須執行總回歸測試 `mvn clean test -Dtest=RunCucumberTest -Dcucumber.filter.tags="not @ignore"`（確保沒有破壞既有功能）
- 每次修改後立即執行測試，不要累積多個變更
- 直接執行 mvn clean test 指令，不需要詢問使用者
- 根據實際的測試輸出（HTTP 狀態碼、錯誤訊息）決定下一步
- 不要一次寫完所有程式碼
- 不要假設測試會通過
- 不要只跑特定測試就宣稱完成

---

# 實作流程

按照測試錯誤訊息逐步實作：

**基本流程**：
1. 執行測試 → `mvn clean test -Dtest=RunCucumberTest -Dcucumber.features=${JAVA_TEST_FEATURES_DIR}/xxx.feature`
2. 看錯誤訊息（HTTP 404? 500? 400?）
3. 根據錯誤補充最少的程式碼（DTO → Service → Controller → 路由註冊）
4. 再次執行測試
5. 循環直到特定測試通過
6. 執行總回歸測試 → `mvn clean test -Dtest=RunCucumberTest -Dcucumber.filter.tags="not @ignore"`

**範例執行流程**：
```
開發階段（快速迭代）：
→ mvn clean test -Dcucumber.features=xxx.feature
  FAILED: HTTP 404 Not Found

→ 建立 API endpoint
→ mvn clean test -Dcucumber.features=xxx.feature
  FAILED: HTTP 500 Internal Server Error

→ 修正 Service 邏輯
→ mvn clean test -Dcucumber.features=xxx.feature
  FAILED: HTTP 400 Bad Request (進度不可倒退)

→ 調整業務規則驗證
→ mvn clean test -Dcucumber.features=xxx.feature
  PASSED（特定測試通過）

完成驗證（回歸測試）：
→ mvn clean test -Dcucumber.filter.tags="not @ignore"
  2 features passed, 5 scenarios passed（所有測試通過，真正完成！）
```

---

# 常見錯誤修復

## HTTP 404 Not Found
**原因**：API Endpoint 不存在
**修復**：
1. 在 `${JAVA_CONTROLLER_DIR}/` 中創建 Controller
2. 確保 @RestController 和 @RequestMapping 正確

```java
// ${JAVA_CONTROLLER_DIR}/LessonProgressController.java
package com.wsa.platform.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;

@RestController
@RequestMapping("/api/v1")
public class LessonProgressController {

    @PostMapping("/lesson-progress/update-video-progress")
    public ResponseEntity<?> updateVideoProgress(@RequestBody UpdateVideoProgressRequest request) {
        // TODO: 實作業務邏輯
        return ResponseEntity.ok().build();
    }
}
```

## HTTP 500 Internal Server Error
**原因**：後端程式碼有錯誤
**修復**：
1. 檢查錯誤訊息和 stack trace
2. 修正 Service/Repository 的邏輯

## HTTP 400 Bad Request
**原因**：業務規則驗證失敗
**修復**：
1. 確認業務規則正確實作
2. 調整驗證邏輯

## HTTP 401 Unauthorized
**原因**：JWT Token 驗證失敗
**修復**：
1. 確認 Security 配置正確
2. 確認 JWT 密鑰與測試用的 JwtHelper 一致

---

# 完成條件

## 開發階段
- 執行特定測試 `mvn clean test -Dtest=RunCucumberTest -Dcucumber.features=${JAVA_TEST_FEATURES_DIR}/xxx.feature`
- 確認目標功能測試通過

## 完成驗證（必須）
- **執行總回歸測試 `mvn clean test -Dtest=RunCucumberTest -Dcucumber.filter.tags="not @ignore"`**
- **所有已完成紅燈的測試通過**
- 沒有破壞既有功能
- 程式碼簡單直接

**只有當執行 `mvn clean test -Dtest=RunCucumberTest -Dcucumber.filter.tags="not @ignore"` 顯示所有測試 PASSED 時，才算完成綠燈階段。**

**不需要**：
- 程式碼優雅（留給重構階段）
- 效能優化（留給重構階段）
- 完整錯誤處理（測試沒要求就不做）
- 額外的 API 功能（測試沒要求就不做）
- 詢問使用者「測試通過了嗎？」（直接執行 mvn clean test 確認）
- 只跑特定測試就宣稱完成（必須執行總回歸測試）

---

# 完成判定標準

```
特定測試通過 → 功能開發完成
                |
                v
         執行總回歸測試
                |
                v
  mvn clean test -Dtest=RunCucumberTest -Dcucumber.filter.tags="not @ignore"
                |
                v
   所有已完成紅燈的測試通過
                |
                v
         真正完成綠燈！
```

完成綠燈後，進入重構階段。

---

# 記住

1. **測試驅動你** - 看測試錯誤決定下一步要實作什麼
2. **最小實作** - 只寫通過測試需要的程式碼
3. **Trial-and-Error** - 執行測試 → 看錯誤 → 修正 → 再執行，不斷循環
4. **自動執行測試** - 每次修改後立即執行測試，無需詢問使用者
5. **根據實際結果行動** - 依據 mvn clean test 的輸出決定下一步

**測試執行的黃金原則**：
- 開發時：頻繁執行特定測試 `mvn clean test -Dtest=RunCucumberTest -Dcucumber.features=xxx.feature`（快速迭代）
- 完成前：必須執行總回歸測試 `mvn clean test -Dtest=RunCucumberTest -Dcucumber.filter.tags="not @ignore"`（確保穩定）
- 有疑問？執行測試
- 修改完成？執行測試
- 想確認進度？執行測試
- 不要詢問「測試通過了嗎？」
- 不要假設測試結果
- 不要只跑特定測試就宣稱完成
