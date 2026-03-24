Feature: 社群歸屬與主動關懷

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | alice@example.com  | FREE     |
      | 2        | bob@example.com    | PRO      |
      | 3        | ultra@example.com  | ULTRA    |
    
  Rule: 後置（狀態）- 針對 ULTRA 用戶顯示匿名學習夥伴以強化歸屬感

    Example: ULTRA 用戶在儀表板可看見同時段活躍考生
      When 使用者 "ultra@example.com" 瀏覽 "個人儀表板首頁"
      Then 畫面應顯示不包含個資的橫幅，例如 "目前有 368 位考生正一起奮鬥"
      And 使用者 "alice@example.com" 不應看到此橫幅

  Rule: 後置（狀態）- 定期產生並向使用者遞送個人化學習報告

    Example: 自動為活躍用戶生成週報
      When 系統觸發每週學習報告生成排程
      Then 系統應產生包含「學習時數」、「進步點」與「AI 總評」的週報
      And 報告數據應只與該用戶自己的歷史做比較
      And 儀表板或個人空間應記錄對應的「成長時間軸」里程碑節點

  Rule: 後置（狀態）- 系統主動偵測學習低谷並發送溫暖喚回或輔導訊息

    Example: 偵測到超過指定天數未登入時發起喚回
      Given 使用者 "alice@example.com" 已經超過 3 天未登入
      When 系統執行低谷偵測排程
      Then 系統應發送站外通知 (Email 或 Push Notification)
      And 通知文案語氣應為溫馨風格，例如 "最近忙嗎？Certi 等你回來，隨時可以繼續 💛"

    Example: 偵測到反覆卡關或成績連續退步時由 AI 主動出擊
      Given 使用者 "bob@example.com" 連續 2 回測驗成績明顯下滑
      When 使用者 "bob@example.com" 瀏覽測驗結果或儀表板
      Then AI 教練（Certi）應主動彈出對話視窗提供安慰
      And AI 教練應給出切換學習策略的實質建議
