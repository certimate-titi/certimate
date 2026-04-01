@command
Feature: 平台管理後台 — 權限驗證與用戶管理

  Background:
    Given 系統中有以下管理角色：
      | 角色代碼      | 權限範圍                                         |
      | super_admin  | 所有權限，包含管理員帳號 CRUD 與系統設定           |
      | admin        | 用戶管理、內容審核、財務檢視（唯讀系統設定除外）   |
      | org_admin    | 僅限自己機構的學生管理與派卷分析                   |
      | user         | 個人學習功能                                      |
    And 系統中有以下使用者帳號：
      | 使用者 ID | Email                   | 訂閱方案      | 角色         | 狀態   |
      | 1        | super@certimate.com     | ULTRA_1599    | super_admin  | active |
      | 2        | ops@certimate.com       | ULTRA_1599    | admin        | active |
      | 3        | org@school.com          | ULTRA_1599    | org_admin    | active |
      | 4        | alice@example.com       | PRO_199       | user         | active |
      | 5        | bob@example.com         | FREE          | user         | active |
      | 6        | cooling@example.com     | PRO_PLUS_399  | user         | cooling |

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

  Rule: 後置（回應）- 趨勢圖表應支援最長 90 天範圍

    Example: 查看 90 天用戶成長趨勢
      When 使用者 "super@certimate.com" 查看營運趨勢圖表，時間範圍為 "90d"
      Then 操作成功
      And 回應應包含 90 筆每日 DAU 與 MAU 資料點

  Rule: 後置（回應）- AI 成本分析應按模型分列消耗量

    Example: 查看 AI 成本分析取得各模型消耗
      When 使用者 "super@certimate.com" 查看 AI 成本分析
      Then 操作成功
      And 回應應包含以下模型的 Token 消耗量：
        | 模型               |
        | gemini-1.5-flash   |
        | claude-3.5-sonnet  |
        | gpt-4o             |

  Rule: 後置（狀態）- Worker 失敗率超過 5% 時應觸發異常警報

    Example: 失敗率超標時觸發紅色警報與 Email 通知
      Given 過去 1 小時 Worker 任務失敗率為 8%
      When 系統執行異常偵測排程
      Then 營運儀表板應顯示紅色警報卡片，內容為「Worker 失敗率異常：8%」
      And 系統應發送 Email 通知至所有 admin 與 super_admin

  # ========== 用戶管理 ==========

  Rule: 後置（回應）- 用戶搜尋應支援 Email、方案與狀態篩選

    Example: 依 Email 搜尋用戶
      When 使用者 "ops@certimate.com" 搜尋用戶，關鍵字為 "alice"
      Then 操作成功
      And 回應應包含使用者 "alice@example.com" 的摘要資訊：
        | 欄位     | 值            |
        | email    | alice@example.com |
        | plan     | PRO_199       |
        | status   | active        |

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

    Example: super_admin 將 FREE 用戶升級為 PRO_199 成功
      When 使用者 "super@certimate.com" 將使用者 5 的訂閱方案調整為 "PRO_199"，起始日期為 "2026-04-01"，結束日期為 "2026-07-01"
      Then 操作成功
      And 使用者 5 的訂閱方案應為 "PRO_199"
      And 系統應記錄審計日誌：
        | 欄位     | 值                              |
        | admin_id | 1                               |
        | action   | adjust_subscription             |
        | target   | 使用者 5                         |
        | details  | FREE → PRO_199                  |

    Example: admin 角色無法調整訂閱
      When 使用者 "ops@certimate.com" 將使用者 5 的訂閱方案調整為 "PRO_199"，起始日期為 "2026-04-01"，結束日期為 "2026-07-01"
      Then 操作失敗，錯誤為「權限不足，僅 super_admin 可調整訂閱」

  Rule: 後置（狀態）- 停權帳號應記錄原因並寫入審計日誌

    Example: 停權用戶帳號成功
      When 使用者 "ops@certimate.com" 停權使用者 5 的帳號，原因為 "違反使用條款"
      Then 操作成功
      And 使用者 5 的狀態應為 "suspended"
      And 使用者 "bob@example.com" 應無法登入系統
      And 系統應記錄審計日誌：
        | 欄位     | 值                   |
        | action   | suspend_user         |
        | target   | 使用者 5              |
        | details  | 違反使用條款          |

  Rule: 後置（狀態）- 恢復帳號應將狀態改回 active 並寫入審計日誌

    Example: 恢復用戶帳號成功
      Given 使用者 5 的狀態為 "suspended"
      When 使用者 "ops@certimate.com" 恢復使用者 5 的帳號
      Then 操作成功
      And 使用者 5 的狀態應為 "active"
      And 系統應記錄審計日誌：
        | 欄位     | 值                   |
        | action   | activate_user        |
        | target   | 使用者 5              |
        | details  | 恢復用戶帳號          |

  Rule: 後置（狀態）- super_admin 可調整用戶角色

    Example: super_admin 將一般用戶升級為 admin
      When 使用者 "super@certimate.com" 將使用者 5 的角色調整為 "admin"
      Then 操作成功
      And 使用者 5 的角色應為 "admin"
      And 系統應記錄審計日誌：
        | 欄位     | 值                   |
        | action   | adjust_role          |

  Rule: 後置（狀態）- super_admin 可刪除用戶帳號（需確認名稱）

    Example: 刪除用戶帳號成功（確認名稱正確）
      When 使用者 "super@certimate.com" 刪除使用者 5 的帳號，確認名稱為 "bob@example.com"
      Then 操作成功
      And 使用者 5 的狀態應為 "deleted"
      And 系統應記錄審計日誌：
        | 欄位     | 值                   |
        | action   | delete_user          |

    Example: 刪除用戶帳號失敗（確認名稱不符）
      When 使用者 "super@certimate.com" 刪除使用者 5 的帳號，確認名稱為 "wrong_name"
      Then 操作失敗，錯誤為「確認名稱不符，請輸入「bob@example.com」」

  Rule: 後置（狀態）- 管理員可發送通知給指定用戶

    Example: 發送通知給用戶成功
      When 使用者 "ops@certimate.com" 發送通知給使用者 5，訊息為 "您的帳號已恢復正常"
      Then 操作成功
      And 系統應記錄審計日誌：
        | 欄位     | 值                   |
        | action   | notify_user          |
        | target   | 使用者 5              |

    Example: 發送空白通知失敗
      When 使用者 "ops@certimate.com" 發送通知給使用者 5，訊息為 ""
      Then 操作失敗，錯誤為「通知訊息不可為空」

  Rule: 後置（回應）- 用戶搜尋應排除管理員角色

    Example: 用戶列表不包含管理員帳號
      When 使用者 "ops@certimate.com" 搜尋用戶，關鍵字為 ""
      Then 操作成功
      And 回應不應包含角色為 "admin" 或 "super_admin" 的使用者

  Rule: 後置（狀態）- super_admin 可透過 Email 調整用戶角色

    Example: 透過 Email 將一般用戶升級為管理員
      When 使用者 "super@certimate.com" 透過 Email "bob@example.com" 將角色調整為 "admin"
      Then 操作成功
      And 使用者 5 的角色應為 "admin"

    Example: 透過不存在的 Email 調整角色失敗
      When 使用者 "super@certimate.com" 透過 Email "notexist@example.com" 將角色調整為 "admin"
      Then 操作失敗，錯誤為「目標使用者不存在，請確認 Email 是否正確」

  Rule: 後置（回應）- 批量匯出應產生包含篩選結果的 CSV 檔案

    Example: 匯出 PRO_199 方案用戶 CSV
      When 使用者 "ops@certimate.com" 匯出用戶 CSV，篩選方案為 "PRO_199"
      Then 操作成功
      And 回應應為 CSV 檔案，包含欄位：email、display_name、plan、status、created_at

  # ========== UI 互動情境 ==========

  @ignore
  Rule: 後置（回應）- 匯出使用者 CSV 應觸發檔案下載

    Example: 匯出使用者 CSV 下載成功
      When 使用者 "ops@certimate.com" 於用戶管理頁面點擊「匯出 CSV」按鈕
      Then 操作成功
      And 瀏覽器應觸發 CSV 檔案下載
      And 下載檔案名稱應包含 "users" 與當日日期

  @ignore
  Rule: 後置（狀態）- 新增使用者應透過 prompt 輸入 Email 與密碼

    Example: 新增使用者透過 prompt 輸入 email 與密碼成功
      When 使用者 "super@certimate.com" 於用戶管理頁面點擊「新增使用者」按鈕
      And 在彈出的對話框中輸入 Email 為 "newuser@example.com"，密碼為 "Passw0rd!"
      Then 操作成功
      And 系統中應存在 Email 為 "newuser@example.com" 的使用者
      And 系統應記錄審計日誌：
        | 欄位     | 值                   |
        | action   | create_user          |

  @ignore
  Rule: 後置（狀態）- 發送通知需在輸入框輸入訊息後送出

    Example: 發送通知給使用者輸入訊息成功
      When 使用者 "ops@certimate.com" 於使用者 5 的操作選單點擊「發送通知」
      And 在通知輸入框中輸入訊息 "您的帳號已恢復正常"
      And 點擊「送出」按鈕
      Then 操作成功
      And 系統應記錄審計日誌：
        | 欄位     | 值                   |
        | action   | notify_user          |
        | target   | 使用者 5              |

  @ignore
  Rule: 後置（狀態）- 停權使用者需確認原因後才可執行

    Example: 停權使用者需確認原因
      When 使用者 "ops@certimate.com" 於使用者 5 的操作選單點擊「停權」
      Then 系統應顯示確認對話框，要求輸入停權原因
      When 輸入停權原因為 "違反使用條款" 並點擊「確認」
      Then 操作成功
      And 使用者 5 的狀態應為 "suspended"

  @ignore
  Rule: 後置（狀態）- 刪除使用者帳號需確認輸入使用者名稱

    Example: 刪除使用者帳號需確認名稱
      When 使用者 "super@certimate.com" 於使用者 5 的操作選單點擊「刪除帳號」
      Then 系統應顯示確認對話框，提示輸入 "bob@example.com" 以確認刪除
      When 輸入確認名稱為 "bob@example.com" 並點擊「確認刪除」
      Then 操作成功
      And 使用者 5 的狀態應為 "deleted"

  @ignore
  Rule: 後置（狀態）- 調整訂閱等級需透過 Modal 選擇方案與日期

    Example: 調整訂閱等級 Modal 選擇方案與日期
      When 使用者 "super@certimate.com" 於使用者 5 的操作選單點擊「調整訂閱」
      Then 系統應顯示調整訂閱 Modal
      When 在 Modal 中選擇方案為 "PRO_199"，起始日期為 "2026-04-01"，結束日期為 "2026-07-01"
      And 點擊「確認調整」按鈕
      Then 操作成功
      And 使用者 5 的訂閱方案應為 "PRO_199"

  @ignore
  Rule: 後置（回應）- 使用者搜尋應依 Email 即時過濾結果

    Example: 使用者搜尋依 email 即時過濾
      When 使用者 "ops@certimate.com" 於用戶管理頁面的搜尋框輸入 "alice"
      Then 用戶列表應即時過濾，僅顯示 Email 包含 "alice" 的使用者
      And 列表中應包含 "alice@example.com"
      And 列表中不應包含 "bob@example.com"

  @ignore
  Rule: 後置（回應）- 使用者列表應支援分頁導航

    Example: 使用者分頁導航上一頁與下一頁
      Given 系統中有超過 20 筆使用者資料
      When 使用者 "ops@certimate.com" 於用戶管理頁面查看用戶列表
      Then 列表應顯示第一頁資料，每頁最多 20 筆
      And 頁面應顯示「下一頁」按鈕
      When 點擊「下一頁」按鈕
      Then 列表應顯示第二頁資料
      And 頁面應顯示「上一頁」按鈕
      When 點擊「上一頁」按鈕
      Then 列表應顯示第一頁資料
