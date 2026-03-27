Feature: 平台管理後台 — 權限驗證與用戶管理

  Background:
    Given 系統中有以下管理角色說明（僅文件用途）
    And 系統中有以下使用者帳號：
      | 使用者 ID | Email                   | 訂閱方案  | 角色        | 狀態    |
      | 1        | super@certimate.com     | ULTRA     | SUPER_ADMIN | active  |
      | 2        | ops@certimate.com       | ULTRA     | ADMIN       | active  |
      | 3        | org@school.com          | ULTRA     | ORG_ADMIN   | active  |
      | 4        | alice@example.com       | PRO       | USER        | active  |
      | 5        | bob@example.com         | FREE      | USER        | active  |
      | 6        | cooling@example.com     | PRO_PLUS  | USER        | cooling |

  # ========== 權限驗證 ==========

  Rule: 前置（狀態）- super_admin 與 admin 角色可存取管理後台

    Example: super_admin 進入管理後台成功
      When 使用者 "super@certimate.com" 存取管理後台
      Then 操作成功
      And 頁面應顯示營運儀表板

    Example: admin 進入管理後台成功但無系統設定選單
      When 使用者 "ops@certimate.com" 存取管理後台
      Then 操作成功
      And 頁面應顯示營運儀表板
      And 導航列不應包含「系統設定」選項

  Rule: 前置（狀態）- org_admin 與 user 角色不可存取管理後台

    Example: org_admin 存取管理後台被拒絕
      When 使用者 "org@school.com" 存取管理後台
      Then 操作失敗，錯誤為「權限不足，無法存取管理後台」

    Example: 一般用戶存取管理後台被拒絕
      When 使用者 "alice@example.com" 存取管理後台
      Then 操作失敗，錯誤為「權限不足，無法存取管理後台」

  Rule: 前置（狀態）- admin 角色不可存取系統設定

    Example: admin 存取系統設定頁被拒絕
      When 使用者 "ops@certimate.com" 存取管理後台系統設定頁
      Then 操作失敗，錯誤為「權限不足，僅 super_admin 可存取系統設定」

  # ========== 必要參數 ==========

  Rule: 前置（參數）- 管理後台操作必須提供必要參數

    Scenario Outline: 缺少 <缺少參數> 時操作失敗
      When 使用者 "super@certimate.com" 停權使用者帳號，使用者 ID 為 <使用者ID>，原因為 <原因>
      Then 操作失敗，錯誤為「必要參數未提供」

      Examples:
        | 缺少參數   | 使用者ID | 原因   |
        | 使用者 ID  |          | 違規   |
        | 原因       | 5        |        |

  # ========== 營運儀表板 ==========

  Rule: 後置（回應）- 營運儀表板應回傳六項核心 KPI

    Example: 查看營運儀表板取得 KPI 卡片資料
      When 使用者 "super@certimate.com" 查看營運儀表板
      Then 操作成功
      And 回應應包含以下 KPI 欄位：
        | 欄位                | 說明                |
        | dau                 | 今日活躍用戶數      |
        | mau                 | 月活躍用戶數        |
        | new_registrations   | 今日新註冊數        |
        | conversion_rate     | 免費轉付費比率      |
        | mrr                 | 月經常性收入（TWD） |
        | ai_token_today      | 今日 AI Token 消耗  |
        | queue_depth         | 當前任務佇列深度    |

  # ========== 用戶管理 ==========

  Rule: 後置（回應）- 用戶搜尋應支援 Email、方案與狀態篩選

    Example: 依 Email 搜尋用戶
      When 使用者 "ops@certimate.com" 搜尋用戶，關鍵字為 "alice"
      Then 操作成功
      And 回應應包含使用者 "alice@example.com" 的摘要資訊：
        | 欄位     | 值                |
        | email    | alice@example.com |
        | plan     | PRO               |
        | status   | active            |

    Example: 依訂閱方案篩選用戶
      When 使用者 "ops@certimate.com" 篩選用戶，方案為 "FREE"
      Then 操作成功
      And 回應中所有使用者的方案應為 "FREE"

  Rule: 後置（回應）- 用戶詳情頁應回傳六個資訊區塊

    Example: 查看用戶詳情頁取得完整資訊
      When 使用者 "ops@certimate.com" 查看使用者 5 的詳情
      Then 操作成功
      And 回應應包含以下區塊：
        | 區塊         | 內容說明                                  |
        | profile      | 顯示名稱、Email、角色、註冊日期           |
        | subscription | 當前方案、訂閱狀態、下次扣款日            |
        | behavior     | 最近登入時間、總登入次數、最後考試日期     |
        | token_usage  | 本月 AI Token 消耗量、剩餘額度            |
        | login_history| 最近 10 筆登入紀錄（時間、IP、裝置）       |
        | anomalies    | 冷卻紀錄、異常操作紀錄                    |

  Rule: 後置（狀態）- super_admin 手動調整用戶訂閱應即時生效

    Example: super_admin 將 FREE 用戶升級為 PRO 成功
      When 使用者 "super@certimate.com" 將使用者 5 的訂閱方案調整為 "PRO"，OTP 為 "123456"
      Then 操作成功
      And 使用者 5 的訂閱方案應為 "PRO"
      And 系統應記錄審計日誌：
        | 欄位     | 值                              |
        | admin_id | 1                               |
        | action   | adjust_subscription             |
        | target   | 使用者 5                         |
        | details  | FREE → PRO                      |

    Example: admin 角色無法調整訂閱
      When 使用者 "ops@certimate.com" 將使用者 5 的訂閱方案調整為 "PRO"，OTP 為 "123456"
      Then 操作失敗，錯誤為「權限不足，僅 super_admin 可調整訂閱」

  Rule: 後置（狀態）- 停權帳號應記錄原因並寫入審計日誌

    Example: 停權用戶帳號成功
      When 使用者 "ops@certimate.com" 停權使用者 5 的帳號，原因為 "違反使用條款"
      Then 操作成功
      And 使用者 5 的狀態應為 "suspended"
      And 系統應記錄審計日誌：
        | 欄位     | 值                   |
        | action   | suspend_user         |
        | target   | 使用者 5              |
        | details  | 違反使用條款          |

  Rule: 後置（回應）- 批量匯出應產生包含篩選結果的 CSV 檔案

    Example: 匯出 PRO 方案用戶 CSV
      When 使用者 "ops@certimate.com" 匯出用戶 CSV，篩選方案為 "PRO"
      Then 操作成功
      And 回應應為 CSV 檔案，包含欄位：email、display_name、plan、status、created_at
