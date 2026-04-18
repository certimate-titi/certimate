@query
Feature: 平台管理後台 — 財務與訂閱管理

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                   | 訂閱方案      | 角色         |
      | 1        | super@certimate.com     | ULTRA_1599    | super_admin  |
      | 2        | ops@certimate.com       | ULTRA_1599    | admin        |
    And 系統中有以下交易紀錄：
      | 交易 ID | 使用者 ID | 金額 | 方案         | 狀態   | 交易時間            |
      | TXN-001 | 10       | 199  | PRO_199      | success| 2026-03-01 10:00:00 |
      | TXN-002 | 11       | 399  | PRO_PLUS_399 | success| 2026-03-02 14:30:00 |
      | TXN-003 | 12       | 1599 | ULTRA_1599   | failed | 2026-03-03 09:00:00 |
    And 系統中有以下退款申請：
      | 退款 ID | 使用者 ID | 交易 ID | 金額 | 狀態    |
      | REF-001 | 10       | TXN-001 | 199  | pending |
      | REF-002 | 11       | TXN-002 | 399  | pending |

  # ========== 訂閱分布與營收 ==========

  Rule: 後置（回應）- 訂閱分布應回傳各方案用戶數與 MRR 趨勢

    Example: 查看訂閱分布取得圓餅圖與 MRR 資料
      When 使用者 "ops@certimate.com" 查看訂閱分布統計
      Then 操作成功
      And 回應應包含各方案用戶數：
        | 方案          | 用戶數 |
        | FREE          | 1200   |
        | PRO_199       | 350    |
        | PRO_PLUS_399  | 120    |
        | ULTRA_1599    | 30     |
      And 回應應包含最近 30 天的 MRR 趨勢資料點

  # ========== 交易紀錄 ==========

  Rule: 後置（回應）- 交易紀錄查詢應回傳完整欄位且支援篩選

    Example: 查看交易紀錄取得明細列表
      When 使用者 "ops@certimate.com" 查看交易紀錄
      Then 操作成功
      And 回應中每筆交易應包含：
        | 欄位            | 範例值              |
        | transaction_id  | TXN-001             |
        | user_id         | 10                  |
        | amount          | 199                 |
        | plan            | PRO_199             |
        | status          | success             |
        | created_at      | 2026-03-01 10:00:00 |

    Example: 依狀態篩選交易紀錄
      When 使用者 "ops@certimate.com" 查看交易紀錄，篩選狀態為 "failed"
      Then 操作成功
      And 回應中所有交易的狀態應為 "failed"

  # ========== 退款管理 ==========

  Rule: 後置（狀態）- 核准退款應觸發 Stripe Refund 並自動降級至 FREE

    Example: super_admin 核准退款成功
      When 使用者 "super@certimate.com" 核准退款 "REF-001"，OTP 為 "123456"
      Then 操作成功
      And 退款 "REF-001" 的狀態應為 "approved"
      And 使用者 10 的訂閱方案應自動降級為 "FREE"
      And 系統應記錄審計日誌：
        | 欄位     | 值                |
        | action   | approve_refund    |
        | target   | REF-001           |
        | details  | 退款 199 TWD      |

  Rule: 後置（狀態）- 駁回退款應記錄理由並通知用戶

    Example: 駁回退款申請成功
      When 使用者 "ops@certimate.com" 駁回退款 "REF-002"，理由為 "超過退款期限"
      Then 操作成功
      And 退款 "REF-002" 的狀態應為 "rejected"
      And 系統應發送駁回通知 Email 至使用者 11，內容包含理由 "超過退款期限"

  # ========== 優惠碼 ==========

  Rule: 前置（參數）- 優惠碼必要參數必須提供

    Scenario Outline: 建立優惠碼缺少 <缺少參數> 時失敗
      When 使用者 "super@certimate.com" 建立優惠碼，代碼為 <代碼>，折扣類型為 <折扣類型>，折扣值為 <折扣值>
      Then 操作失敗，錯誤為「必要參數未提供」

      Examples:
        | 缺少參數  | 代碼       | 折扣類型   | 折扣值 |
        | 代碼      |            | percentage | 30     |
        | 折扣類型  | LAUNCH2026 |            | 30     |
        | 折扣值    | LAUNCH2026 | percentage |        |

  Rule: 後置（狀態）- 成功建立優惠碼後應為啟用狀態

    Example: 建立百分比折扣優惠碼成功
      When 使用者 "super@certimate.com" 建立優惠碼：
        | 欄位           | 值           |
        | code           | LAUNCH2026   |
        | discount_type  | percentage   |
        | discount_value | 30           |
        | applicable_plans | PRO_199    |
        | max_uses       | 500          |
        | max_uses_per_user | 1         |
      Then 操作成功
      And 優惠碼 "LAUNCH2026" 的狀態應為 "active"
      And 優惠碼 "LAUNCH2026" 的已使用次數應為 0

  @added-by:cto
  Rule: 後置（回應）- 管理員可列出退款申請佇列並依狀態篩選

    Example: 列出待審退款成功
      When 使用者 "ops@certimate.com" 查詢待審退款清單
      Then 操作成功
      And 退款清單應包含退款 "REF-001"
      And 退款清單應包含退款 "REF-002"

    Example: 非管理員查詢退款清單應被拒絕
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email             | 訂閱方案 | 角色 |
        | 30       | guest@example.com | FREE     | user |
      When 使用者 "guest@example.com" 查詢待審退款清單
      Then 操作失敗，狀態碼為 403

  @added-by:cto
  Rule: 後置（回應）- 管理員可列出所有優惠碼

    Example: 列出優惠碼成功
      Given 系統中有以下優惠碼：
        | 代碼        | 折扣類型 | 折扣值 |
        | LAUNCH2026  | percent  | 20     |
      When 使用者 "ops@certimate.com" 查詢優惠碼清單
      Then 操作成功
      And 優惠碼清單應包含代碼 "LAUNCH2026"

  @added-by:cto
  Rule: 命令（申請）- 使用者可對自己的交易申請退款

    Example: 使用者申請退款成功
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email             | 訂閱方案 |
        | 99       | alice@example.com | PRO_199  |
      And 系統中有以下交易紀錄：
        | 交易 ID    | 使用者 ID | 金額 | 方案    | 狀態    | 交易時間            |
        | TXN-ALICE | 99       | 199  | PRO_199 | success | 2026-03-01 10:00:00 |
      When 使用者 "alice@example.com" 對交易 "TXN-ALICE" 申請退款，金額為 199，理由為 "不再使用"
      Then 操作成功
      And 回應應包含 refund_id 欄位
      And 回應的 status 應為 "pending"

  @added-by:cto
  Rule: 命令（驗證）- 使用者結帳前可驗證優惠碼並取得試算金額

    Example: 驗證有效優惠碼取得折扣試算
      Given 系統中有以下優惠碼：
        | 代碼        | 折扣類型 | 折扣值 |
        | WELCOME10   | percent  | 10     |
      When 使用者 "ops@certimate.com" 驗證優惠碼 "WELCOME10"，方案為 "PRO_199"，金額為 199
      Then 操作成功
      And 回應的 discount_amount 應為 19.9
      And 回應的 final_amount 應為 179.1

    Example: 驗證無效優惠碼應回傳 404
      When 使用者 "ops@certimate.com" 驗證優惠碼 "NOTEXIST"，方案為 "PRO_199"，金額為 199
      Then 操作失敗，狀態碼為 404

  # ========== UI 互動情境 ==========

  Rule: 後置（回應）- 匯出財務報告應觸發 JSON 檔案下載

    Example: 匯出財務報告下載 JSON
      When 使用者 "ops@certimate.com" 於財務管理頁面點擊「匯出報告」按鈕
      Then 操作成功
      And 瀏覽器應觸發 JSON 檔案下載
      And 下載檔案應包含交易摘要與營收統計資料

  Rule: 後置（回應）- 交易搜尋應依交易 ID 即時過濾

    Example: 交易搜尋依交易 ID 過濾
      When 使用者 "ops@certimate.com" 於交易紀錄頁面的搜尋框輸入 "TXN-001"
      Then 交易列表應即時過濾，僅顯示交易 ID 包含 "TXN-001" 的紀錄
      And 列表中應包含交易 "TXN-001"
      And 列表中不應包含交易 "TXN-002"

  Rule: 後置（回應）- 交易狀態篩選應透過下拉選單切換

    Example: 交易狀態篩選下拉選單切換
      When 使用者 "ops@certimate.com" 於交易紀錄頁面的狀態篩選下拉選單選擇 "failed"
      Then 交易列表應僅顯示狀態為 "failed" 的交易
      And 列表中應包含交易 "TXN-003"
      And 列表中不應包含交易 "TXN-001"

  Rule: 後置（回應）- 交易列表應支援展開顯示詳情

    Example: 交易列展開顯示詳情
      When 使用者 "ops@certimate.com" 於交易紀錄頁面點擊交易 "TXN-001" 的展開按鈕
      Then 交易 "TXN-001" 應展開顯示詳細資訊：
        | 欄位            | 值                  |
        | transaction_id  | TXN-001             |
        | user_id         | 10                  |
        | amount          | 199                 |
        | plan            | PRO_199             |
        | status          | success             |
        | created_at      | 2026-03-01 10:00:00 |

  Rule: 後置（回應）- MRR 趨勢圖表應顯示正確資料

    Example: MRR 趨勢圖表顯示正確資料
      When 使用者 "ops@certimate.com" 於財務管理頁面查看 MRR 趨勢圖表
      Then 操作成功
      And 圖表應顯示最近 30 天的 MRR 資料點
      And 每個資料點應包含日期與對應的 MRR 金額
