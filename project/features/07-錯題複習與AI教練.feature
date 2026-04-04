@ignore @query
Feature: 錯題複習與 AI 教練

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email               | 訂閱方案      |
      | 1        | free@example.com    | FREE          |
      | 2        | pro@example.com     | PRO_199       |
      | 3        | ultra@example.com   | ULTRA_1599    |
    And 系統中有以下測驗與錯題記錄：
      | 測驗 ID | 使用者 ID | 狀態      | 科目    |
      | 1       | 1        | SUBMITTED | AWS SAA |
      | 2       | 2        | SUBMITTED | AWS SAA |
      | 3       | 3        | SUBMITTED | PMP     |
    And 測驗 1 包含以下錯題：
      | 題目 ID | 題目內容                          | 正確答案 | 使用者選擇 | 知識節點     |
      | 101     | S3 的版本控制功能預設為何？        | B        | C          | S3 儲存服務  |
      | 102     | IAM Policy 的評估順序為何？        | A        | D          | IAM 身分管理 |
    And 測驗 2 包含以下錯題：
      | 題目 ID | 題目內容                          | 正確答案 | 使用者選擇 | 知識節點     |
      | 201     | EC2 Auto Scaling 的觸發條件為何？ | C        | A          | EC2 運算服務 |

  # ========== 學科切換 ==========

  Rule: 前置（導航）- 學科切換器應過濾對應科目的錯題

    Example: 切換學科後錯題列表僅顯示該科目
      When 使用者 "free@example.com" 在錯題複習頁面選擇科目 "AWS SAA"
      Then 操作成功
      And 錯題列表應僅包含 AWS SAA 科目的錯題

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 只能查看自己測驗的錯題記錄

    Example: 查看其他使用者的錯題記錄失敗
      When 使用者 "free@example.com" 查看測驗 2 的錯題記錄
      Then 操作失敗，錯誤為「無存取此錯題記錄的權限」

  Rule: 前置（參數）- 查看錯題解析必須提供有效的題目 ID

    Example: 查看不存在的題目解析失敗
      When 使用者 "free@example.com" 查看測驗 1 題目 999 的解析
      Then 操作失敗，錯誤為「題目不存在」

  # ========== FREE 用戶解析 ==========

  Rule: 後置（回應）- FREE 用戶查看錯題解析應取得基本資訊與升級提示

    Example: FREE 用戶查看錯題取得簡短提示與毛玻璃遮罩
      When 使用者 "free@example.com" 查看測驗 1 題目 101 的解析
      Then 操作成功
      And 回應應包含基本資訊：
        | 欄位     | 值                            |
        | question | S3 的版本控制功能預設為何？   |
        | correct  | B                             |
        | selected | C                             |
        | tip      | S3 版本控制預設為停用狀態。   |
      And 回應應標記深度解析區為鎖定狀態
      And 回應應包含升級提示：
        | 欄位         | 值        |
        | target_plan  | PRO_199   |
        | monthly_fee  | 199       |

  # ========== PRO+ 用戶解析 ==========

  Rule: 後置（回應）- PRO 以上用戶查看錯題解析應取得完整 Markdown 解析與溯源引用

    Example: PRO 用戶查看錯題取得完整解析內容
      When 使用者 "pro@example.com" 查看測驗 2 題目 201 的解析
      Then 操作成功
      And 回應應包含完整的 Markdown 格式深度解析（非空白）
      And 回應應包含溯源引用：
        | 欄位             | 範例值                       |
        | source_resource  | 關聯資源名稱                 |
        | source_ref       | 頁碼或影片時間戳             |

  # ========== AI 教練對話 ==========

  Rule: 前置（狀態）- FREE 用戶不可使用 AI 教練對話

    Example: FREE 用戶嘗試向 AI 教練提問失敗
      When 使用者 "free@example.com" 在測驗 1 題目 101 的 AI 教練視窗輸入 "為什麼答案是 B？"
      Then 操作失敗，錯誤為「AI 教練對話為 PRO 以上方案專屬功能」

  Rule: 後置（回應）- PRO 以上用戶可向 AI 教練提問且回應以串流方式輸出

    Example: PRO 用戶成功與 AI 教練對話取得串流回應
      When 使用者 "pro@example.com" 在測驗 2 題目 201 的 AI 教練視窗輸入 "我還是不懂觸發條件的判斷邏輯"
      Then 操作成功
      And 回應應以串流方式輸出
      And AI 教練回覆應包含與題目 201 相關的解釋內容
      And AI 教練回覆語氣應帶有鼓勵性（非冷冰冰的條列式）

  Rule: 後置（個人化）- AI 教練應根據使用者的年齡、學歷與職業調整回覆方式

    Example: 高中學歷使用者收到淺顯易懂的比喻式回覆
      Given 使用者 "pro@example.com" 的個人資料為：
        | 欄位     | 值          |
        | 年齡     | 18          |
        | 最高學歷 | 高中 / 高職 |
        | 職業     | 學生        |
      When 使用者 "pro@example.com" 在 AI 教練視窗輸入 "什麼是 Auto Scaling？"
      Then AI 教練回覆應使用生活化比喻（例如「像是餐廳在尖峰時段自動增加服務生」）
      And AI 教練回覆不應假設使用者具備進階技術背景知識

    Example: 碩士學歷且具技術背景的使用者收到精準技術回覆
      Given 使用者 "ultra@example.com" 的個人資料為：
        | 欄位     | 值           |
        | 年齡     | 30           |
        | 最高學歷 | 碩士         |
        | 職業     | 軟體工程師   |
      When 使用者 "ultra@example.com" 在 AI 教練視窗輸入 "Auto Scaling 的觸發機制？"
      Then AI 教練回覆應直接使用技術術語（如 CloudWatch Alarm、Target Tracking Policy）
      And AI 教練回覆可引用 API 參數或 CLI 指令作為補充

    Example: 使用者未填寫個人資料時 AI 教練使用通用語氣
      Given 使用者 "pro@example.com" 的個人資料中年齡與學歷皆為空
      When 使用者 "pro@example.com" 在 AI 教練視窗提問
      Then AI 教練應使用中等難度的通用說明方式（預設大學程度）

  Rule: 後置（回應）- AI 教練應能引用使用者過去的錯題歷史提供連貫指導

    Example: AI 教練引用歷史錯題提供上下文感知回應
      Given 使用者 "pro@example.com" 過去曾在 EC2 相關題目答錯 3 次
      When 使用者 "pro@example.com" 在測驗 2 題目 201 的 AI 教練視窗輸入 "我 EC2 這塊一直搞不清楚"
      Then 操作成功
      And AI 教練回覆應提及使用者在 EC2 相關題目的歷史錯誤模式

  # ========== ULTRA 專屬：進階 AI 教練 ==========

  Rule: 後置（回應）- ULTRA 用戶可使用進階 AI 教練取得深度學習策略

    Example: ULTRA 用戶取得弱點突破策略與考前衝刺計畫
      When 使用者 "ultra@example.com" 請求進階 AI 教練分析
      Then 操作成功
      And 回應應包含弱點分析：
        | 欄位             | 說明                        |
        | weak_topics      | 掌握度最低的前 3 個知識節點 |
        | error_pattern    | 常見錯誤模式描述            |
      And 回應應包含突破策略：
        | 欄位             | 說明                        |
        | strategy         | 至少 1 條具體學習策略        |
        | recommended_quiz | 建議練習的題目範圍           |
      And 回應應包含考前衝刺計畫：
        | 欄位             | 說明                        |
        | daily_plan       | 每日建議學習內容（最多 7 天）|
        | focus_area       | 重點衝刺知識節點            |

    Example: 非 ULTRA 用戶請求進階 AI 教練失敗
      When 使用者 "pro@example.com" 請求進階 AI 教練分析
      Then 操作失敗，錯誤為「進階 AI 教練為 ULTRA 方案專屬功能」

  Rule: 後置（個人化）- 進階 AI 教練應根據學習歷程提供個人化建議

    Example: 有完整學習歷程的 ULTRA 用戶收到個人化建議
      Given 使用者 "ultra@example.com" 過去 30 天完成 12 次測驗
      And 使用者 "ultra@example.com" 的弱點節點為 "整合管理" 和 "範疇管理"
      When 使用者 "ultra@example.com" 請求進階 AI 教練分析
      Then 操作成功
      And 弱點分析應提及 "整合管理" 和 "範疇管理"
      And 突破策略應針對這兩個弱點節點

  # ========== 超綱防護 ==========

  Rule: 後置（回應）- 詢問超出題庫範圍的問題時應回覆範圍外提示

    Example: 詢問非題庫範圍的問題時顯示提示
      When 使用者 "pro@example.com" 在測驗 2 題目 201 的 AI 教練視窗輸入 "幫我寫一首詩"
      Then 操作成功
      And AI 教練回覆應包含「此問題超出目前題庫範圍」

  Rule: 後置（狀態）- 10 分鐘內超綱提問達 5 次後觸發 30 分鐘冷卻

    Example: 第 5 次超綱提問後 AI 教練進入冷卻
      Given 使用者 "pro@example.com" 在過去 10 分鐘內已提出 4 次超出範圍的問題
      When 使用者 "pro@example.com" 再次提出超出範圍的問題
      Then 操作成功
      And AI 教練回覆應包含冷卻提示：「您已暫時被限制使用 AI 教練，請 30 分鐘後再試」
      And 使用者 "pro@example.com" 在接下來 30 分鐘內的 AI 教練提問應被拒絕

  # ========== 免責聲明 ==========

  Rule: 後置（回應）- AI 教練介面必須顯示免責聲明

    Example: 開啟 AI 教練視窗時顯示免責文字
      When 使用者 "pro@example.com" 開啟 AI 教練對話視窗
      Then 操作成功
      And 介面應顯示免責聲明：「AI 生成內容僅供參考，請隨時自行查證重要資訊。」

  # ========== 錯題側邊列表切換 ==========

  Rule: 後置（互動）- 點擊錯題側邊列表中的題目可切換右側顯示內容

    @ignore
    Example: 錯題側邊列表點擊切換顯示題目
      Given 使用者 "free@example.com" 已進入測驗 1 的錯題複習頁面
      And 側邊列表顯示題目 101 與題目 102
      When 使用者在側邊列表點擊題目 102
      Then 右側解析區應切換顯示題目 102 的內容
      And 側邊列表中題目 102 應呈現選中狀態

  # ========== 答案對比顯示 ==========

  Rule: 後置（UI）- 錯題解析應同時顯示使用者錯誤答案與正確答案的對比

    @ignore
    Example: 使用者錯誤答案與正確答案對比顯示
      When 使用者 "free@example.com" 查看測驗 1 題目 101 的解析
      Then 操作成功
      And 解析區應以視覺對比方式顯示使用者選擇「C」與正確答案「B」
      And 正確答案應以綠色標示，錯誤答案應以紅色標示

  # ========== PRO_PLUS 引用來源切換 ==========

  Rule: 後置（互動）- PRO_PLUS 以上使用者可切換查看解析的引用來源

    @ignore
    Example: PRO_PLUS 使用者查看引用來源切換
      Given 使用者 "ultra@example.com" 查看測驗 3 的錯題解析
      When 使用者點擊「查看引用來源」切換按鈕
      Then 解析區應展開顯示該題的原始資源引用
      And 引用來源應包含資源名稱與對應的頁碼或時間戳
      When 使用者再次點擊「收合引用來源」
      Then 引用來源區塊應收合隱藏

  # ========== FREE 使用者毛玻璃遮罩 ==========

  Rule: 後置（UI）- FREE 使用者的深度解說區應以毛玻璃遮罩遮擋內容

    @ignore
    Example: FREE 使用者解說區毛玻璃遮罩遮擋內容
      When 使用者 "free@example.com" 查看測驗 1 題目 101 的解析
      Then 操作成功
      And 深度解說區應以毛玻璃（高斯模糊）效果遮擋完整內容
      And 遮罩上方應顯示「升級至 PRO_199 解鎖完整解析」的升級按鈕

  # ========== PRO_199 AI 聊天鎖定 ==========

  Rule: 後置（商業漏斗）- PRO_199 使用者的 AI 聊天功能應鎖定並提示升級

    @ignore
    Example: PRO_199 使用者 AI 聊天鎖定提示升級
      When 使用者 "pro@example.com" 在錯題複習頁面嘗試開啟 AI 教練聊天
      Then AI 教練聊天區域應呈現鎖定狀態
      And 鎖定區域應顯示升級提示：「升級至 ULTRA_1599 方案以使用 AI 教練即時對話」

  # ========== 無錯題空狀態 ==========

  Rule: 後置（UI）- 當使用者無任何錯題時應顯示空狀態與回到儀表板連結

    @ignore
    Example: 無錯題時顯示回到儀表板連結
      Given 使用者 "ultra@example.com" 的所有測驗均無錯題記錄
      When 使用者 "ultra@example.com" 進入錯題複習頁面
      Then 頁面應顯示空狀態提示：「目前沒有錯題記錄，繼續保持！」
      And 頁面應顯示「回到儀表板」連結按鈕
      When 使用者點擊「回到儀表板」連結
      Then 頁面應導航至儀表板頁面
