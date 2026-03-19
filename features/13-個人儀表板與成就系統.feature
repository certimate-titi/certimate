Feature: 個人儀表板與成就系統

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | alice@example.com  | FREE     |

  Rule: 前置（狀態）- 登入後首頁預設為個人儀表板
    
    Example: 登入後系統載入儀表板首頁
      When 使用者 "alice@example.com" 成功登入系統
      Then 系統應導向至 "個人儀表板首頁"

  Rule: 後置（狀態）- 儀表板應顯示核心學習狀態與組件
  
    Example: 儀表板正確顯示雷達圖與組件
      When 使用者 "alice@example.com" 瀏覽 "個人儀表板首頁"
      Then 畫面應顯示即將到來的考試倒數計時
      And 畫面應顯示能力分布雷達圖
      And 畫面應顯示「快速上傳區」與「待辦提醒」

  Rule: 後置（狀態）- 每日登入與學習行為觸發連勝火焰 (Streaks)

    Example: 連續多日登入並進行學習可累積連勝火焰
      Given 使用者 "alice@example.com" 已經累積 2 天連勝
      When 使用者 "alice@example.com" 在隔日登入系統並完成一次測驗
      Then 其連勝火焰應更新為 3 天
      And 系統應顯示包含連勝達成動畫的通知

    Example: 連勝中斷保護機制免除歸零
      Given 使用者 "alice@example.com" 擁有 3 天連勝且擁有「免費凍結」額度
      When 使用者 "alice@example.com" 整天未登入
      Then 隔日登入時連勝火焰不應歸零
      And 系統應消耗一次凍結額度並顯示溫馨提示 "休息也是學習的一部分，歡迎回來 🤗"

  Rule: 後置（狀態）- 每日動態產生微任務 (Daily Quests)

    Example: 系統自動派發每日微任務
      When 使用者 "alice@example.com" 每日首次登入
      Then 系統應產生 1 到 3 個動態學習微任務（如：複習錯題 5 題）
      And 任務介面應暗示完成後可獲得經驗值或解鎖進度

  Rule: 後置（狀態）- 達成特定條件時頒發成就徽章 (Badges)

    Example: 首次上傳資源獲得徽章
      When 使用者 "alice@example.com" 首次成功上傳一份測驗資源
      Then 系統應觸發全螢幕慶祝動畫
      And 使用者應獲得 "🌱 播種者" 徽章
      And 畫面顯示訊息獎勵其踏出第一步
