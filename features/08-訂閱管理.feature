@ignore
Feature: 訂閱管理

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                  | 訂閱方案 | 訂閱狀態    | 下次扣款日 | 月費 |
      | 1        | free@example.com       | FREE     | 無          | null       | 0    |
      | 2        | pro@example.com        | PRO      | 訂閱中      | 2024-02-01 | 199  |
      | 3        | ultra@example.com      | ULTRA    | 訂閱中      | 2024-02-01 | 499  |
      | 4        | cancelled@example.com  | PRO      | 已取消待到期 | 2024-01-31 | 199  |
    And 系統中有以下帳單記錄：
      | 帳單 ID | 使用者 ID | 金額 | 狀態   | 建立時間            |
      | 1       | 2        | 199  | 已支付 | 2024-01-01 00:00:00 |
      | 2       | 2        | 199  | 已支付 | 2023-12-01 00:00:00 |
      | 3       | 3        | 499  | 已支付 | 2024-01-01 00:00:00 |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 已為相同方案的用戶不可重複訂閱

    Example: PRO 用戶嘗試再次訂閱 PRO 方案失敗
      When 使用者 "pro@example.com" 訂閱 PRO 方案
      Then 操作失敗
      And 錯誤訊息應為 "您已訂閱此方案"

  Rule: 前置（狀態）- 降級方案須在當前訂閱週期結束後生效

    Example: ULTRA 用戶申請降級至 PRO 方案時收到到期日提示
      When 使用者 "ultra@example.com" 申請變更方案至 PRO
      Then 操作成功
      And 回應應包含：
        | 欄位         | 值                        |
        | 降級生效日期 | 2024-02-01                |
        | 提示訊息     | 降級將於下一計費週期生效  |

  # ========== 後置條件 ==========

  Rule: 後置（回應）- 查看訂閱資訊應回傳當前方案、下次扣款日與功能比較

    Example: FREE 用戶查看訂閱資訊時顯示升級提示
      When 使用者 "free@example.com" 查看訂閱管理頁
      Then 操作成功
      And 回應應包含：
        | 欄位     | 值   |
        | 當前方案 | FREE |
        | 月費     | 0    |
      And 回應應包含 PRO 與 ULTRA 方案的功能比較資訊

    Example: PRO 用戶查看訂閱資訊時顯示下次扣款日
      When 使用者 "pro@example.com" 查看訂閱管理頁
      Then 操作成功
      And 回應應包含：
        | 欄位       | 值         |
        | 當前方案   | PRO        |
        | 月費       | 199        |
        | 下次扣款日 | 2024-02-01 |

  Rule: 後置（狀態）- 成功升級方案後功能權限應立即生效

    Example: FREE 用戶升級至 PRO 方案後立即獲得 PRO 功能權限
      When 使用者 "free@example.com" 完成 PRO 方案訂閱付款
      Then 操作成功
      And 使用者 "free@example.com" 的訂閱方案應更新為 "PRO"
      And 使用者 "free@example.com" 每次測驗題數上限應更新為 50

  Rule: 後置（狀態）- 取消訂閱後當前週期結束前功能應維持可用

    Example: PRO 用戶取消訂閱後到期前仍保有 PRO 功能權限
      When 使用者 "pro@example.com" 取消訂閱
      Then 操作成功
      And 使用者 "pro@example.com" 的訂閱狀態應更新為 "已取消待到期"
      And 使用者 "pro@example.com" 在 2024-02-01 前每次測驗題數上限應仍為 50

  Rule: 後置（回應）- 帳單歷史應回傳按建立時間倒序排列的支付記錄與發票下載連結

    Example: PRO 用戶查看帳單歷史取得完整記錄
      When 使用者 "pro@example.com" 查看帳單歷史
      Then 操作成功
      And 帳單清單應包含以下記錄，依建立時間倒序排列：
        | 帳單 ID | 金額 | 狀態   | 建立時間            |
        | 1       | 199  | 已支付 | 2024-01-01 00:00:00 |
        | 2       | 199  | 已支付 | 2023-12-01 00:00:00 |
      And 每筆帳單應包含有效的發票下載連結
