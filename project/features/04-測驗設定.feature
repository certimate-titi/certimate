@frontend
Feature: 測驗設定

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | free@example.com   | FREE     |
      | 2        | pro@example.com    | PRO_199    |
      | 3        | ultra@example.com  | ULTRA_1599 |
    And 系統中有以下資源：
      | 資源 ID | 使用者 ID | 名稱              | 狀態      |
      | 1       | 1        | AWS_SAA_講義.pdf  | COMPLETED |
      | 2       | 2        | 雲端架構筆記.md   | COMPLETED |
      | 3       | 3        | PMP考試寶典.pdf   | COMPLETED |
    And 系統中有以下心智圖知識節點：
      | 節點 ID | 資源 ID | 名稱           | 掌握度顏色 | 可出題數 |
      | 1       | 1       | EC2 運算服務   | 紅色       | 20       |
      | 2       | 1       | S3 儲存服務    | 綠色       | 20       |
      | 3       | 1       | IAM 身分管理   | 紅色       | 20       |
      | 4       | 1       | VPC 網路設定   | 灰色       | 20       |
      | 5       | 2       | 高可用架構     | 灰色       | 60       |
      | 6       | 3       | 整合管理       | 灰色       | 100      |

  # ========== 跨學科導航與範圍過濾 ==========

  Rule: 前置（導航）- 提供學科切換器過濾可用於測驗的資源範圍

    Example: 切換學科後測驗範圍僅顯示該學科關聯的資源
      When 使用者在測驗設定頁面頂部選擇學科 "PMP"
      Then "1 選擇測驗範圍" 列表中應僅顯示 subjectId 為 "subj_pmp" 且狀態為 COMPLETED 的資源
      And 選題列表應排除非當前學科的資源（如 AWS 講義）

  # ========== 前置條件 ==========

  Rule: 前置（參數）- 必須至少選擇一個知識節點範圍

    Example: 未選擇任何節點即送出設定失敗
      When 使用者 "free@example.com" 提交測驗設定，未勾選任何知識節點，題數為 5
      Then 操作失敗
      And 錯誤訊息應為 "請至少選擇一個知識範圍"

  Rule: 前置（參數）- 考古題模擬考模式下，題目數量不得超過所選範圍的可出題總數

    Example: historical_only 模式要求題數超過 capacity 時失敗
      Given 使用者 "free@example.com" 選擇 exam_mode = "historical_only"
      When 使用者 "free@example.com" 提交測驗設定，選擇節點 1，題數為 30
      Then 操作失敗
      And 錯誤訊息應為 "所選範圍最多可出 20 題，請調整題數"

  @backend
  Rule: 前置（參數）- AI 混合 / AI 生成模式不受所選範圍 capacity 限制

    Example: AI 混合模式選 50 題即使所選節點 capacity 僅 10 題仍可生成
      Given 使用者 "ultra@example.com" 選擇 exam_mode = "ai_hybrid"
      And 所選節點的 capacity 總和為 10 題
      When 使用者 "ultra@example.com" 提交測驗設定，題數為 50
      Then 操作成功
      And 系統應從 chunks 動態生成題目補足，不回 capacity 錯誤

    Example: 預設模式（未指定 exam_mode）視為 AI 模式，亦不受 capacity 限制
      Given 使用者 "ultra@example.com" 未指定 exam_mode
      And 所選節點的 capacity 總和為 5 題
      When 使用者 "ultra@example.com" 提交測驗設定，題數為 30
      Then 操作成功

  Rule: 前置（參數）- FREE 方案每次測驗題數上限為 10 題

    Example: FREE 用戶要求超過 10 題失敗
      When 使用者 "free@example.com" 提交測驗設定，選擇節點 1 和節點 2，題數為 15
      Then 操作失敗
      And 錯誤訊息應為 "FREE 方案每次測驗最多 10 題，升級 PRO 最多可出 50 題"

    Example: FREE 用戶要求恰好 10 題成功
      When 使用者 "free@example.com" 提交測驗設定，選擇節點 1 和節點 2，題數為 10
      Then 操作成功

  Rule: 前置（參數）- PRO 方案每次測驗題數上限為 50 題

    Example: PRO 用戶要求超過 50 題失敗
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 5，題數為 60
      Then 操作失敗
      And 錯誤訊息應為 "PRO 方案每次測驗最多 50 題，升級 PRO_PLUS 最多可出 100 題"

    Example: PRO 用戶要求恰好 50 題成功
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 5，題數為 50
      Then 操作成功

  Rule: 前置（參數）- PRO_PLUS 方案每次測驗題數上限為 100 題

    Example: PRO_PLUS 用戶要求 100 題成功
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email                | 訂閱方案      |
        | 4        | proplus@example.com  | PRO_PLUS_399  |
      And 系統中有以下資源：
        | 資源 ID | 使用者 ID | 名稱            | 狀態      |
        | 4       | 4        | 大型題庫.pdf    | COMPLETED |
      And 系統中有以下心智圖知識節點：
        | 節點 ID | 資源 ID | 名稱       | 掌握度顏色 | 可出題數 |
        | 7       | 4       | 綜合測驗   | 灰色       | 150      |
      When 使用者 "proplus@example.com" 提交測驗設定，選擇節點 7，題數為 100
      Then 操作成功

  Rule: 前置（參數）- ULTRA 方案每次測驗題數無上限

    Example: ULTRA 用戶要求 100 題成功
      When 使用者 "ultra@example.com" 提交測驗設定，選擇節點 6，題數為 100
      Then 操作成功

  # ========== Bloom 配比自動偵測 ==========

  Rule: 後置（配比）- 提交測驗設定時系統自動偵測科目是否有考古題，決定 Bloom 配比來源

    Example: 科目有考古題時自動套用考古題 Bloom 配比
      Given 學科 "信託業業務人員" 有以下考古題 Bloom 統計：
        | bloom_category | percentage |
        | remember       | 36         |
        | understand     | 28         |
        | apply          | 20         |
        | analyze        | 10         |
        | evaluate       | 4          |
        | create         | 2          |
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 5，題數為 20，難易度分配為 Easy:30% Medium:50% Hard:20%
      Then 操作成功
      And 系統應自動套用考古題 Bloom 配比作為出題依據
      And 測驗任務的 bloom_source 應為 "historical"

    Example: 科目無考古題時使用系統預設 Bloom 配比
      When 使用者 "free@example.com" 提交測驗設定，選擇節點 1 和節點 2，題數為 10，難易度分配為 Easy:50% Medium:50% Hard:0%
      Then 操作成功
      And 系統應套用預設 Bloom 配比（remember:20/understand:25/apply:25/analyze:15/evaluate:10/create:5）
      And 測驗任務的 bloom_source 應為 "default"

  # ========== 考古題模擬考模式 ==========

  Rule: 前置（模式）- 使用者可選擇「考古題模擬考」模式，100% 從考古題題庫出題

    Example: 選擇考古題模擬考模式時 100% 從題庫抽取
      Given 使用者 "pro@example.com" 有學習歷程於考科 "AI 應用規劃師"
      And 考科 "AI 應用規劃師" 有 213 題考古題
      When 使用者 "pro@example.com" 提交測驗設定：
        | 欄位            | 值                                          |
        | node_ids        | [人工智慧基礎概論, 生成式AI應用與規劃]          |
        | question_count  | 20                                           |
        | exam_mode       | historical_only                              |
      Then 操作成功
      And 測驗應包含 20 題
      And 所有題目應來自考古題題庫（reliability 全部為 green）
      And 不應呼叫 AI 生成服務

    Example: 考古題模擬考模式下題庫不足時自動調整題數
      Given 使用者 "pro@example.com" 有學習歷程於考科 "AI 應用規劃師"
      And 考科 "AI 應用規劃師" 知識節點 "機器學習技術與應用" 僅有 5 題考古題
      When 使用者 "pro@example.com" 提交測驗設定：
        | 欄位            | 值                     |
        | node_ids        | [機器學習技術與應用]     |
        | question_count  | 50                     |
        | exam_mode       | historical_only         |
      Then 操作成功
      And 回應應包含提示 "此範圍考古題僅 5 題，已自動調整"
      And 測驗應包含 5 題

  # ========== 考古題題庫作為測驗範圍 ==========

  Rule: 前置（範圍）- 使用者無個人文件時，系統考古題題庫的知識節點應作為可選測驗範圍

    Example: 使用者無上傳文件但科目有考古題時，可選擇考古題知識節點出題
      Given 使用者 "pro@example.com" 有學習歷程於考科 "AI 應用規劃師"
      And 使用者 "pro@example.com" 未上傳任何資源
      And 考科 "AI 應用規劃師" 有系統考古題資源，包含以下知識節點：
        | 節點名稱           | 可出題數 |
        | 人工智慧基礎概論    | 44      |
        | 生成式AI應用與規劃  | 94      |
      When 使用者 "pro@example.com" 提交測驗設定，選擇知識節點 "人工智慧基礎概論"，題數為 20
      Then 操作成功
      And 測驗應包含 20 題考古題

  # ========== 後置條件 ==========

  # 詳細的多階段 AI Prompt 流程請參見 04a-AI考題生成服務.feature

  Rule: 後置（狀態）- 成功提交設定後應建立狀態為 PENDING 的測驗任務並透過 SSE 推送生成進度

    Example: 成功提交測驗設定後建立測驗任務
      When 使用者 "free@example.com" 提交測驗設定，選擇節點 1 和節點 2，題數為 10，難易度分配為 Easy:50% Medium:50% Hard:0%
      Then 操作成功
      And 系統應建立測驗任務，初始狀態為 "PENDING"
      And 系統應開始透過 SSE 推送生成進度事件

    # SSE 四階段進度事件規格詳見 04a-AI考題生成服務.feature

  Rule: 後置（回應）- 生成完成後回傳測驗 ID 供前端導向機考工作區

    Example: 測驗生成完成後回傳可用的測驗 ID 與題目總數
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 5，題數為 20，難易度分配為 Easy:30% Medium:50% Hard:20%
      And 後端 AI 成功生成考卷
      Then 操作成功
      And 回應應包含有效的測驗 ID
      And 回應應包含生成的題目總數 20

  # ========== ULTRA 專屬：Bloom 層級自訂比例 ==========

  Rule: 前置（參數）- ULTRA 方案可自訂 Bloom 認知層級比例

    Example: ULTRA 用戶自訂 Bloom 比例成功提交
      When 使用者 "ultra@example.com" 提交測驗設定，選擇節點 6，題數為 50，自訂 Bloom 比例為：
        | bloom_category | percentage |
        | remember       | 10         |
        | understand     | 15         |
        | apply          | 30         |
        | analyze        | 25         |
        | evaluate       | 15         |
        | create         | 5          |
      Then 操作成功
      And 測驗任務的 bloom_source 應為 "custom"
      And 測驗任務的 bloom_distribution 應符合自訂比例

    Example: 非 ULTRA 用戶傳入 Bloom 自訂比例時忽略，使用預設
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 5，題數為 20，自訂 Bloom 比例為：
        | bloom_category | percentage |
        | remember       | 10         |
        | understand     | 10         |
        | apply          | 30         |
        | analyze        | 30         |
        | evaluate       | 15         |
        | create         | 5          |
      Then 操作成功
      And 測驗任務的 bloom_source 應為 "default"（非 custom）
      And 回應應包含提示 "Bloom 自訂比例為 ULTRA 方案專屬功能"

  @frontend
  Rule: 前置（UI）- 進階出題配方面板僅 ULTRA tier 與管理者帳號可見

    # 落地紀錄（2026-05-03）：守衛 (isUltra || isAdmin)。對齊權限模型備忘：
    # 管理者帳號（ADMIN/SUPER_ADMIN）自動含 user-facing tier 功能。
    # 純 USER tier（FREE / PRO / PRO_PLUS）看不到此面板。

    Example: ULTRA 用戶於測驗設定頁可見「進階出題配方」面板
      Given 使用者 "ultra@example.com" 已登入
      When 使用者 "ultra@example.com" 進入測驗設定頁
      Then 頁面應顯示「進階出題配方」面板

    Example: FREE 用戶於測驗設定頁看不見「進階出題配方」面板
      Given 使用者 "free@example.com" 已登入
      When 使用者 "free@example.com" 進入測驗設定頁
      Then 頁面應不顯示「進階出題配方」面板

    Example: ADMIN 管理者於測驗設定頁可見「進階出題配方」面板
      Given 使用者 "admin@example.com" 已登入
      When 使用者 "admin@example.com" 進入測驗設定頁
      Then 頁面應顯示「進階出題配方」面板

    Example: ULTRA 用戶自訂 Bloom 比例加總不為 100 時失敗
      When 使用者 "ultra@example.com" 提交測驗設定，選擇節點 6，題數為 50，自訂 Bloom 比例為：
        | bloom_category | percentage |
        | remember       | 30         |
        | understand     | 30         |
        | apply          | 30         |
        | analyze        | 20         |
        | evaluate       | 0          |
        | create         | 0          |
      Then 操作失敗
      And 錯誤訊息應為 "Bloom 比例加總必須為 100%"

  # ========== ULTRA 專屬：考古題優先召回 ==========

  Rule: 後置（配比）- ULTRA 用戶出題時考古題召回權重加倍

    Example: ULTRA 用戶混合出題時考古題佔比顯著高於非 ULTRA
      When 使用者 "ultra@example.com" 提交測驗設定，選擇節點 6，題數為 50
      Then 操作成功
      And 測驗中考古題（reliability 為 green）佔比應不低於 60%（在題庫充足時）

    Example: PRO 用戶混合出題時使用標準召回權重
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 5，題數為 20
      Then 操作成功
      And 測驗中考古題與 AI 生成題的比例應依標準權重分配

  # ========== UI 元件補充場景 ==========

  Rule: 前置（參數）- 題型切換應支援選擇多種題型

    Example: 選擇多種題型成功提交測驗設定
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 5，題數為 20，題型為 "單選" 和 "多選" 和 "填空"
      Then 操作成功
      And 系統應建立測驗任務，包含題型 "單選" 和 "多選" 和 "填空"

  Rule: 前置（參數）- 難度滑桿應支援調整至最高難度

    Example: 難度滑桿調整至最高難度後成功提交
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 5，題數為 20，難易度分配為 Easy:0% Medium:0% Hard:100%
      Then 操作成功
      And 系統應建立測驗任務，難易度分配中 Hard 佔比應為 100%

  Rule: 前置（狀態）- 文件未處理完成時無法選擇作為測驗範圍

    Example: 文件狀態為 PROCESSING 時無法選擇
      Given 系統中有以下資源：
        | 資源 ID | 使用者 ID | 名稱              | 狀態       |
        | 5       | 1        | 處理中文件.pdf    | PROCESSING |
      When 使用者 "free@example.com" 嘗試在測驗設定中選擇資源 5
      Then 操作失敗
      And 錯誤訊息應為 "該文件尚未處理完成，無法用於出題"
