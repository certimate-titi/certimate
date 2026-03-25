@ignore @query
Feature: 個人儀表板與成就系統

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 | Onboarding |
      | 1        | alice@example.com  | FREE     | true       |
    And 使用者 "alice@example.com" 備考以下科目：
      | 科目     | 考試日期   |
      | AWS SAA  | 2026-06-15 |
      | TOEIC    | 2026-09-01 |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 已完成 Onboarding 的用戶登入後預設導向儀表板

    Example: 登入後導向儀表板首頁
      When 使用者 "alice@example.com" 成功登入系統
      Then 系統應導向至個人儀表板首頁

  Rule: 前置（狀態）- 未完成 Onboarding 的用戶應導向引導頁

    Example: 未完成 Onboarding 的用戶被重新導向
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email             | 訂閱方案 | Onboarding |
        | 2        | new@example.com   | FREE     | false      |
      When 使用者 "new@example.com" 成功登入系統
      Then 系統應導向至 Onboarding 引導頁

  Rule: 前置（參數）- 儀表板查詢必須有至少一個備考科目

    Example: 無備考科目的用戶查看儀表板顯示引導
      Given 使用者 "alice@example.com" 尚未設定任何備考科目
      When 使用者 "alice@example.com" 查看儀表板
      Then 操作成功
      And 頁面應顯示「請至少新增一個備考科目」引導提示

  # ========== 科目切換器 ==========

  Rule: 後置（回應）- 儀表板應顯示科目切換器與核心學習組件

    Example: 備考多科時顯示科目切換器
      When 使用者 "alice@example.com" 查看儀表板
      Then 操作成功
      And 科目切換器應包含：
        | 科目    |
        | AWS SAA |
        | TOEIC   |
      And 頁面應顯示「+ 新增備考科目」入口
      And 預設顯示 "AWS SAA" 的學習數據

    Example: 切換科目後儀表板數據更新
      Given 使用者 "alice@example.com" 目前在儀表板檢視 "AWS SAA"
      When 使用者 "alice@example.com" 切換至 "TOEIC"
      Then 操作成功
      And 回應中的考試倒數應對應 "TOEIC" 的考試日期 2026-09-01
      And 回應中的雷達圖應對應 "TOEIC" 的能力分布

  Rule: 後置（回應）- 儀表板應包含考試倒數、雷達圖、快速上傳區與待辦提醒

    Example: 查看儀表板取得完整組件資料
      When 使用者 "alice@example.com" 查看儀表板，科目為 "AWS SAA"
      Then 操作成功
      And 回應應包含以下組件：
        | 組件              | 說明                         |
        | exam_countdown    | 距考試日期剩餘天數           |
        | radar_chart       | 各知識節點的能力分布         |
        | quick_upload      | 快速上傳資源入口             |
        | todo_reminders    | 待複習錯題與未完成考卷       |

  # ========== 連勝火焰 ==========

  Rule: 後置（狀態）- 每日登入並學習應累積連勝天數

    Example: 連續第 3 天登入並完成測驗後連勝更新
      Given 使用者 "alice@example.com" 目前連勝為 2 天
      When 使用者 "alice@example.com" 今日登入並完成一次測驗
      Then 使用者 "alice@example.com" 的連勝應為 3 天

  Rule: 後置（狀態）- 連勝中斷時若有凍結額度應免除歸零

    Example: 未登入但有凍結額度保護連勝
      Given 使用者 "alice@example.com" 目前連勝為 3 天且擁有 1 次凍結額度
      When 使用者 "alice@example.com" 整天未登入
      Then 隔日登入時連勝應維持 3 天
      And 凍結額度應消耗為 0 次
      And 系統應顯示提示：「休息也是學習的一部分，歡迎回來」

    Example: 未登入且無凍結額度時連勝歸零
      Given 使用者 "alice@example.com" 目前連勝為 5 天且凍結額度為 0 次
      When 使用者 "alice@example.com" 整天未登入
      Then 隔日登入時連勝應歸零為 0 天

  # ========== 每日微任務 ==========

  Rule: 後置（狀態）- 每日首次登入應自動產生 1-3 個微任務

    Example: 登入後收到每日微任務
      When 使用者 "alice@example.com" 今日首次登入
      Then 系統應產生 1 至 3 個每日微任務
      And 每個任務應包含：
        | 欄位         | 說明                    |
        | quest_type   | quiz / explore / review |
        | description  | 任務描述                |
        | xp_reward    | 完成可獲得的 XP         |
        | status       | pending                 |

  Rule: 後置（狀態）- 任務完成由系統事件自動觸發，不接受手動完成

    Example: 完成測驗後系統自動標記 quiz 任務為完成
      Given 使用者 "alice@example.com" 有一個類型為 "quiz" 的任務「完成一份 15 題測驗」，狀態為 "pending"
      When 使用者 "alice@example.com" 完成一份 15 題的測驗
      Then 該任務狀態應更新為 "completed"
      And 使用者 "alice@example.com" 應獲得對應的 XP 獎勵

    Example: 嘗試透過 API 手動完成任務被拒絕
      Given 使用者 "alice@example.com" 有一個未完成的每日任務 ID 為 1
      When 使用者 "alice@example.com" 嘗試手動完成任務 1
      Then 操作失敗，錯誤為「任務完成狀態由系統自動判定，不接受手動更新」

  # ========== 成就徽章 ==========

  Rule: 後置（狀態）- 達成特定里程碑時應頒發成就徽章

    Example: 首次上傳資源獲得播種者徽章
      When 使用者 "alice@example.com" 首次成功上傳一份資源
      Then 使用者 "alice@example.com" 應獲得成就徽章：
        | 欄位   | 值           |
        | key    | first_upload |
        | name   | 播種者       |
      And 系統應觸發全螢幕慶祝動畫

    Example: 連勝達 7 天獲得堅持不懈徽章
      Given 使用者 "alice@example.com" 目前連勝為 6 天
      When 使用者 "alice@example.com" 今日登入並完成學習
      Then 使用者 "alice@example.com" 應獲得成就徽章：
        | 欄位   | 值         |
        | key    | streak_7   |
        | name   | 堅持不懈   |

  # ========== 個人資料 ==========

  Rule: 後置（狀態）- 編輯個人資料應更新顯示名稱與 AI 教練參考資訊

    Example: 更新個人資料成功
      When 使用者 "alice@example.com" 更新個人資料：
        | 欄位         | 值           |
        | display_name | 愛麗絲       |
        | age          | 28           |
        | education    | 資訊工程碩士 |
        | career       | 軟體開發     |
      Then 操作成功
      And 使用者 "alice@example.com" 的顯示名稱應為 "愛麗絲"

  Rule: 後置（狀態）- 上傳頭像後應全站同步更新

    Example: 更新頭像成功
      When 使用者 "alice@example.com" 上傳新頭像
      Then 操作成功
      And 回應應包含新頭像的 URL
