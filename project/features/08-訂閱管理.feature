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

  # ========== EDU 學生方案 ==========

  Rule: 後置（回應）- EDU 方案應出現在方案權限對照表中

    Example: 查看訂閱資訊時 EDU 方案列於比較表中
      When 使用者 "free@example.com" 查看訂閱管理頁
      Then 操作成功
      And 回應應包含各方案額度比較：
        | 方案          | AI 對話次數 | 上傳數 | 考試數 | Vision OCR | 自主出題 | 高階教練 |
        | FREE          | 3           | 5      | 10     | 0          | 是       | 否       |
        | PRO_199       | 30          | 50     | 100    | 0          | 是       | 否       |
        | PRO_PLUS_399  | 200         | 200    | 500    | 50         | 是       | 是       |
        | ULTRA_1599    | 無限        | 無限   | 無限   | 500        | 是       | 是       |
        | EDU           | 5           | 0      | 無限   | 0          | 否       | 否       |

  Rule: 後置（狀態）- EDU 方案僅可由機構管理員透過 CSV 匯入或邀請指派，不可自行訂閱

    Example: 一般用戶嘗試訂閱 EDU 方案失敗
      When 使用者 "free@example.com" 訂閱 "EDU" 方案
      Then 操作失敗，錯誤為「EDU 方案僅限機構管理員指派，無法自行訂閱」

  # ========== 14 天免費試用 ==========

  Rule: 前置（狀態）- 每個帳號僅可使用一次 ULTRA 免費試用

    Example: 首次啟用 ULTRA 14 天試用成功
      When 使用者 "free@example.com" 啟用 ULTRA 14 天免費試用
      Then 操作成功
      And 使用者 "free@example.com" 的訂閱方案應為 "ULTRA_1599"
      And 使用者 "free@example.com" 的訂閱狀態應為 "trial"
      And 使用者 "free@example.com" 的試用到期日應為啟用日起第 14 天

    Example: 已使用過試用的用戶再次啟用失敗
      Given 使用者 "pro@example.com" 已使用過 ULTRA 免費試用
      When 使用者 "pro@example.com" 啟用 ULTRA 14 天免費試用
      Then 操作失敗，錯誤為「您已使用過免費試用，請直接訂閱」

  Rule: 後置（狀態）- 試用到期後應自動降回原方案

    Example: 試用到期後自動降回 FREE
      Given 使用者 "free@example.com" 的 ULTRA 試用將於 2026-04-01 到期
      And 使用者 "free@example.com" 試用前的方案為 "FREE"
      When 系統執行試用到期檢查排程，當前日期為 2026-04-01
      Then 使用者 "free@example.com" 的訂閱方案應自動降級為 "FREE"
      And 使用者 "free@example.com" 的訂閱狀態應為 "無"

    Example: 試用期間轉為正式訂閱後不再觸發降級
      Given 使用者 "free@example.com" 正在 ULTRA 試用中
      When 使用者 "free@example.com" 完成 "ULTRA_1599" 方案訂閱付款
      Then 使用者 "free@example.com" 的訂閱狀態應更新為 "active"
      And 系統不應在原試用到期日觸發降級

  Rule: 後置（回應）- 試用期間應顯示剩餘天數提示

    Example: 試用中查看訂閱資訊取得剩餘天數
      Given 使用者 "free@example.com" 正在 ULTRA 試用中，剩餘 7 天
      When 使用者 "free@example.com" 查看訂閱管理頁
      Then 操作成功
      And 回應應包含：
        | 欄位                | 值          |
        | current_plan        | ULTRA_1599  |
        | subscription_status | trial       |
        | trial_days_left     | 7           |

  # ========== Fair Use Policy（公平使用限制）==========

  Rule: 後置（狀態）- ULTRA 無限配額應設有 soft cap 防濫用機制

    Example: 單日 AI 呼叫超過 1000 次觸發 soft cap 告警
      Given 使用者 "ultra@example.com" 今日已使用 AI 對話 1000 次
      When 使用者 "ultra@example.com" 發起第 1001 次 AI 對話
      Then 操作成功（不阻斷使用者）
      And 系統應記錄 soft cap 告警日誌，包含 user_id 與當日用量

    Example: 連續 3 天觸發 soft cap 後系統通知管理員
      Given 使用者 "ultra@example.com" 連續 3 天觸發 soft cap 告警
      When 系統執行每日 FUP 檢查排程
      Then 系統應發送告警通知至管理員 Email
      And 告警內容應包含使用者 Email 與連續觸發天數
