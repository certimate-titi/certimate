@command
Feature: 節點練習模式

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | alice@example.com  | PRO_199  |
    And 使用者 "alice@example.com" 備考科目為 "AWS SAA"（科目 ID: 1）
    And 科目 "AWS SAA" 有以下知識節點：
      | 節點名稱   | 節點 ID | 父節點 ID | 深度 |
      | 運算       | N1     |           | 0    |
      | EC2        | N2     | N1        | 1    |
      | Lambda     | N3     | N1        | 1    |
    And 知識節點 "EC2" 有以下練習題：
      | 題目 ID | 題目內容                          | 選項A         | 選項B           | 選項C          | 選項D         | 正確答案 | 詳解                   |
      | Q1     | EC2 執行個體類型中，哪一個適合記憶體密集型工作負載？ | t3.micro     | r5.xlarge       | c5.large      | m5.large     | B       | R 系列針對記憶體最佳化     |
      | Q2     | EC2 的自動擴展群組最少需要幾個執行個體？        | 0            | 1               | 2             | 3            | A       | 最少可設為 0 個          |
    And 知識節點 "Lambda" 有以下練習題：
      | 題目 ID | 題目內容                      | 選項A     | 選項B     | 選項C      | 選項D       | 正確答案 | 詳解                    |
      | Q3     | Lambda 函數的最長執行時間為何？   | 5 分鐘    | 10 分鐘   | 15 分鐘    | 30 分鐘     | C       | Lambda 上限為 15 分鐘    |

  # ========== 節點題目列表 ==========

  Rule: 後置（查詢）- 使用者可查詢知識節點下的練習題

    Example: 查詢節點練習題列表
      When 使用者 "alice@example.com" 查詢節點 "EC2" 的練習題
      Then 操作成功
      And 回應應包含 2 道練習題

    Example: 查詢無題目的節點回傳空列表
      When 使用者 "alice@example.com" 查詢節點 "運算" 的練習題
      Then 操作成功
      And 回應應包含 0 道練習題

  # ========== 練習作答 ==========

  Rule: 後置（狀態）- 練習答對後即時回傳正確答案與詳解並更新進度

    Example: 練習答對後即時回饋與進度更新
      When 使用者 "alice@example.com" 練習作答題目 "Q1"，選擇 "B"
      Then 操作成功
      And 作答結果為正確
      And 回應應包含正確答案 "B"
      And 回應應包含詳解
      And 節點 "EC2" 的進度應已更新

  Rule: 後置（狀態）- 練習答錯後即時回傳正確答案與詳解並更新進度

    Example: 練習答錯後即時回饋
      When 使用者 "alice@example.com" 練習作答題目 "Q1"，選擇 "A"
      Then 操作成功
      And 作答結果為錯誤
      And 回應應包含正確答案 "B"
      And 回應應包含詳解

  # ========== 進度傳播 ==========

  Rule: 後置（狀態）- 練習作答後進度向上傳播至父節點

    Example: 子節點作答後父節點進度更新
      When 使用者 "alice@example.com" 練習作答題目 "Q1"，選擇 "B"
      Then 操作成功
      And 父節點 "運算" 的進度應已傳播更新

  # ========== 不存在的題目 ==========

  Rule: 前置（參數）- 作答不存在的題目應回傳 404

    Example: 作答不存在的題目回傳錯誤
      When 使用者 "alice@example.com" 練習作答不存在的題目
      Then 操作失敗，錯誤為「題目不存在」

  # ========== 入口導航（前端行為） ==========

  Rule: 前置（導航）- 從知識節點詳情面板點「練習」應直達該節點的練習題

    Example: 有題目時直接進入作答畫面
      Given 使用者 "alice@example.com" 在 "/knowledge" 頁面選取知識節點 "EC2"
      When 使用者點擊節點詳情的「練習」按鈕
      Then 頁面應導向 "/practice?nodeId=N2&nodeName=EC2"
      And 練習頁面應自動載入 "EC2" 的練習題並進入作答畫面
      And 不應顯示「選擇知識節點開始練習」的節點列表

    Example: 節點無題目時顯示專屬空態而非回退至節點列表
      Given 使用者 "alice@example.com" 在 "/knowledge" 頁面選取知識節點 "運算"
      When 使用者點擊節點詳情的「練習」按鈕
      Then 頁面應導向 "/practice?nodeId=N1&nodeName=運算"
      And 練習頁面應顯示「「運算」尚無練習題」的空態訊息
      And 空態應提供「選擇其他節點」與「回知識圖譜」兩個操作
      And 不應靜默回退至節點列表

  Rule: 前置（入口）- /practice 保留作為可直接造訪的節點選擇入口

    Example: 無 nodeId 參數時顯示節點選擇列表
      Given 使用者 "alice@example.com" 直接造訪 "/practice"（未帶 nodeId）
      Then 頁面應顯示「選擇知識節點開始練習」的葉節點列表
      And 每個節點卡片應顯示掌握度百分比徽章
      And 徽章顏色應依掌握度分級：綠色（已掌握）/ 黃色（待加強）/ 紅色（待努力）/ 灰色（未測）
