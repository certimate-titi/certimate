Feature: 平台管理後台 — 財務與訂閱管理

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                   | 訂閱方案  | 角色         |
      | 1        | super@certimate.com     | ULTRA     | SUPER_ADMIN  |
      | 2        | ops@certimate.com       | ULTRA     | ADMIN        |
    And 系統中有以下交易紀錄：
      | 交易 ID | 使用者 ID | 金額 | 方案      | 狀態    | 交易時間            |
      | TXN-001 | 1        | 199  | PRO       | success | 2026-03-01 10:00:00 |
      | TXN-002 | 2        | 399  | PRO_PLUS  | success | 2026-03-02 14:30:00 |
      | TXN-003 | 1        | 1599 | ULTRA     | failed  | 2026-03-03 09:00:00 |
    And 系統中有以下退款申請：
      | 退款 ID | 使用者 ID | 交易 ID | 金額 | 狀態    |
      | REF-001 | 1        | TXN-001 | 199  | pending |
      | REF-002 | 2        | TXN-002 | 399  | pending |

  # ========== 訂閱分布統計 ==========

  Rule: 後置（回應）- 訂閱分布應回傳各方案用戶數

    Example: 查看訂閱分布取得各方案統計
      When 使用者 "ops@certimate.com" 查看訂閱分布統計
      Then 操作成功
      And 回應應包含訂閱分布資料

  # ========== 交易紀錄 ==========

  Rule: 後置（回應）- 交易紀錄查詢應回傳完整欄位且支援篩選

    Example: 查看交易紀錄取得明細列表
      When 使用者 "ops@certimate.com" 查看交易紀錄
      Then 操作成功
      And 回應中應包含交易紀錄列表

    Example: 依狀態篩選交易紀錄
      When 使用者 "ops@certimate.com" 查看交易紀錄，篩選狀態為 "failed"
      Then 操作成功
      And 回應中所有交易的狀態應為 "failed"

  # ========== 退款管理 ==========

  Rule: 後置（狀態）- 核准退款應更新狀態並記錄審計日誌

    Example: super_admin 核准退款成功
      When 使用者 "super@certimate.com" 核准退款 "REF-001"
      Then 操作成功
      And 退款 "REF-001" 的狀態應為 "approved"
      And 系統應記錄審計日誌：
        | 欄位     | 值                |
        | action   | approve_refund    |

  Rule: 後置（狀態）- 駁回退款應記錄理由

    Example: 駁回退款申請成功
      When 使用者 "ops@certimate.com" 駁回退款 "REF-002"，理由為 "超過退款期限"
      Then 操作成功
      And 退款 "REF-002" 的狀態應為 "rejected"

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
        | 欄位              | 值           |
        | code              | LAUNCH2026   |
        | discount_type     | percentage   |
        | discount_value    | 30           |
        | applicable_plans  | PRO          |
        | max_uses          | 500          |
        | max_uses_per_user | 1            |
      Then 操作成功
      And 優惠碼 "LAUNCH2026" 的狀態應為 "active"
      And 優惠碼 "LAUNCH2026" 的已使用次數應為 0
