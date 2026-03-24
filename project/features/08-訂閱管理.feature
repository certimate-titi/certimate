@ignore
Feature: 訂閱管理與多階層控制

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                  | 訂閱方案 | 訂閱狀態       | 下次扣款日 | 月費 |
      | 1        | free@example.com       | FREE     | 無             | null       | 0    |
      | 2        | pro@example.com        | PRO      | 訂閱中         | 2024-02-01 | 199  |
      | 3        | proplus@example.com    | PRO_PLUS | 訂閱中         | 2024-02-01 | 399  |
      | 4        | ultra@example.com      | ULTRA    | 訂閱中         | 2024-02-01 | 1599 |
      | 5        | cancelled@example.com  | PRO      | 已取消待到期   | 2024-01-31 | 199  |
    And 系統中有以下帳單記錄：
      | 帳單 ID | 使用者 ID | 金額 | 狀態   | 建立時間            |
      | 1       | 2        | 199  | 已支付 | 2024-01-01 00:00:00 |
      | 2       | 3        | 399  | 已支付 | 2024-01-01 00:00:00 |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 已為相同方案的用戶不可重複訂閱

    Example: PRO_PLUS 用戶嘗試再次訂閱 PRO_PLUS 方案失敗
      When 使用者 "proplus@example.com" 訂閱 PRO_PLUS 方案
      Then 操作失敗
      And 錯誤訊息應為 "您已訂閱此方案"

  Rule: 前置（狀態）- 降級方案須在當前訂閱週期結束後生效

    Example: PRO_PLUS 用戶申請降級至 PRO 方案時收到到期日提示
      When 使用者 "proplus@example.com" 申請變更方案至 PRO
      Then 操作成功
      And 回應應包含：
        | 欄位         | 值                        |
        | 降級生效日期 | 2024-02-01                |
        | 提示訊息     | 降級將於下一計費週期生效  |

  # ========== 後置條件 ==========

  Rule: 後置（回應）- 查看訂閱資訊應回傳當前方案、下次扣款日與權限額度比較

    Example: FREE 用戶查看訂閱資訊時顯示升級提示
      When 使用者 "free@example.com" 查看訂閱管理頁
      Then 操作成功
      And 回應應包含：
        | 欄位     | 值   |
        | 當前方案 | FREE |
        | 月費     | 0    |
      And 回應應包含 PRO、PRO_PLUS 與 ULTRA 方案的功能與 Claude 教練次數比較資訊

    Example: PRO_PLUS 用戶查看訂閱資訊時顯示下次扣款日與超高階教練剩餘額度
      When 使用者 "proplus@example.com" 查看訂閱管理頁
      Then 操作成功
      And 回應應包含：
        | 欄位         | 值         |
        | 當前方案     | PRO_PLUS   |
        | 月費         | 399        |
        | 下次扣款日   | 2024-02-01 |
        | 教練剩餘額度 | 200        |

  Rule: 後置（狀態）- 成功升級方案後神級 API 權限應立即生效

    Example: PRO 用戶升級至 PRO_PLUS 方案後立即解鎖 Claude 教練
      When 使用者 "pro@example.com" 完成 PRO_PLUS 方案訂閱付款
      Then 操作成功
      And 使用者 "pro@example.com" 的訂閱方案應更新為 "PRO_PLUS"
      And 系統立即配發 200 次 Claude 高階教練使用配額

  Rule: 後置（狀態）- 取消訂閱後當前週期結束前功能應維持可用

    Example: PRO_PLUS 用戶取消訂閱後到期前仍保有 Claude 權限
      When 使用者 "proplus@example.com" 取消訂閱
      Then 操作成功
      And 使用者 "proplus@example.com" 的訂閱狀態應更新為 "已取消待到期"
      And 使用者 "proplus@example.com" 在 2024-02-01 前仍可扣除並使用剩餘的 Claude 額度
