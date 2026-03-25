@ignore @command
Feature: 社群歸屬與主動關懷

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案      | 最後登入日      |
      | 1        | alice@example.com  | FREE          | 2026-03-20     |
      | 2        | bob@example.com    | PRO_199       | 2026-03-25     |
      | 3        | ultra@example.com  | ULTRA_1599    | 2026-03-25     |
    And 使用者 "bob@example.com" 最近三次測驗分數為：
      | 次序 | 分數 |
      | 1    | 75   |
      | 2    | 68   |
      | 3    | 55   |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 匿名活躍考生橫幅僅對 ULTRA 用戶顯示

    Example: FREE 用戶不應看到活躍考生橫幅
      When 使用者 "alice@example.com" 瀏覽個人儀表板首頁
      Then 操作成功
      And 頁面不應包含「共同備考夥伴」橫幅區塊

  Rule: 前置（參數）- 活躍考生統計不得包含任何個人識別資訊

    Example: 橫幅數字來自匿名統計不洩漏個資
      When 使用者 "ultra@example.com" 瀏覽個人儀表板首頁
      Then 操作成功
      And 頁面應顯示「共同備考夥伴」橫幅
      And 橫幅內容格式應為「目前有 N 位考生正一起奮鬥」，其中 N 為正整數
      And 橫幅不應包含任何 Email、姓名或使用者 ID

  # ========== 週報生成 ==========

  Rule: 後置（狀態）- 系統應每週自動為活躍用戶生成個人化週報

    Example: 活躍用戶收到包含具體數據的週報
      Given 使用者 "bob@example.com" 在本週有以下學習紀錄：
        | 學習時數 | 完成考試數 | 答題數 |
        | 8.5      | 3          | 120    |
      When 系統觸發每週學習報告生成排程
      Then 系統應為使用者 "bob@example.com" 生成週報，內容包含：
        | 欄位          | 值   |
        | study_hours   | 8.5  |
        | exams_completed | 3  |
        | questions_answered | 120 |
      And 週報應包含 AI 生成的進步摘要（非空白）
      And 週報數據僅與使用者自己的歷史比較，不含排名

    Example: 本週無活動的用戶不生成週報
      Given 使用者 "alice@example.com" 本週無任何學習活動
      When 系統觸發每週學習報告生成排程
      Then 系統不應為使用者 "alice@example.com" 生成週報

  # ========== 低谷偵測與喚回 ==========

  Rule: 後置（狀態）- 超過 3 天未登入時系統應發送溫暖喚回通知

    Example: 使用者超過 3 天未登入時收到喚回 Email
      Given 今日為 2026-03-25
      And 使用者 "alice@example.com" 的最後登入日為 2026-03-20
      When 系統執行低谷偵測排程
      Then 系統應發送 Email 通知至 "alice@example.com"
      And Email 標題應包含使用者顯示名稱
      And Email 語氣應為溫馨風格，不含施壓或貶低用語

    Example: 最後登入未超過 3 天的用戶不觸發喚回
      Given 今日為 2026-03-25
      And 使用者 "bob@example.com" 的最後登入日為 2026-03-25
      When 系統執行低谷偵測排程
      Then 系統不應發送喚回通知至 "bob@example.com"

  Rule: 後置（狀態）- 連續成績下滑時 AI 教練應主動提供支持

    Example: 連續 2 次成績下滑後 AI 教練主動出現
      Given 使用者 "bob@example.com" 連續 2 次測驗成績下滑（75 → 68 → 55）
      When 使用者 "bob@example.com" 瀏覽測驗結果頁面
      Then AI 教練（Certi）應主動顯示對話視窗
      And AI 教練的訊息應包含：
        | 內容類型     | 說明                           |
        | 情緒支持     | 鼓勵性文字，不含批評           |
        | 策略建議     | 至少一條具體的學習策略調整建議 |

    Example: 成績穩定或上升時 AI 教練不主動介入
      Given 使用者 "ultra@example.com" 最近三次測驗分數為 70、75、82
      When 使用者 "ultra@example.com" 瀏覽測驗結果頁面
      Then AI 教練不應主動顯示對話視窗
