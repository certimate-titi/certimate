@ignore @command
Feature: 訂閱管理與多階層控制

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                  | 訂閱方案      | 訂閱狀態     | 下次扣款日  | 月費 |
      | 1        | free@example.com       | FREE          | 無           | null        | 0    |
      | 2        | pro@example.com        | PRO_199       | active       | 2026-04-01  | 199  |
      | 3        | proplus@example.com    | PRO_PLUS_399  | active       | 2026-04-01  | 399  |
      | 4        | ultra@example.com      | ULTRA_1599    | active       | 2026-04-01  | 1599 |
      | 5        | cancelled@example.com  | PRO_199       | cancelled    | 2026-03-31  | 199  |
    And 系統中有以下帳單記錄：
      | 帳單 ID | 使用者 ID | 金額 | 狀態     | 建立時間            |
      | INV-001 | 2        | 199  | success  | 2026-03-01 00:00:00 |
      | INV-002 | 3        | 399  | success  | 2026-03-01 00:00:00 |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 不可重複訂閱相同方案

    Example: PRO_PLUS 用戶嘗試再次訂閱 PRO_PLUS 失敗
      When 使用者 "proplus@example.com" 訂閱 "PRO_PLUS_399" 方案
      Then 操作失敗，錯誤為「您已訂閱此方案」

  Rule: 前置（狀態）- 已取消訂閱的用戶在到期前不可重新訂閱相同方案

    Example: 已取消的 PRO 用戶在到期前嘗試重新訂閱 PRO 失敗
      When 使用者 "cancelled@example.com" 訂閱 "PRO_199" 方案
      Then 操作失敗，錯誤為「您的 PRO_199 方案尚未到期，請等待到期後再訂閱」

  Rule: 前置（參數）- 訂閱操作必須提供必要參數

    Scenario Outline: 缺少 <缺少參數> 時訂閱失敗
      When 使用者 "free@example.com" 訂閱 <目標方案> 方案
      Then 操作失敗，錯誤為「必要參數未提供」

      Examples:
        | 缺少參數   | 目標方案 |
        | 目標方案   |          |

  # ========== 查看訂閱資訊 ==========

  Rule: 後置（回應）- 查看訂閱資訊應回傳當前方案、下次扣款日與額度比較

    Example: FREE 用戶查看訂閱資訊取得升級比較
      When 使用者 "free@example.com" 查看訂閱管理頁
      Then 操作成功
      And 回應應包含：
        | 欄位          | 值   |
        | current_plan  | FREE |
        | monthly_fee   | 0    |
        | next_billing  | null |
      And 回應應包含各方案額度比較：
        | 方案          | AI 對話次數 | 上傳數 | 考試數 | Vision OCR |
        | FREE          | 3           | 5      | 10     | 0          |
        | PRO_199       | 30          | 50     | 100    | 0          |
        | PRO_PLUS_399  | 200         | 200    | 500    | 50         |
        | ULTRA_1599    | 無限        | 無限   | 無限   | 500        |

    Example: PRO_PLUS 用戶查看訂閱資訊取得詳細狀態
      When 使用者 "proplus@example.com" 查看訂閱管理頁
      Then 操作成功
      And 回應應包含：
        | 欄位                 | 值            |
        | current_plan         | PRO_PLUS_399  |
        | monthly_fee          | 399           |
        | next_billing         | 2026-04-01    |
        | coach_remaining_quota| 200           |

  # ========== 升級 ==========

  Rule: 後置（狀態）- 升級方案後權限與額度應即時生效

    Example: PRO 用戶升級至 PRO_PLUS 後立即解鎖高階教練
      When 使用者 "pro@example.com" 完成 "PRO_PLUS_399" 方案訂閱付款
      Then 操作成功
      And 使用者 "pro@example.com" 的訂閱方案應為 "PRO_PLUS_399"
      And 使用者 "pro@example.com" 的高階教練剩餘額度應為 200
      And 使用者 "pro@example.com" 的每月上傳限額應為 200

    Example: FREE 用戶升級至 PRO 後額度立即切換
      When 使用者 "free@example.com" 完成 "PRO_199" 方案訂閱付款
      Then 操作成功
      And 使用者 "free@example.com" 的訂閱方案應為 "PRO_199"
      And 使用者 "free@example.com" 的每日 AI 對話限額應從 3 提升至 30

  # ========== 降級 ==========

  Rule: 後置（狀態）- 降級方案應於當期結束後生效

    Example: PRO_PLUS 用戶申請降級至 PRO 收到到期提示
      When 使用者 "proplus@example.com" 申請降級至 "PRO_199" 方案
      Then 操作成功
      And 回應應包含：
        | 欄位                  | 值                       |
        | downgrade_effective   | 2026-04-01               |
        | message               | 降級將於下一計費週期生效 |
      And 使用者 "proplus@example.com" 在 2026-04-01 前的訂閱方案應維持 "PRO_PLUS_399"

  # ========== 取消訂閱 ==========

  Rule: 後置（狀態）- 取消訂閱後當期結束前功能應維持可用

    Example: PRO_PLUS 用戶取消訂閱後到期前保有所有功能
      When 使用者 "proplus@example.com" 取消訂閱
      Then 操作成功
      And 使用者 "proplus@example.com" 的訂閱狀態應為 "cancelled"
      And 使用者 "proplus@example.com" 在 2026-04-01 前仍可使用高階教練功能
      And 2026-04-01 到期後使用者 "proplus@example.com" 的訂閱方案應自動降級為 "FREE"

  # ========== 帳單紀錄 ==========

  Rule: 後置（回應）- 帳單紀錄查詢應回傳完整交易明細

    Example: 查看帳單紀錄取得歷史發票
      When 使用者 "proplus@example.com" 查看帳單紀錄
      Then 操作成功
      And 回應中每筆帳單應包含：
        | 欄位        | 範例值              |
        | invoice_id  | INV-002             |
        | amount      | 399                 |
        | plan        | PRO_PLUS_399        |
        | status      | success             |
        | created_at  | 2026-03-01 00:00:00 |
