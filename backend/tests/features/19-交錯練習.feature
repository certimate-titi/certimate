Feature: 交錯練習

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案   |
      | 1        | pro@example.com    | PRO_199    |
      | 2        | free@example.com   | FREE       |
    And 系統中有以下資源：
      | 資源 ID | 使用者 ID | 名稱              | 狀態      |
      | 1       | 1        | AWS_SAA_講義.pdf  | COMPLETED |
    And 系統中有以下心智圖知識節點：
      | 節點 ID | 資源 ID | 名稱           | 掌握度顏色 | 可出題數 |
      | 1       | 1       | EC2 運算服務   | 紅色       | 20       |
      | 2       | 1       | S3 儲存服務    | 綠色       | 20       |
      | 3       | 1       | IAM 身分管理   | 紅色       | 20       |
      | 4       | 1       | VPC 網路設定   | 灰色       | 20       |

  # ========== 交錯練習模式 ==========

  Rule: 後置（排序）- 選擇多個知識節點時，預設以交錯方式排列題目

    Example: 選擇 3 個知識節點出 9 題時，題目應交錯排列而非集中排列
      Given 使用者 "pro@example.com" 提交測驗設定，選擇節點 1、2、3，題數為 9
      When AI 生成 9 題完成，各節點各 3 題
      Then 題目排列順序不應為同一節點連續超過 2 題
      And 題目應以交錯方式排列，例如：節點1 → 節點2 → 節點3 → 節點1 → 節點2 → 節點3 ...
      And exam 的 question_order_mode 應為 "interleaved"

    Example: 僅選擇 1 個知識節點時，交錯練習不適用
      Given 使用者 "pro@example.com" 提交測驗設定，選擇節點 1，題數為 10
      When AI 生成 10 題完成
      Then 題目按難度由易到難排列
      And exam 的 question_order_mode 應為 "sequential"

  Rule: 後置（排序）- 交錯排列時應避免相同知識節點的題目相鄰

    Example: 當各節點題數不均時仍應盡量交錯
      Given 使用者 "pro@example.com" 提交測驗設定，選擇節點 1、2、3，題數為 10
      When AI 生成 10 題完成，節點 1 有 4 題、節點 2 有 3 題、節點 3 有 3 題
      Then 同一節點的題目最多連續出現 2 題
      And 相鄰題目的知識節點應盡量不同

  # ========== 交錯練習與難度交叉 ==========

  Rule: 後置（排序）- 交錯排列時同時考慮難度分散，避免連續出現高難度題

    Example: 交錯排列中難度也應分散
      Given 使用者 "pro@example.com" 提交測驗設定，選擇節點 1、2，題數為 10，難易度分配為 Easy:30% Medium:50% Hard:20%
      When AI 生成 10 題完成
      Then 題目應交錯排列知識節點
      And hard 難度的題目不應連續超過 2 題
      And 前 3 題中應至少包含 1 題 easy 難度（建立信心）

  # ========== 使用者可切換排列模式 ==========

  Rule: 前置（參數）- 使用者可在測驗設定頁選擇題目排列模式

    Example: 使用者選擇集中練習模式
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 1、2、3，題數為 9，排列模式為 "集中練習"
      Then 操作成功
      And exam 的 question_order_mode 應為 "grouped"
      And 題目應按知識節點分組排列

    Example: 使用者選擇交錯練習模式（預設）
      When 使用者 "pro@example.com" 提交測驗設定，選擇節點 1、2、3，題數為 9，排列模式為 "交錯練習"
      Then 操作成功
      And exam 的 question_order_mode 應為 "interleaved"

  # ========== 交錯練習與學習模式的整合 ==========

  Rule: 後置（排序）- Sprint 模式下交錯練習應優先穿插錯題節點

    Example: Sprint 模式下錯題相關節點的題目優先穿插
      Given 使用者 "pro@example.com" 的學習模式為 "sprint"
      And 使用者在節點 1 和節點 3 的歷史錯題較多
      When 使用者提交測驗設定，選擇節點 1、2、3、4，題數為 20
      Then 交錯排列中節點 1 和節點 3 的題目應更均勻地分散於整份考卷
      And 不應將錯題集中在考卷前段或後段

  # ========== 測驗結果中的交錯效果分析 ==========

  Rule: 後置（回應）- 測驗結果頁應標示本次考試使用的排列模式

    Example: 結果頁顯示交錯練習模式標籤
      Given 使用者 "pro@example.com" 完成一場交錯練習模式的測驗
      When 使用者查看測驗結果
      Then 結果頁應顯示排列模式標籤 "交錯練習"
      And 結果頁應包含提示：「交錯練習有助於長期記憶，持續使用效果更佳」
