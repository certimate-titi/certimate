@backend @command
Feature: 平台管理後台 — 系統設定（僅 super_admin）

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                   | 訂閱方案      | 角色         |
      | 1        | super@certimate.com     | ULTRA_1599    | super_admin  |
      | 2        | ops@certimate.com       | ULTRA_1599    | admin        |
    And 系統中有以下 AI 模型路由設定：
      | 方案     | 任務類型 | 主要模型            | 備援模型           |
      | FREE     | basic    | gemini-1.5-flash    | llama-3.1-8b       |
      | PRO_199  | advanced | claude-3.5-sonnet   | gemini-1.5-flash   |
    And 系統中有以下方案限額設定：
      | 方案     | 每月上傳數 | 每月考試數 | 每日 AI 對話數 | 每月 Vision 頁數 |
      | FREE     | 5          | 10         | 3              | 0                |
      | PRO_199  | 50         | 100        | 30             | 0                |
    And 系統中有以下 Feature Flag：
      | Flag ID | Flag Key                    | 狀態   | 上線比例 |
      | 1       | enable_socratic_tutor_v2    | false  | 0        |

  # ========== AI 模型路由 ==========

  Rule: 後置（狀態）- 更新 AI 模型路由應即時生效並記錄審計日誌

    Example: super_admin 變更 FREE 方案的基本模型成功
      When 使用者 "super@certimate.com" 更新 AI 模型路由，方案為 "FREE"，任務類型為 "basic"，主要模型為 "llama-3.1-8b"
      Then 操作成功
      And FREE 方案 basic 任務的主要模型應為 "llama-3.1-8b"
      And 系統應記錄審計日誌：
        | 欄位     | 值                                           |
        | action   | update_model_routing                         |
        | details  | FREE basic: gemini-1.5-flash → llama-3.1-8b  |

  # ========== 方案限額 ==========

  Rule: 後置（狀態）- 更新方案限額應即時生效

    Example: super_admin 調整 FREE 方案每月上傳數成功
      When 使用者 "super@certimate.com" 更新方案限額，方案為 "FREE"，每月上傳數為 8
      Then 操作成功
      And FREE 方案的每月上傳數限額應為 8

  # ========== 系統公告 ==========

  Rule: 前置（參數）- 建立公告必須提供標題與內容

    Scenario Outline: 建立公告缺少 <缺少參數> 時失敗
      When 使用者 "super@certimate.com" 建立系統公告，標題為 <標題>，內容為 <內容>，類型為 "info"
      Then 操作失敗，錯誤為「必要參數未提供」

      Examples:
        | 缺少參數 | 標題         | 內容                   |
        | 標題     |              | 2026/04/01 維護        |
        | 內容     | 系統維護通知  |                        |

  Rule: 後置（狀態）- 成功建立公告後應在指定時間範圍內顯示

    Example: 建立排程系統維護公告成功
      When 使用者 "super@certimate.com" 建立系統公告：
        | 欄位         | 值                         |
        | title        | 系統維護通知                |
        | content      | 2026/04/01 02:00-06:00 維護 |
        | type         | maintenance                 |
        | display_mode | banner                      |
        | starts_at    | 2026-03-30T00:00:00         |
        | ends_at      | 2026-04-01T06:00:00         |
      Then 操作成功
      And 公告狀態應為 "active"

  Rule: 後置（狀態）- super_admin 可停用已建立的公告

    Example: 停用公告成功
      Given 系統中有一則 active 狀態的公告，ID 為 "ann-1"，標題為 "系統維護通知"
      When 使用者 "super@certimate.com" 停用公告 "ann-1"
      Then 操作成功
      And 公告 "ann-1" 的狀態應為 "inactive"

  Rule: 後置（狀態）- super_admin 可刪除已建立的公告

    Example: 刪除公告成功
      Given 系統中有一則公告，ID 為 "ann-2"，標題為 "臨時公告"
      When 使用者 "super@certimate.com" 刪除公告 "ann-2"
      Then 操作成功
      And 系統中不應存在公告 "ann-2"

  Rule: 後置（回應）- 一般用戶可讀取生效中的公告

    Example: 一般用戶取得 banner 類型公告
      Given 系統中有一則 active 狀態的公告，標題為 "新功能上線"，顯示方式為 "banner"
      And 系統中有一則 inactive 狀態的公告，標題為 "已停用公告"
      When 一般用戶查詢公開公告列表
      Then 操作成功
      And 回應應包含標題為 "新功能上線" 的公告
      And 回應不應包含標題為 "已停用公告" 的公告

  # ========== Feature Flag ==========

  Rule: 後置（狀態）- 更新 Feature Flag 上線比例應即時生效

    Example: 設定 Feature Flag 20% 漸進式上線成功
      When 使用者 "super@certimate.com" 更新 Feature Flag 1，上線比例為 20，目標方案為 "PRO_199,PRO_PLUS_399"
      Then 操作成功
      And Feature Flag "enable_socratic_tutor_v2" 應為啟用狀態
      And 上線比例應為 20

  # ========== 管理員帳號 ==========

  Rule: 後置（狀態）- super_admin 可新增管理員帳號

    Example: 新增 admin 帳號成功
      When 使用者 "super@certimate.com" 新增管理員，Email 為 "newops@certimate.com"，角色為 "admin"
      Then 操作成功
      And 系統應發送帳號啟用信至 "newops@certimate.com"
      And 系統應記錄審計日誌：
        | 欄位     | 值                         |
        | action   | create_admin               |
        | details  | newops@certimate.com admin |

  # ========== 系統維運操作 ==========

  Rule: 後置（狀態）- 重置 AI 流量限制應清除所有用戶的冷卻狀態

    Example: super_admin 重置 AI 流量限制成功
      When 使用者 "super@certimate.com" 重置 AI 流量限制
      Then 操作成功
      And 系統應記錄審計日誌：
        | 欄位    | 值                  |
        | action  | reset_ai_limits     |

  Rule: 後置（狀態）- 清理系統暫存檔應返回清理結果

    Example: super_admin 清理系統暫存檔成功
      When 使用者 "super@certimate.com" 清理系統暫存檔
      Then 操作成功
      And 系統應記錄審計日誌：
        | 欄位    | 值                  |
        | action  | clear_cache         |

  # ========== 審計日誌 ==========

  Rule: 後置（回應）- 審計日誌應回傳不可變的完整操作紀錄

    Example: 查看審計日誌取得完整操作紀錄
      When 使用者 "super@certimate.com" 查看審計日誌
      Then 操作成功
      And 回應中每筆紀錄應包含：
        | 欄位         | 說明                   |
        | timestamp    | 操作時間               |
        | admin_id     | 執行操作的管理員 ID    |
        | action       | 操作類型               |
        | target_type  | 操作對象類型           |
        | target_id    | 操作對象 ID            |
        | details      | 操作詳情（JSON）       |
        | ip_address   | 來源 IP 位址           |

  # ========== UI 互動情境 ==========

  Rule: 後置（狀態）- AI 模型路由設定應透過表單儲存

    Example: AI 模型路由設定儲存成功
      When 使用者 "super@certimate.com" 於 AI 模型路由設定頁面選擇方案 "FREE"，任務類型 "basic"
      And 將主要模型修改為 "llama-3.1-8b"
      And 點擊「儲存」按鈕
      Then 操作成功
      And FREE 方案 basic 任務的主要模型應為 "llama-3.1-8b"
      And 頁面應顯示「設定已儲存」提示訊息

  Rule: 後置（狀態）- 方案配額表格應支援行內編輯與儲存

    Example: 方案配額表格編輯儲存成功
      When 使用者 "super@certimate.com" 於方案配額表格中將 "FREE" 方案的每月上傳數修改為 8
      And 點擊「儲存變更」按鈕
      Then 操作成功
      And FREE 方案的每月上傳數限額應為 8
      And 頁面應顯示「配額已更新」提示訊息

  Rule: 後置（狀態）- Feature Flag 應支援切換開關操作

    Example: 功能旗標切換開關
      When 使用者 "super@certimate.com" 於 Feature Flag 列表中將 "enable_socratic_tutor_v2" 的開關切換為啟用
      Then 操作成功
      And Feature Flag "enable_socratic_tutor_v2" 應為啟用狀態
      And 頁面應顯示該 Flag 狀態為「已啟用」

  Rule: 後置（回應）- 管理員帳號表格應顯示所有管理員資訊

    Example: 管理員帳號表格顯示
      When 使用者 "super@certimate.com" 於系統設定頁面查看管理員帳號列表
      Then 操作成功
      And 表格應包含以下欄位：Email、角色、建立日期、狀態
      And 表格中應包含 "super@certimate.com" 與 "ops@certimate.com"

  Rule: 後置（回應）- 稽核日誌應支援匯出 CSV

    Example: 稽核日誌匯出 CSV
      When 使用者 "super@certimate.com" 於稽核日誌頁面點擊「匯出 CSV」按鈕
      Then 操作成功
      And 瀏覽器應觸發 CSV 檔案下載
      And 下載檔案應包含欄位：timestamp、admin_id、action、target_type、target_id、details

  Rule: 後置（回應）- 稽核日誌應支援日期範圍篩選

    Example: 稽核日誌日期範圍篩選
      When 使用者 "super@certimate.com" 於稽核日誌頁面設定起始日期為 "2026-03-01"，結束日期為 "2026-03-31"
      And 點擊「篩選」按鈕
      Then 操作成功
      And 稽核日誌列表應僅顯示 2026-03-01 至 2026-03-31 範圍內的紀錄

  Rule: 後置（回應）- 稽核日誌應支援分頁導航

    Example: 稽核日誌分頁導航
      Given 系統中有超過 50 筆稽核日誌紀錄
      When 使用者 "super@certimate.com" 於稽核日誌頁面查看紀錄列表
      Then 列表應顯示第一頁資料，每頁最多 50 筆
      And 頁面應顯示「下一頁」按鈕
      When 點擊「下一頁」按鈕
      Then 列表應顯示第二頁資料

  # ========== GET 列表 API 覆蓋 ==========

  @added-by:cto
  Rule: 後置（回應）- 管理員應能查詢系統公告列表

    Example: 查詢系統公告列表
      When 使用者 "super@certimate.com" 查詢系統公告列表
      Then 操作成功

  @added-by:cto
  Rule: 後置（回應）- 管理員應能查詢特性旗標列表

    Example: 查詢特性旗標列表
      When 使用者 "super@certimate.com" 查詢特性旗標列表
      Then 操作成功

  @added-by:cto
  Rule: 後置（回應）- 管理員應能查詢 AI 模型路由列表

    Example: 查詢 AI 模型路由列表
      When 使用者 "super@certimate.com" 查詢 AI 模型路由列表
      Then 操作成功

  @added-by:cto
  Rule: 後置（回應）- 管理員應能查詢方案配額列表

    Example: 查詢方案配額列表
      When 使用者 "super@certimate.com" 查詢方案配額列表
      Then 操作成功

      And 頁面應顯示「上一頁」按鈕
