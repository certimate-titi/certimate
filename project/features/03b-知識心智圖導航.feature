@ignore @query
Feature: 知識心智圖 API 測試規格（節點查詢、教練對話與付費牆）

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                | 訂閱方案      |
      | 1        | free@example.com     | FREE          |
      | 2        | pro@example.com      | PRO_199       |
      | 3        | proplus@example.com  | PRO_PLUS_399  |
    And 系統中有以下備考科目：
      | 科目 ID | 名稱     |
      | 1       | AWS SAA  |
      | 2       | PMP      |
    And 使用者 "pro@example.com" 備考 "AWS SAA" 與 "PMP"
    And 科目 "AWS SAA" 下有以下知識節點：
      | 節點 ID | 名稱         | 來源資源     | 來源頁碼 | 來源時間戳 | 答對率 | 掌握顏色 |
      | 101     | S3 儲存服務  | aws-guide.pdf| 12       | null       | 85     | green    |
      | 102     | EC2 運算邏輯 | aws-video    | null     | 512        | 30     | red      |
      | 103     | IAM 管理     | aws-guide.pdf| 45       | null       | 0      | gray     |

  # ========== 學科切換 ==========

  Rule: 前置（導航）- 學科切換器應過濾對應科目的知識節點樹

    Example: 切換至 AWS SAA 後心智圖顯示對應節點
      When 使用者 "pro@example.com" 在知識心智圖頁面選擇科目 "AWS SAA"
      Then 操作成功
      And 心智圖應顯示 AWS SAA 的知識節點：
        | 節點 ID | 名稱         |
        | 101     | S3 儲存服務  |
        | 102     | EC2 運算邏輯 |
        | 103     | IAM 管理     |
      And 心智圖不應包含 PMP 科目的節點

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 使用者只能瀏覽自己備考科目的知識節點

    Example: 查看非自己備考科目的節點失敗
      Given 使用者 "free@example.com" 僅備考 "PMP"
      When 使用者 "free@example.com" 查看科目 "AWS SAA" 的知識節點樹
      Then 操作失敗，錯誤為「您尚未加入此備考科目」

  Rule: 前置（參數）- 查看節點溯源必須提供有效的節點 ID

    Example: 查看不存在的節點溯源失敗
      When 使用者 "pro@example.com" 查看節點 999 的溯源內容
      Then 操作失敗，錯誤為「知識節點不存在」

  # ========== 頁面佈局 ==========

  Rule: 後置（回應）- 頁面應採非對稱佈局，左側 75% 教練面板、右側 25% 心智圖導航

    Example: 進入知識心智圖頁面取得佈局資料
      When 使用者 "pro@example.com" 進入知識心智圖頁面
      Then 操作成功
      And 回應應包含：
        | 區塊          | 寬度比例 | 內容                      |
        | coach_panel   | 75%      | AI 教練對話區與溯源內容    |
        | mind_map_nav  | 25%      | 互動知識節點樹             |

  # ========== 節點點擊聯動 ==========

  Rule: 後置（回應）- 點擊知識節點應回傳溯源內容至教練面板

    Example: 點擊 PDF 類知識節點取得頁碼溯源
      When 使用者 "pro@example.com" 點擊知識節點 101
      Then 操作成功
      And 教練面板應顯示溯源資訊：
        | 欄位           | 值            |
        | node_name      | S3 儲存服務   |
        | source_type    | pdf           |
        | source_ref     | 第 12 頁      |
      And 教練面板應以 Markdown 格式顯示該節點萃取的原文重點

    Example: 點擊 YouTube 類知識節點取得時間戳溯源
      When 使用者 "pro@example.com" 點擊知識節點 102
      Then 操作成功
      And 教練面板應顯示溯源資訊：
        | 欄位           | 值              |
        | node_name      | EC2 運算邏輯    |
        | source_type    | youtube         |
        | source_ref     | 00:08:32        |

  # ========== AI 教練付費牆 ==========

  Rule: 後置（回應）- FREE 用戶在教練對話框有單節點 3 次追問限制

    Example: FREE 用戶第 4 次追問同一節點時被鎖定
      Given 使用者 "free@example.com" 已在節點 101 追問 3 次
      When 使用者 "free@example.com" 在節點 101 的教練對話框輸入第 4 次提問
      Then 操作失敗，錯誤為「已達免費追問上限，升級 PRO_PLUS 解鎖無限對話」

  Rule: 後置（回應）- PRO_199 用戶嘗試使用高階教練對話時應顯示付費牆

    Example: PRO 用戶在教練對話框輸入時觸發毛玻璃鎖定
      When 使用者 "pro@example.com" 在節點 102 的教練對話框輸入 "請用簡單的例子教我這段"
      Then 操作失敗，錯誤為「AI 教練深度對話為 PRO_PLUS 專屬功能」
      And 回應應包含升級提示：
        | 欄位         | 值                              |
        | target_plan  | PRO_PLUS_399                    |
        | message      | 解鎖 Claude 3.5 終極教練         |

  Rule: 後置（回應）- PRO_PLUS 用戶可使用高階教練並扣除月度額度

    Example: PRO_PLUS 用戶成功與 AI 教練對話
      Given 使用者 "proplus@example.com" 本月高階教練剩餘額度為 50
      When 使用者 "proplus@example.com" 在節點 102 的教練對話框輸入 "EC2 的 Auto Scaling 為什麼觸發條件結果不同？"
      Then 操作成功
      And 回應應以串流方式輸出 AI 教練回覆
      And 使用者 "proplus@example.com" 的高階教練剩餘額度應為 49
      And 回應應標示使用模型為 "claude-3.5-sonnet"

  # ========== 節點掌握度顏色 ==========

  Rule: 後置（回應）- 知識節點應依答對率顯示紅綠燈顏色

    Example: 查看節點樹時每個節點顯示對應掌握顏色
      When 使用者 "pro@example.com" 查看科目 "AWS SAA" 的知識節點樹
      Then 操作成功
      And 節點應依答對率顯示顏色：
        | 節點 ID | 名稱         | 答對率 | 顏色   |
        | 101     | S3 儲存服務  | 85     | green  |
        | 102     | EC2 運算邏輯 | 30     | red    |
        | 103     | IAM 管理     | 0      | gray   |
      And 顏色規則為：green >= 80、orange 60-79、red < 60、gray 未作答
