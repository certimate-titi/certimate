---
name: aibdd.auto.python.e2e.green
description: Python E2E Stage 3：綠燈階段。Trial-and-error 循環讓測試通過，實作後端 API（schemas → services → controllers → 路由註冊）。可被 /python-e2e 調用，也可獨立使用。
user-invocable: true
args-config: arguments-template.yml
argument-hint: "[feature-file]"
input: ${PY_TEST_FEATURES_DIR}/**/*.feature, ${PY_STEPS_DIR}/**/*.py, ${PY_MODELS_DIR}/**/*.py
output: ${PY_SCHEMAS_DIR}/**/*.py, ${PY_SERVICES_DIR}/**/*.py, ${PY_API_DIR}/**/*.py, ${PY_MAIN_FILE}
---

# 角色

綠燈實作者。在 TDD 紅燈階段已經寫好 E2E 測試並確認失敗。現在進入綠燈階段：寫最少的程式碼讓測試通過，實作後端 API，不斷 trial-and-error 直到所有測試變綠。

---

# 入口

## 被 /python-e2e 調用時

接收參數 `FEATURE_FILE`，直接進入 trial-and-error 循環。

## 獨立使用時

詢問目標 feature 檔案：

```
請指定要處理的 Feature 檔案路徑：
（例如：${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature）
```

---

# 核心原則

## 0. 測試驅動開發的鐵律

**必須透過執行自動化測試來驗證實作是否完成，絕不猜測。**

- 每完成一個步驟，立即執行測試
- 無需詢問使用者，直接下達 `behave` 指令
- 根據測試結果決定下一步行動
- 絕不假設測試會通過
- 絕不詢問「測試通過了嗎？」

**測試執行策略（重要）**：

1. **開發階段：先跑目標情境的特定測試**
   - 快速驗證當前實作
   - 縮短反饋循環
   - 專注於正在開發的功能

2. **完成階段：執行總回歸測試**
   - 確保沒有破壞既有功能
   - 驗證系統整體穩定性
   - 必須通過所有測試才算完成

**執行測試的時機與範圍**：
```
開發中（每個步驟後）：
→ behave ${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature
  （只跑當前功能的測試，快速反饋）

→ behave ${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature --name "成功增加影片進度"
  （只跑特定測試情境，更快速）

完成時（最終驗證）：
→ behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore
  （只跑已完成紅燈的 features，確保沒有破壞既有功能）
```

**測試指令範例**：
```bash
# 1. 開發階段：執行特定 Feature 檔案（快速迭代）
behave ${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature

# 2. 開發階段：執行特定 Scenario（最快）
behave ${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature --name "成功增加影片進度"

# 3. 完成階段：執行所有已完成紅燈的測試（總回歸測試）
behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore
```

**重要提醒**：
- 開發時：頻繁執行特定測試（快速反饋）
- 完成前：必須執行 `behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore`（總回歸測試）
- 只有當**所有已完成紅燈的測試**都通過，才算完成綠燈階段
- 不要只跑特定測試就宣稱完成

**為什麼使用 `--tags=~@ignore`？**
- 只執行已完成紅燈實作的 features（已移除 `@ignore` 標籤）
- 避免執行尚未實作的 features 造成混淆
- 確保回歸測試的範圍清晰明確

## 1. 最小增量開發原則

只寫讓測試通過所需的最少程式碼，不要多做。

**範例概念**：
```python
# 做太多了（測試沒要求）
@router.post("/lesson-progress/update-video-progress")
def update_video_progress(request):
    validate_inventory()      # 沒測試
    send_email_notification() # 沒測試
    log_audit_trail()        # 沒測試
    return update_progress_logic(request)

# 剛好夠（只實作測試要求的）
@router.post("/lesson-progress/update-video-progress")
def update_video_progress(request):
    return update_progress_logic(request)
```

## 2. Trial-and-Error 流程

**核心流程**：測試 → 看錯誤 → 修正 → 再測試（循環直到通過）

```
開發循環（快速迭代）：
1. 執行特定測試 → behave ${PY_TEST_FEATURES_DIR}/xxx.feature
2. 看錯誤訊息 → 理解失敗原因
3. 寫最少的程式碼修正這個錯誤
4. 再次執行特定測試 → behave ${PY_TEST_FEATURES_DIR}/xxx.feature
5. 還有錯誤？回到步驟 2
6. 特定測試通過？進入完成驗證

完成驗證（回歸測試）：
7. 執行所有已完成紅燈的測試 → behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore
8. 所有測試通過？完成綠燈！
9. 有測試失敗？回到步驟 2，修復破壞的測試
```

**重要**：
- 開發時：頻繁執行特定測試（快速反饋，節省時間）
- 完成前：必須執行總回歸測試 `behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore`（確保沒有破壞既有功能）
- 每次修改後立即執行測試，不要累積多個變更
- 直接執行 behave 指令，不需要詢問使用者
- 根據實際的測試輸出（HTTP 狀態碼、錯誤訊息）決定下一步
- 不要一次寫完所有程式碼
- 不要假設測試會通過
- 不要只跑特定測試就宣稱完成

**範例執行流程**：
```
開發階段（快速迭代）：
→ behave ${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature
  FAILED: HTTP 404 Not Found

→ 建立 API endpoint
→ behave ${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature
  FAILED: HTTP 500 Internal Server Error

→ 修正 Service 邏輯
→ behave ${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature
  FAILED: HTTP 400 Bad Request (進度不可倒退)

→ 調整業務規則驗證
→ behave ${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature
  PASSED（特定測試通過）

完成驗證（回歸測試）：
→ behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore
  2 features passed, 5 scenarios passed（所有測試通過，真正完成！）
```

---

# 實作流程

按照測試錯誤訊息逐步實作：

**基本流程**：
1. 執行測試 → `behave ${PY_TEST_FEATURES_DIR}/xxx.feature`
2. 看錯誤訊息（HTTP 404? 500? 400?）
3. 根據錯誤補充最少的程式碼（schemas → services → controllers → 註冊路由）
4. 再次執行測試
5. 循環直到特定測試通過
6. 執行總回歸測試 → `behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore`

**重點**：
- 每個步驟後立即執行測試
- 根據測試輸出決定下一步
- 完成前必須執行 `behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore`
- 不要一次寫完所有程式碼

---

# 常見錯誤修復

## HTTP 404 Not Found
**原因**：API Endpoint 不存在
**修復**：
1. 在 `${PY_API_DIR}/` 中創建 router
2. 在 `${PY_MAIN_FILE}` 中註冊 router

```python
# ${PY_API_DIR}/lesson_progress.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ${PY_CORE_DIR.replace('/', '.')}.deps import get_db

router = APIRouter()

@router.post("/lesson-progress/update-video-progress")
def update_video_progress(request: UpdateVideoProgressRequest, db: Session = Depends(get_db)):
    # TODO: 實作業務邏輯
    pass

# ${PY_MAIN_FILE}
from ${PY_API_DIR.replace('/', '.')}.lesson_progress import router as lesson_progress_router
app.include_router(lesson_progress_router, prefix="/api/v1")
```

## HTTP 500 Internal Server Error
**原因**：後端程式碼有錯誤
**修復**：
1. 檢查錯誤訊息
2. 修正 Service/Repository 的邏輯

## HTTP 400 Bad Request
**原因**：業務規則驗證失敗
**修復**：
1. 確認業務規則正確實作
2. 調整驗證邏輯

## HTTP 401 Unauthorized
**原因**：JWT Token 驗證失敗
**修復**：
1. 確認 `${PY_CORE_DIR}/deps.py` 中的 `get_current_user_id` 實作正確
2. 確認 JWT 密鑰與測試用的 JwtHelper 一致

---

# 完成條件

綠燈階段完成的標準：

**開發階段**：
- [ ] 執行特定測試 `behave ${PY_TEST_FEATURES_DIR}/xxx.feature`
- [ ] 確認目標功能測試通過

**完成驗證（必須）**：
- [ ] **執行總回歸測試 `behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore`**
- [ ] **所有已完成紅燈的測試通過（綠燈）**
- [ ] 沒有破壞既有功能
- [ ] 程式碼簡單直接

**驗證方式**：
```bash
# 開發階段：執行特定功能的測試（快速迭代）
behave ${PY_TEST_FEATURES_DIR}/01-增加影片進度.feature

# 完成驗證：執行所有已完成紅燈的測試（總回歸測試，必須）
behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore
```

**只有當執行 `behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore` 顯示所有測試 PASSED 時，才算完成綠燈階段。**

**不需要**：
- 程式碼優雅（留給重構階段）
- 效能優化（留給重構階段）
- 完整錯誤處理（測試沒要求就不做）
- 額外的 API 功能（測試沒要求就不做）
- 詢問使用者「測試通過了嗎？」（直接執行 behave 確認）
- 只跑特定測試就宣稱完成（必須執行總回歸測試）

---

# 記住

1. **測試驅動你** - 看測試錯誤決定下一步要實作什麼
2. **最小實作** - 只寫通過測試需要的程式碼
3. **Trial-and-Error** - 執行測試 → 看錯誤 → 修正 → 再執行，不斷循環
4. **自動執行測試** - 每次修改後立即執行測試，無需詢問使用者
5. **根據實際結果行動** - 依據 behave 的輸出決定下一步

**測試執行的黃金原則**：
- 開發時：頻繁執行特定測試 `behave ${PY_TEST_FEATURES_DIR}/xxx.feature`（快速迭代）
- 完成前：必須執行總回歸測試 `behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore`（確保穩定）
- 有疑問？執行測試
- 修改完成？執行測試
- 想確認進度？執行測試
- 不要詢問「測試通過了嗎？」
- 不要假設測試結果
- 不要只跑特定測試就宣稱完成

**完成判定標準**：
```
特定測試通過 → 功能開發完成
                |
         執行總回歸測試
                |
  behave ${PY_TEST_FEATURES_DIR}/ --tags=~@ignore
                |
   所有已完成紅燈的測試通過
                |
         真正完成綠燈！
```

完成綠燈後，進入重構階段（Stage 4）。
