---
name: aibdd.auto.python.ut.refactor
description: Python UT Stage 4：重構階段。Phase A（測試程式碼）→ 跑測試 → Phase B（生產程式碼）→ 跑測試。嚴格遵守 /aibdd.auto.python.code-quality 規範，安全規則禁止未經許可的跨檔搬移。可被 /python-ut 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${PY_STEPS_DIR}/**/*.py, ${PY_MODELS_DIR}/**/*.py, ${PY_REPOSITORIES_DIR}/fake_*.py, ${PY_SERVICES_DIR}/**/*.py
output: 重構後的程式碼（測試持續通過）
---

# 角色

BDD 重構階段協調器，負責在保持測試綠燈的前提下，改善程式碼品質。

**核心原則**：程式碼可以改變，但測試結果不能改變。

---

# 入口條件（雙模式）

## 模式 A：獨立使用

使用者直接調用 `/python-ut-refactor`。

1. 詢問目標 Feature File（若使用者未在 argument 帶入）
2. 確認綠燈階段已完成（測試全部通過）
3. 執行重構流程

## 模式 B：被 /python-ut 調用

接收參數：Feature File 路徑。直接執行重構流程。

---

# 重構的目標

1. **提升可讀性**：讓程式碼更容易理解
2. **提升可維護性**：讓程式碼更容易修改
3. **消除重複**：遵循 DRY 原則
4. **清理技術債**：移除 TODO 註解、臨時程式碼

---

# 工作流程

```
執行測試（確認綠燈）
    |
    v
【Phase A】先重構測試碼（steps / environment / tests）
    |
    v
執行測試（確認仍然綠燈）
    |
    v
【Phase B】再重構產品程式碼（app/ 下的 models / repositories / services）
    |
    v
執行測試（確認仍然綠燈）
    |
    v
完成重構
```

**關鍵**：
- 每個 Phase 結束都要跑一次測試
- Phase 內每次小步驟變更後也要跑測試（盡量小步）

---

# 重構任務清單

## 1. 清理 TODO 註解

移除所有樣板階段遺留的 TODO 註解。

**Before**：
```python
@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """
    TODO: [事件風暴部位: Aggregate - LessonProgress]
    TODO: 參考 /aibdd.auto.python.ut.handlers.aggregate-given 實作
    TODO: 參考 Aggregate/Table: LessonProgress
    """
    user_id = context.ids.get(user_name, user_name)
    # ...
```

**After**：
```python
@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """建立用戶的課程進度初始狀態"""
    user_id = context.ids.get(user_name, user_name)
    # ...
```

## 2. 改善 DocString 可讀性

為 step functions 添加有意義的 docstring。

**Before**：
```python
@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    # ...
```

**After**：
```python
@given('用戶 "{user_name}" 在課程 {lesson_id:d} 的進度為 {progress:d}%，狀態為 "{status}"')
def step_impl(context, user_name, lesson_id, progress, status):
    """建立用戶的課程進度初始狀態"""
    # ...
```

## 3. 檢查 /aibdd.auto.python.code-quality 規範

重構時須參考以下規範文件（位於 /aibdd.auto.python.code-quality skill）：

| 規範文件 | 重點 |
|---------|------|
| 程式碼品質規範 | Early Return、命名規範、程式碼長度 |
| 程式架構規範 | 分層架構、依賴方向 |
| SOLID設計原則 | SRP、OCP、DIP |
| Step-Definition組織規範 | Step 分類、一個 step 一個 module |
| StepDef-Meta註記清理規範 | TODO/META 清理標準 |
| 日誌實踐規範 | 日誌格式與等級 |

---

# 安全規則

**重構階段預設只做「局部小步」**，避免把測試碼改成另一種架構造成風險。

- **兩段式重構順序不可顛倒**：一定是先 Phase A（測試碼）→ 測試綠燈 → 再 Phase B（產品碼）→ 測試綠燈。
- **禁止自動抽 helpers / 抽共用模組**：除非使用者明確要求，否則不要新增 `helpers.py`、不要搬移/改寫 step 的結構。
- **禁止跨檔案搬動程式碼**：優先在原檔案內做最小的可讀性改善（例如移除 TODO、補 docstring、調整命名/縮排）。
- **如果真的要抽共用**：必須先徵詢確認，且一次只抽一個小片段，並在每次變更後立刻跑測試確認綠燈。

---

# Phase A：測試程式碼重構

## 範圍

- `${PY_STEPS_DIR}/**/*.py`（Step Definitions）
- `${PY_ENV_FILE}`（environment hooks）

## 常見重構項目

1. **移除 TODO 註解** → 替換為有意義的 docstring
2. **改善命名** → 變數名稱更語意化
3. **簡化邏輯** → 減少巢狀、使用 Early Return
4. **調整縮排與格式** → 統一程式碼風格

## Phase A 完成檢查

```bash
behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore
```

所有測試必須通過，才能進入 Phase B。

---

# Phase B：生產程式碼重構

## 範圍

- `${PY_MODELS_DIR}/**/*.py`（Aggregates）
- `${PY_REPOSITORIES_DIR}/**/*.py`（FakeRepositories）
- `${PY_SERVICES_DIR}/**/*.py`（Services）
- `${PY_APP_DIR}/exceptions.py`（自定義例外）

## 常見重構項目

1. **改善 Model 定義** → 添加型別註解、property
2. **改善 Repository 介面** → 方法命名一致性
3. **改善 Service 邏輯** → Early Return、Guard Clause
4. **提取共用常數** → 狀態映射、錯誤訊息

## Phase B 完成檢查

```bash
behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore
```

所有測試必須通過。

---

# Critical Rules

### R1: 每個 Phase 與每個小步驟後都要立即執行測試
```bash
behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore
```

### R2: 一次只做一個小重構
不要同時重構多個部分，避免難以定位問題。

### R3: 只抽取重複兩次以上的邏輯
單次出現的邏輯不需要抽取，避免過度抽象。

### R4: 保持 step 函數簡潔
重構後的 step 函數應該更易讀，邏輯清晰。

### R5: 不改變測試行為
重構只改善程式碼結構，不改變測試的輸入/輸出。

### R6: 移除所有 TODO 註解
重構完成後，TODO 註解應該全部被有意義的 docstring 取代。

### R7: 遵守安全規則
- 不自動抽 helpers（除非使用者明確要求）
- 不跨檔案搬動程式碼（除非使用者明確要求）
- 每次變更後都跑測試

### R8: 參考 /aibdd.auto.python.code-quality 規範
所有重構須符合 /aibdd.auto.python.code-quality 的規範要求。

---

# 完成條件

- Phase A（測試程式碼）重構完成，測試通過
- Phase B（生產程式碼）重構完成，測試通過
- 所有 TODO 註解已移除
- Step 函數有清楚的 docstring
- 程式碼可讀性提升
- 執行 `behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore` 所有測試通過
