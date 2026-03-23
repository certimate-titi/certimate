Feature: 測驗設定

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | free@example.com   | FREE     |
      | 2        | pro@example.com    | PRO      |
      | 3        | ultra@example.com  | ULTRA    |
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

  Rule: 後置（狀態）- 成功提交設定後應建立狀態為 PENDING 的測驗任務並透過 SSE 推送生成進度

    Example: 成功提交測驗設定後建立測驗任務
      When 使用者 "free@example.com" 提交測驗設定，選擇節點 1 和節點 2，題數為 10，難易度分配為 Easy:50% Medium:50% Hard:0%
      Then 操作成功
      And 系統應建立測驗任務，初始狀態為 "PENDING"
      And 系統應開始透過 SSE 推送生成進度事件

    Example: SSE 進度事件應按預期階段依序推送
      Given 使用者 "free@example.com" 已提交合法測驗設定並建立測驗任務 ID 為 100
      When 後端 AI 生成服務依序完成各階段
      Then SSE 應依序推送以下進度事件：
        | 進度百分比 | 說明訊息                    |
        | 10        | 正在從向量庫提取知識點...   |
        | 40        | AI 教練正在設計考題陷阱...  |
        | 80        | 校對邏輯與排版中...         |
        | 100       | 考卷準備完畢！              |

  Rule: 後置（回應）- 生成完成後回傳測驗 ID 供前端導向機考工作區

    Example: 測驗生成完成後回傳可用的測驗 ID 與題目總數
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 5，題數為 20，難易度分配為 Easy:30% Medium:50% Hard:20%
      And 後端 AI 成功生成考卷
      Then 操作成功
      And 回應應包含有效的測驗 ID
      And 回應應包含生成的題目總數 20
