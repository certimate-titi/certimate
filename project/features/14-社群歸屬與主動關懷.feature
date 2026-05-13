@frontend @command
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

  # ========== 週報生成 ==========
  # 註：「共同備考夥伴」橫幅功能已於 2026-04-27 由 CEO 簽核移除（CEO 簽核 B 路徑）。
  # 原 Rule 改為：儀表板不顯示活躍考生橫幅。
  # 對側 backend feature 同步刪除，並保留 step 實作為 deprecated（向後相容）。

  Rule: 前置（狀態）- 儀表板不顯示活躍考生橫幅（功能已下架）

    Example: 任何方案使用者均不顯示活躍考生橫幅
      When 使用者 "alice@example.com" 瀏覽個人儀表板首頁
      Then 操作成功
      And 頁面不應包含「共同備考夥伴」橫幅區塊


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

  # ========== 週報 Email 寄送 ==========

  Rule: 後置（狀態）- 週報生成後應自動寄送 Email 至使用者信箱

    Example: 活躍用戶收到週報 Email
      Given 使用者 "bob@example.com" 在本週有學習活動
      When 系統觸發每週學習報告生成排程
      Then 系統應寄送週報 Email 至 "bob@example.com"
      And Email 標題應包含「學習週報」
      And Email 內容應包含學習時數、完成考試數與 AI 生成摘要
      And Email 應包含「回到平台繼續學習」的 CTA 連結

    Example: 本週無活動的用戶不寄送週報 Email
      Given 使用者 "alice@example.com" 本週無任何學習活動
      When 系統觸發每週學習報告生成排程
      Then 系統不應寄送 Email 至 "alice@example.com"

  Rule: 後置（回應）- 使用者可在平台內查看歷史週報列表

    Example: 查看歷史週報列表
      Given 使用者 "bob@example.com" 有 3 份歷史週報
      When 使用者 "bob@example.com" 查看週報列表
      Then 操作成功
      And 回應應包含 3 份週報
      And 每份週報應包含：
        | 欄位               | 說明              |
        | week_start         | 週報起始日期      |
        | week_end           | 週報結束日期      |
        | study_hours        | 學習時數          |
        | exams_completed    | 完成考試數        |
        | progress_summary   | AI 生成的進步摘要 |

    Example: 週報列表為空時顯示引導說明
      Given 使用者 "alice@example.com" 尚無任何歷史週報
      When 使用者 "alice@example.com" 查看週報列表
      Then 操作成功
      And 頁面應顯示「尚無週報」標題
      And 頁面應說明「活躍用戶（每週至少做 1 份測驗）會在週日自動收到報告」

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
