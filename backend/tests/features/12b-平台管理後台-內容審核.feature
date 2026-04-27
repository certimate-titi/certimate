@backend @command
Feature: 平台管理後台 — 內容與安全審核

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                   | 訂閱方案      | 角色         | 狀態    |
      | 1        | super@certimate.com     | ULTRA_1599    | super_admin  | active  |
      | 2        | ops@certimate.com       | ULTRA_1599    | admin        | active  |
      | 7        | cooling@example.com     | PRO_PLUS_399  | user         | cooling |
    And 系統中有以下 AI 冷卻紀錄：
      | 使用者 ID | 原因                    | 冷卻結束時間        |
      | 7        | 10min_5_out_of_scope    | 2026-03-25 15:30:00 |
    And 系統中有以下內容檢舉：
      | 檢舉 ID | 檢舉者 ID | 類型      | 目標類型  | 目標 ID | 狀態    |
      | RPT-001 | 10       | copyright | resource  | 50      | pending |
      | RPT-002 | 11       | inappropriate | resource | 51  | pending |

  # ========== AI 濫用監控 ==========

  Rule: 後置（回應）- AI 濫用監控應回傳冷卻中用戶清單與剩餘時間

    Example: 查看 AI 濫用監控取得冷卻用戶列表
      When 使用者 "ops@certimate.com" 查看 AI 濫用監控面板
      Then 操作成功
      And 回應應包含冷卻中用戶：
        | 使用者 ID | Email                  | 原因                  | 冷卻剩餘秒數 |
        | 7        | cooling@example.com    | 10min_5_out_of_scope  | 1800         |

  Rule: 後置（狀態）- 手動解除冷卻應立即生效並記錄審計日誌

    Example: 管理員手動解除用戶冷卻成功
      When 使用者 "ops@certimate.com" 解除使用者 7 的 AI 冷卻狀態
      Then 操作成功
      And 使用者 7 的冷卻狀態應為已解除
      And 系統應記錄審計日誌：
        | 欄位     | 值                    |
        | action   | unlock_cooldown       |
        | target   | 使用者 7               |

  # ========== 內容檢舉處理 ==========

  Rule: 後置（回應）- 檢舉佇列應回傳待處理檢舉清單

    Example: 查看待處理檢舉列表
      When 使用者 "ops@certimate.com" 查看內容檢舉佇列，篩選狀態為 "pending"
      Then 操作成功
      And 回應應包含 2 筆待處理檢舉

  Rule: 後置（狀態）- 判定違規時刪除內容並警告用戶

    Example: 處理版權檢舉為違規成功
      When 使用者 "ops@certimate.com" 處理檢舉 "RPT-001"，動作為 "delete_and_warn"，備註為 "確認版權侵害"
      Then 操作成功
      And 檢舉 "RPT-001" 的狀態應為 "resolved"
      And 目標資源 50 應被刪除
      And 系統應發送警告通知至資源擁有者
      And 系統應記錄審計日誌：
        | 欄位     | 值                    |
        | action   | resolve_report        |
        | target   | RPT-001               |
        | details  | delete_and_warn       |

  Rule: 後置（狀態）- 判定為誤報時原始內容不受影響

    Example: 處理檢舉為誤報成功
      When 使用者 "ops@certimate.com" 處理檢舉 "RPT-002"，動作為 "dismiss"，備註為 "審查後不構成違規"
      Then 操作成功
      And 檢舉 "RPT-002" 的狀態應為 "dismissed"
      And 目標資源 51 不應被刪除

  # ========== UI 互動情境 ==========

  Rule: 後置（狀態）- 通過內容審核項目應更新狀態為已通過

    Example: 通過內容審核項目成功
      When 使用者 "ops@certimate.com" 於檢舉 "RPT-002" 點擊「通過」按鈕
      Then 操作成功
      And 檢舉 "RPT-002" 的狀態應為 "approved"
      And 目標資源 51 不應被刪除

  Rule: 後置（狀態）- 移除內容審核項目需確認後執行

    Example: 移除內容審核項目需確認
      When 使用者 "ops@certimate.com" 於檢舉 "RPT-001" 點擊「移除」按鈕
      Then 系統應顯示確認對話框，提示「確定要移除此內容嗎？此操作無法復原。」
      When 點擊「確認移除」按鈕
      Then 操作成功
      And 檢舉 "RPT-001" 的狀態應為 "resolved"
      And 目標資源 50 應被刪除

  Rule: 後置（回應）- 審核佇列應支援篩選切換

    Example: 審核佇列篩選切換
      When 使用者 "ops@certimate.com" 於內容審核頁面的篩選選單選擇 "pending"
      Then 檢舉列表應僅顯示狀態為 "pending" 的檢舉
      When 於篩選選單切換為 "resolved"
      Then 檢舉列表應僅顯示狀態為 "resolved" 的檢舉

  Rule: 後置（狀態）- 快速操作可重設 AI 速率限制

    Example: 快速操作重設 AI 速率限制
      When 使用者 "super@certimate.com" 於系統維運面板點擊「重設 AI 速率限制」按鈕
      Then 系統應顯示確認對話框
      When 點擊「確認」按鈕
      Then 操作成功
      And 系統應記錄審計日誌：
        | 欄位    | 值                  |
        | action  | reset_ai_limits     |

  Rule: 後置（狀態）- 快速操作可清除系統快取

    Example: 快速操作清除系統快取
      When 使用者 "super@certimate.com" 於系統維運面板點擊「清除系統快取」按鈕
      Then 系統應顯示確認對話框
      When 點擊「確認」按鈕
      Then 操作成功
      And 系統應記錄審計日誌：
        | 欄位    | 值                  |
        | action  | clear_cache         |

  # ========== 前端審核面板（frontend-compatible endpoints） ==========

  @added-by:cto
  Rule: 後置（回應）- 前端審核佇列回應應包含 items 陣列

    Example: 查看前端審核佇列
      When 使用者 "ops@certimate.com" 查詢前端審核佇列
      Then 操作成功
      And 回應應包含 "items" 欄位

  @added-by:cto
  Rule: 後置（回應）- 前端審核統計應回傳四項指標

    Example: 查看審核統計
      When 使用者 "ops@certimate.com" 查詢審核統計
      Then 操作成功
      And 回應應包含 "pending_reports" 欄位
      And 回應應包含 "cooled_users" 欄位

  @added-by:cto
  Rule: 後置（回應）- 前端濫用監控應列出冷卻用戶

    Example: 查看前端濫用監控
      When 使用者 "ops@certimate.com" 查詢前端濫用監控
      Then 操作成功
      And 回應應包含 "items" 欄位

    Example: 前端濫用監控應帶出冷卻原因與狀態
      When 使用者 "ops@certimate.com" 查詢前端濫用監控
      Then 操作成功
      And 前端濫用監控清單應包含至少一筆冷卻紀錄
      And 前端濫用監控第一筆的 status 應為 "cooling"
      And 前端濫用監控第一筆的 metric 欄位不應為空

  @added-by:cto
  Rule: 後置（回應）- 內容審核佇列應回傳結構化清單

    Example: 查看內容審核佇列
      When 使用者 "ops@certimate.com" 查詢內容審核佇列
      Then 操作成功
      And 回應應包含 "items" 欄位
