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

  Rule: 前置（參數）- 題目數量不得超過所選範圍的可出題總數

    Example: 要求的題數超過所選節點可出題數時失敗
      When 使用者 "free@example.com" 提交測驗設定，選擇節點 1，題數為 30
      Then 操作失敗
      And 錯誤訊息應為 "所選範圍最多可出 20 題，請調整題數"

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
      And 錯誤訊息應為 "PRO 方案每次測驗最多 50 題，升級 ULTRA 最多可出 100 題以上"

    Example: PRO 用戶要求恰好 50 題成功
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 5，題數為 50
      Then 操作成功

  Rule: 前置（參數）- ULTRA 方案每次測驗題數上限為 100 題以上

    Example: ULTRA 用戶要求 100 題成功
      When 使用者 "ultra@example.com" 提交測驗設定，選擇節點 6，題數為 100
      Then 操作成功

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

  # ========== UI 元件補充場景 ==========

  Rule: 前置（參數）- 題型切換應支援選擇多種題型

    @ignore
    Example: 選擇多種題型成功提交測驗設定
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 5，題數為 20，題型為 "單選" 和 "多選" 和 "填空"
      Then 操作成功
      And 系統應建立測驗任務，包含題型 "單選" 和 "多選" 和 "填空"

  Rule: 前置（參數）- 難度滑桿應支援調整至最高難度

    @ignore
    Example: 難度滑桿調整至最高難度後成功提交
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 5，題數為 20，難易度分配為 Easy:0% Medium:0% Hard:100%
      Then 操作成功
      And 系統應建立測驗任務，難易度分配中 Hard 佔比應為 100%

  Rule: 前置（參數）- PRO_PLUS 方案每次測驗題數上限為 100 題

    @ignore
    Example: PRO_PLUS 用戶要求 100 題成功
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email                | 訂閱方案  |
        | 4        | proplus@example.com  | PRO_PLUS_399 |
      And 系統中有以下資源：
        | 資源 ID | 使用者 ID | 名稱            | 狀態      |
        | 4       | 4        | 大型題庫.pdf    | COMPLETED |
      And 系統中有以下心智圖知識節點：
        | 節點 ID | 資源 ID | 名稱       | 掌握度顏色 | 可出題數 |
        | 7       | 4       | 綜合測驗   | 灰色       | 150      |
      When 使用者 "proplus@example.com" 提交測驗設定，選擇節點 7，題數為 100
      Then 操作成功

  Rule: 前置（狀態）- 文件未處理完成時無法選擇作為測驗範圍

    @ignore
    Example: 文件狀態為 PROCESSING 時無法選擇
      Given 系統中有以下資源：
        | 資源 ID | 使用者 ID | 名稱              | 狀態       |
        | 5       | 1        | 處理中文件.pdf    | PROCESSING |
      When 使用者 "free@example.com" 嘗試在測驗設定中選擇資源 5
      Then 操作失敗
      And 錯誤訊息應為 "該文件尚未處理完成，無法用於出題"
