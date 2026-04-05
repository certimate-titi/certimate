# TiTi CEO 心跳處理紀錄

**時間戳記：** 2026-04-06T01:08:22
**執行者：** CEO（自動心跳排程）
**觸發類型：** 🟢 日常巡檢（scheduled-task: check-todo）

---

## 一、任務來源

讀取 `docs/ToDoList.md`，發現 3 個待辦項目：
1. Edu 學生已有訂閱方案，Ultra 方案帶入 EDU 後的處置
2. Edu 學生邀請信點擊連結後應先進入密碼設定頁
3. `feature_conflicts.md` 中的決議事項需處理（包含 6 個需 titi-commander 評估項目）

---

## 二、已執行工作

### 2.1 待辦 1：Edu 學生訂閱衝突處置

**問題：** Edu 學生若已有個人付費訂閱（PRO_199 / PRO_PLUS_399），被機構指派 EDU 方案後，雙重訂閱如何處置？

**CEO 決議：**
- 個人訂閱自動進入 `suspended`（暫停計費）狀態
- EDU 期間享 EDU 方案權益（不降級到個人訂閱所對應的較低或較高層）
- EDU 結束（機構移除 / ULTRA 到期）→ 個人訂閱自動恢復 active，下次扣款日從恢復日起重算 30 天
- 若個人訂閱在暫停期間自然到期 → EDU 結束後降為 FREE

**修改檔案：**
- `project/features/08-訂閱管理.feature`
  - 新增章節：「EDU 學生既有訂閱衝突處置」
  - 新增 4 個 scenarios：
    1. PRO_199 用戶被指派 EDU 後個人訂閱暫停
    2. PRO_PLUS_399 用戶被指派 EDU 後個人訂閱暫停
    3. 機構移除學生後個人 PRO_199 訂閱恢復
    4. 機構 ULTRA 到期後 EDU 學生個人訂閱恢復
    5. EDU 期間個人訂閱到期則 EDU 結束後回 FREE

**目標對齊：** O3 - KR1（控制成本與維持品質）

---

### 2.2 待辦 2：Edu 學生邀請信密碼設定流程

**問題：** 學生點擊邀請信後直接進入首頁，未設定密碼，導致帳號安全與體驗問題。

**CEO 決議：**
- 邀請連結導向：`/invite/setup-password?token={invite_token}`
- Token 有效期：72 小時
- 密碼規則：同一般用戶（強度驗證、確認密碼欄）
- 密碼設定完成 → 帳號啟用 → JWT 發放 → 導向儀表板
- Token 過期 → 顯示提示並引導聯繫管理員重發邀請
- Token 已用 → 顯示「帳號已啟用，請直接登入」

**修改檔案：**
- `project/features/01-身分驗證.feature`
  - 新增章節：「EDU 學生邀請啟用流程」
  - 新增 5 個 scenarios：
    1. EDU 學生點擊有效邀請連結後導向密碼設定頁
    2. 完成密碼設定後帳號啟用並導向儀表板
    3. 密碼確認不一致時設定失敗
    4. 密碼強度不足時設定失敗
    5. Token 過期時顯示過期提示
    6. Token 已使用時顯示已啟用提示

**目標對齊：** O2 - KR1（擴大使用者基礎）

---

### 2.3 待辦 3：feature_conflicts.md 決議事項處理

讀取 `docs/feature_conflicts.md`，找到 6 個標記需 `/titi-commander` 評估的項目：

#### 衝突 1：PRO_199 AI 教練次數限制

**CEO 決議：**
| 方案 | AI 教練月配額 | 功能層級 |
|------|------------|--------|
| FREE | 0 次 | 不可用 |
| PRO_199 | 20 次/月 | 基礎教練 |
| PRO_PLUS_399 | 100 次/月 | 完整教練 |
| ULTRA_1599 | 無限 | 進階教練 |
| EDU | 5 次/月 | 基礎（共用機構配額池）|

**後續工作（待手動執行）：**
- 更新 08-訂閱管理.feature 配額對照表
- 在 07-錯題複習與AI教練.feature 新增次數限制 scenarios

#### 衝突 4：節點顏色更新時機（後端即時 vs 前端 lazy）

**CEO 決議：**
- 採後端即時更新：任何作答事件 → POST exam-results → 觸發 node_mastery 更新 → WebSocket/SSE 推送
- 前端初始化：GET knowledge-map 拉取最新狀態
- Feature 03 + 27 應統一描述為後端即時機制

**後續工作：** 更新 03-知識心智圖.feature 措辭，移除「返回此頁面時」觸發的描述

#### 衝突 7：AI 教練對話 vs 考後總評功能確認

**CEO 決議：**
- **AI 教練對話**：`/api/v1/ai-coach/chat`，互動問答，PRO_199 起可用（月配額限制），SSE 串流
- **考後總評**：`/api/v1/exam-results/{id}/analysis`，靜態報告，PRO_199 基礎版（前 3 大弱點），PRO_PLUS_399 完整版
- 兩者共用 LLM 底層，但 prompt 與 endpoint 獨立

**後續工作：** 更新 06-測驗結果.feature 說明 PRO_199 可得基礎考後總評

#### 問題 8：Feature 28 回溯雙條件觸發邏輯

**CEO 決議：** OR 關係，先到先得，不重複回溯
- 條件A：連續答錯 2 題（快速信號）
- 條件B：節點答對率 < 40%（累積信號）
- 兩條件同時滿足：依先觸發者處理，回溯後計數器歸零

**後續工作：** 更新 28-階層式難度遞進.feature 補充 OR 邏輯說明

#### 問題 9：知識樹 vs 心智圖節點術語定義

**CEO 決議（名稱定義）：**
- 前端 UX：「知識心智圖」（統一用語）
- 後端 DB/API：`knowledge_node`
- 考科官方架構（admin）：`exam_syllabus_node`（Feature 26/29）
- 用戶個人節點（user）：`user_knowledge_node`（Feature 03/04/27）
- DB 表：`knowledge_nodes`，以 `node_type` 欄位區分（`syllabus` / `personal`）

**後續工作：** 更新 erm.dbml 補充 `node_type` 欄位說明

#### 問題 10：錯題複習是否觸發 node_mastery 更新

**CEO 決議：** 是，所有作答事件均觸發 node_mastery 更新（含錯題複習）
- 實作：`calculate_node_mastery()` 覆蓋所有 `exam_type`

**後續工作：** 在 07-錯題複習與AI教練.feature 新增 node_mastery 更新 scenario

---

## 三、修改檔案清單

| 檔案 | 操作 | 說明 |
|------|------|------|
| `project/features/08-訂閱管理.feature` | 新增章節 | EDU 訂閱衝突處置（5 scenarios）|
| `project/features/01-身分驗證.feature` | 新增章節 | EDU 邀請啟用流程（6 scenarios）|
| `docs/feature_conflicts.md` | 更新決議 | 6 項 CEO 評估補全 |
| `docs/ToDoList.md` | 更新 | 3 個待辦標記完成，新增完成紀錄 |

---

## 四、待手動執行（董事會批准後）

| 優先 | 工作項目 | 對應衝突 |
|------|---------|--------|
| 🔴 高 | 更新 07-錯題複習.feature：AI 教練次數限制 scenarios | 衝突1 |
| 🔴 高 | 更新 08-訂閱管理.feature：配額對照表加入 AI 教練次數欄 | 衝突1 |
| 🟡 中 | 更新 06-測驗結果.feature：PRO_199 基礎考後總評 scenario | 衝突7 |
| 🟡 中 | 更新 28-階層式難度遞進.feature：OR 邏輯補充 | 問題8 |
| 🟡 中 | 更新 03-知識心智圖.feature：改為後端即時更新描述 | 衝突4 |
| 🟢 低 | 更新 erm.dbml：knowledge_nodes 加 node_type 欄位 | 問題9 |
| 🟢 低 | 在 07-錯題複習.feature 補充 node_mastery 更新 scenario | 問題10 |

---

## 五、OKR 對齊

| 決議 | 對齊目標 |
|------|--------|
| EDU 訂閱衝突 | O2-KR1（使用者基礎）、O3-KR1（成本控制）|
| EDU 邀請流程 | O2-KR3（NPS 提升）|
| AI 教練次數限制 | O3-KR1（LLM 成本 ≤ 15% 營收）|
| 考後總評功能邊界 | O1-KR2（出題效率）|

---

## 六、下次心跳

**建議：** 2026-04-07 09:00（日常巡檢）
**監控項目：** 上述「待手動執行」項目是否已處理
