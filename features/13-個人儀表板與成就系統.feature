Feature: 個人儀表板與成就系統

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | alice@example.com  | FREE     |

  Rule: 前置（狀態）- 登入後首頁預設為個人儀表板
    
    Example: 登入後系統載入儀表板首頁
      When 使用者 "alice@example.com" 成功登入系統
      Then 系統應導向至 "個人儀表板首頁"

  Rule: 後置（狀態）- 儀表板應顯示科目切換器與核心學習狀態組件

    Example: 備考多科時儀表板顯示科目切換器
      Given 使用者 "alice@example.com" 目前備考 "AWS SAA" 和 "TOEIC"
      When 使用者 "alice@example.com" 瀏覽 "個人儀表板首頁"
      Then 畫面頂部應顯示科目切換器，包含 "AWS SAA" 與 "TOEIC" 選項
      And 畫面應顯示「+ 新增備考科目」入口
      And 預設顯示第一個科目的學習數據

    Example: 切換科目後儀表板數據對應更新
      Given 使用者 "alice@example.com" 目前在儀表板檢視 "AWS SAA" 的數據
      When 使用者切換至 "TOEIC"
      Then 學習狀態區的考試倒數、答對率、雷達圖應更新為 "TOEIC" 的數據
      And 待辦提醒應對應 "TOEIC" 的錯題與未完成考卷

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

    # 任務完成狀態由系統根據使用者行為事件自動判斷，前端不提供手動勾選入口。
    # 可觸發完成的事件類型：完成一次測驗 (quiz)、瀏覽知識節點 (explore)、完成錯題複習 (review)

    Example: 系統自動派發每日微任務
      When 使用者 "alice@example.com" 每日首次登入
      Then 系統應產生 1 到 3 個動態學習微任務（如：複習錯題 5 題）
      And 任務介面應暗示完成後可獲得經驗值或解鎖進度
      And 任務項目不應提供手動勾選完成的操作入口

    Example: 完成對應學習行為後系統自動將任務標記為完成
      Given 使用者 "alice@example.com" 有一個類型為 "quiz" 的每日任務「完成一份 15 題的快速測驗」
      And 該任務狀態為 "未完成"
      When 使用者 "alice@example.com" 完成一份包含 15 題的測驗
      Then 系統應自動將該任務標記為 "已完成"
      And 系統應發放對應的 XP 獎勵至使用者帳號
      And 前端任務卡片應顯示打勾完成動畫

    Example: 使用者嘗試透過 API 手動完成任務應被拒絕
      Given 使用者 "alice@example.com" 有一個類型為 "review" 的每日任務尚未完成
      When 使用者 "alice@example.com" 直接呼叫 POST /daily-quests/{id}/complete
      Then 操作失敗
      And 錯誤訊息應為 "任務完成狀態由系統自動判定，不接受手動更新"

  Rule: 後置（狀態）- 達成特定條件時頒發成就徽章 (Badges)

    Example: 首次上傳資源獲得徽章
      When 使用者 "alice@example.com" 首次成功上傳一份測驗資源
      Then 系統應觸發全螢幕慶祝動畫
      And 使用者應獲得 "🌱 播種者" 徽章
      And 畫面顯示訊息獎勵其踏出第一步

  Rule: 前/後置（狀態）- 個人資料設定與編輯（包含 AI 教練輔助用之背景資訊）

    Example: 編輯個人資料與 AI 教練參考資訊（年齡、學歷等）
      When 使用者 "alice@example.com" 編輯個人資料，更新以下資訊：
        | 欄位       | 更新值           |
        | 顯示名稱   | 愛麗絲           |
        | 年齡       | 28              |
        | 學歷/科系  | 資訊工程碩士      |
        | 職業領域   | 軟體開發         |
      Then 操作成功
      And 前端個人狀態中的名稱應更新為 "愛麗絲"
      And 系統應儲存年齡、學歷、職業領域等資訊，以便 AI 後續在產生考題或回答問題時能依此推導出更符合其能力範圍的說明與挑戰

    Example: 更新個人頭像 (Avatar)
      When 使用者 "alice@example.com" 上傳並更新頭像圖片
      Then 操作成功
      And 後端應回傳新頭像的圖檔位址
      And 前端各處的頭像顯示應立即對應更新
