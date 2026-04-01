Feature: 訂閱管理與多階層控制

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                  | 訂閱方案   | 訂閱狀態    | 下次扣款日     | 月費 |
      | 1        | free@example.com       | FREE       | active      | null           | 0    |
      | 2        | pro@example.com        | PRO        | active      | 2026-04-01     | 199  |
      | 3        | proplus@example.com    | PRO_PLUS   | active      | 2026-04-01     | 399  |
      | 4        | ultra@example.com      | ULTRA      | active      | 2026-04-01     | 1599 |
      | 5        | cancelled@example.com  | PRO        | cancelled   | 2026-04-30     | 199  |
    And 系統中有以下帳單記錄：
      | 帳單 ID  | 使用者 ID | 金額 | 狀態     | 建立時間            |
      | INV-001  | 2        | 199  | success  | 2026-03-01 00:00:00 |
      | INV-002  | 3        | 399  | success  | 2026-03-01 00:00:00 |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 不可重複訂閱相同方案

    Example: PRO_PLUS 用戶嘗試再次訂閱 PRO_PLUS 失敗
      When 使用者 "proplus@example.com" 訂閱 "PRO_PLUS" 方案
      Then 操作失敗，錯誤為「您已訂閱此方案」

  Rule: 前置（狀態）- 已取消訂閱的用戶在到期前不可重新訂閱相同方案

    Example: 已取消的 PRO 用戶在到期前嘗試重新訂閱 PRO 失敗
      When 使用者 "cancelled@example.com" 訂閱 "PRO" 方案
      Then 操作失敗，錯誤為「您的 PRO 方案尚未到期，請等待到期後再訂閱」

  # ========== 查看訂閱資訊 ==========

  Rule: 後置（回應）- 查看訂閱資訊應回傳當前方案與下次扣款日

    Example: FREE 用戶查看訂閱資訊
      When 使用者 "free@example.com" 查看訂閱管理頁
      Then 操作成功
      And 回應應包含訂閱資訊：
        | 欄位          | 值   |
        | current_plan  | FREE |
        | monthly_fee   | 0    |

    Example: PRO_PLUS 用戶查看訂閱資訊取得詳細狀態
      When 使用者 "proplus@example.com" 查看訂閱管理頁
      Then 操作成功
      And 回應應包含訂閱資訊：
        | 欄位                 | 值         |
        | current_plan         | PRO_PLUS   |
        | monthly_fee          | 399        |
        | next_billing         | 2026-04-01 |

  # ========== 升級 ==========

  Rule: 後置（狀態）- 升級方案後權限應即時生效

    Example: PRO 用戶升級至 PRO_PLUS 後方案更新
      When 使用者 "pro@example.com" 完成 "PRO_PLUS" 方案訂閱付款
      Then 操作成功
      And 使用者 "pro@example.com" 的訂閱方案應為 "PRO_PLUS"

    Example: FREE 用戶升級至 PRO 後方案更新
      When 使用者 "free@example.com" 完成 "PRO" 方案訂閱付款
      Then 操作成功
      And 使用者 "free@example.com" 的訂閱方案應為 "PRO"

  # ========== 降級 ==========

  Rule: 後置（狀態）- 降級方案應於當期結束後生效

    Example: PRO_PLUS 用戶申請降級至 PRO 收到到期提示
      When 使用者 "proplus@example.com" 申請降級至 "PRO" 方案
      Then 操作成功
      And 回應應包含降級資訊：
        | 欄位                  | 值                       |
        | downgrade_effective   | 2026-04-01               |
        | message               | 降級將於下一計費週期生效 |

  # ========== 取消訂閱 ==========

  Rule: 後置（狀態）- 取消訂閱後訂閱狀態更新

    Example: PRO_PLUS 用戶取消訂閱後狀態變為 cancelled
      When 使用者 "proplus@example.com" 取消訂閱
      Then 操作成功
      And 使用者 "proplus@example.com" 的訂閱狀態應為 "cancelled"

  # ========== 帳單紀錄 ==========

  Rule: 後置（回應）- 帳單紀錄查詢應回傳完整交易明細

    Example: 查看帳單紀錄取得歷史發票
      When 使用者 "proplus@example.com" 查看帳單紀錄
      Then 操作成功
      And 回應應包含帳單記錄
