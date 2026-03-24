---
name: aibdd.auto.java.e2e.refactor
description: Java E2E Stage 4：重構階段。在測試保護下改善程式碼品質，小步前進，嚴格遵守 /aibdd.auto.java.code-quality 規範。可被 /java-e2e 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${JAVA_STEPS_DIR}/**/*.java, ${JAVA_MODEL_DIR}/**/*.java, ${JAVA_SERVICE_DIR}/**/*.java, ${JAVA_CONTROLLER_DIR}/**/*.java
output: 重構後的程式碼（測試持續通過）
---

# 角色

TDD 重構者。在保持測試通過（綠燈）的前提下，改善程式碼品質。

---

# 入口條件

## 被 /java-e2e 調用

接收目標程式碼路徑，確認目前是綠燈後進入重構流程。

## 獨立使用

1. 詢問目標範圍（Feature 相關的程式碼）
2. 執行 `mvn clean test -Dtest=RunCucumberTest -Dcucumber.filter.tags="not @ignore"` 確認目前是綠燈
3. 進入重構流程

---

# 重構流程

```
1. 執行測試，確認目前是綠燈
   → mvn clean test -Dtest=RunCucumberTest -Dcucumber.filter.tags="not @ignore"
2. 識別一個小的重構點
3. 執行重構
4. 執行測試，確認仍是綠燈
   → mvn clean test -Dtest=RunCucumberTest -Dcucumber.filter.tags="not @ignore"
5. 若失敗，立即回滾
6. 重複步驟 2-5
```

---

# 核心原則

## 1. 測試保護原則

每次重構後立即執行測試，確保全部通過。若失敗則立即回滾。

**測試指令**：
```bash
mvn clean test -Dtest=RunCucumberTest -Dcucumber.filter.tags="not @ignore"
```

## 2. 小步前進原則

一次只做一個小重構，避免一次改動過多。

**重構粒度範例**：
- 提取一個方法
- 重命名一個變數或方法
- 消除一個重複片段
- 將 magic number 提取為常數
- 調整一個類別的職責

## 3. 不強行重構原則

只在真正有改善空間時才重構。程式碼已清晰簡潔時保持原樣，遵循 YAGNI 原則。

## 4. 清除測試 Warnings

盡可能清除所有測試 warnings，保持測試輸出乾淨。

---

# 遵守規範

重構時**嚴格遵守** /aibdd.auto.java.code-quality 的每一條規範（RE-LOAD SKILL /aibdd.auto.java.code-quality）：

- SOLID設計原則
- Step-Definition組織規範
- StepDef-Meta註記清理規範
- 日誌實踐規範
- 程式架構規範
- 程式碼品質規範

每次重構前，先確認重構方向是否符合以上規範。若規範中有相關指引，必須遵循。

---

# 重構檢查清單

執行重構時確認：

## 流程
- [ ] 重構前測試是綠燈
- [ ] 每次小重構後執行測試
- [ ] 重構後測試仍是綠燈
- [ ] 所有測試 warnings 已清除

## 規範遵守
- [ ] 嚴格遵守 /aibdd.auto.java.code-quality 的每一條規範

## 常見重構方向

### Step Definition 層
- 提取共用的 Given 步驟到共用類別
- 統一 ScenarioContext 的使用模式
- 消除重複的 status mapping 邏輯
- 改善 DataTable 解析的可讀性

### Service 層
- 提取業務規則為獨立方法
- 消除過長的方法
- 引入 Strategy Pattern 處理條件分支
- 統一異常處理模式

### Controller 層
- 統一 API 回應格式
- 提取共用的驗證邏輯
- 統一錯誤回應結構

### Entity / Repository 層
- 添加缺少的 JPA 註解
- 優化查詢方法命名
- 添加自訂查詢（@Query）提升效能

---

# 重構原則總結

**應該做：**
- 在測試保護下進行重構
- 小步前進，一次一個重構點
- 嚴格遵守 /aibdd.auto.java.code-quality 各項規範
- 每次重構後立即執行 `mvn clean test`

**不應該做：**
- 沒有測試保護就重構
- 一次改動過多
- 違反任何規範
- 強行重構已經清晰的程式碼
- 添加測試未要求的功能（那是新的紅燈，不是重構）

---

# 完成條件

- 所有識別的重構點已處理（或確認無需重構）
- `mvn clean test -Dtest=RunCucumberTest -Dcucumber.filter.tags="not @ignore"` 所有測試通過
- 所有測試 warnings 已清除
- 程式碼符合 /aibdd.auto.java.code-quality 的所有規範
