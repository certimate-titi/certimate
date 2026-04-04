@ignore @command
Feature: 付款後自動更新使用者角色與權限

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                  | 訂閱方案 | 訂閱狀態 | 角色 |
      | 1        | free@example.com       | FREE     | 無       | user |
      | 2        | pro@example.com        | PRO_199  | active   | user |
    And 系統中有以下方案權限對照表：
      | 方案          | 角色    | AI 對話次數/日 | 上傳數/月 | 考試數/月 | Vision OCR/月 | 高階教練 |
      | FREE          | user    | 3              | 5         | 10        | 0             | 否       |
      | PRO_199       | user    | 30             | 50        | 100       | 0             | 否       |
      | PRO_PLUS_399  | user    | 200            | 200       | 500       | 50            | 是       |
      | ULTRA_1599    | user    | 無限           | 無限      | 無限      | 500           | 是       |
      | EDU           | student | 5              | 0         | 無限      | 0             | 否       |

  # ========== 升級觸發 ==========

  Rule: 後置（狀態）- 綠界付款成功回呼應自動觸發訂閱升級

    Example: FREE 升級至 PRO_199 後權限即時生效
      Given 使用者 "free@example.com" 已建立 PRO_199 付款訂單
      When 系統收到綠界付款成功回呼 (RtnCode=1)
      Then 使用者 "free@example.com" 的訂閱方案應更新為 "PRO_199"
      And 使用者 "free@example.com" 的訂閱狀態應更新為 "active"
      And 使用者 "free@example.com" 的每日 AI 對話限額應從 3 提升至 30
      And 使用者 "free@example.com" 的每月上傳限額應從 5 提升至 50
      And 使用者 "free@example.com" 的每月考試限額應從 10 提升至 100

    Example: PRO_199 升級至 PRO_PLUS_399 後解鎖高階教練
      Given 使用者 "pro@example.com" 已建立 PRO_PLUS_399 付款訂單
      When 系統收到綠界付款成功回呼 (RtnCode=1)
      Then 使用者 "pro@example.com" 的訂閱方案應更新為 "PRO_PLUS_399"
      And 使用者 "pro@example.com" 應解鎖高階教練功能
      And 使用者 "pro@example.com" 的 Vision OCR 額度應為 50

  # ========== Firebase 同步 ==========

  Rule: 後置（同步）- 訂閱變更後應同步 Firebase Custom Claims

    Example: 升級後 Firebase Custom Claims 同步更新
      Given 使用者 "free@example.com" 的 Firebase Custom Claims 為 { "plan": "FREE" }
      When 系統處理完付款成功回呼並升級至 PRO_199
      Then Firebase Custom Claims 應更新為 { "plan": "PRO_199", "subscription_status": "active" }
      And 前端在下次 Token Refresh 時應取得新的 Claims

    Example: 降級後 Firebase Custom Claims 同步更新
      Given 使用者 "pro@example.com" 的訂閱已到期且自動降級為 FREE
      Then Firebase Custom Claims 應更新為 { "plan": "FREE", "subscription_status": "expired" }

  # ========== 額度重置 ==========

  Rule: 後置（排程）- 每月扣款日應自動重置用量額度

    Example: 月度續訂成功後重置當月用量
      Given 使用者 "pro@example.com" 當月已使用 AI 對話 25 次
      When 系統在下次扣款日成功續訂
      Then 使用者 "pro@example.com" 的 AI 對話已使用次數應重置為 0
      And 使用者 "pro@example.com" 的上傳已使用次數應重置為 0

  # ========== 異常處理 ==========

  Rule: 後置（異常）- 付款成功但訂閱更新失敗時應記錄並告警

    Example: 資料庫更新失敗時交易紀錄應標記為需人工處理
      Given 使用者 "free@example.com" 已建立 PRO_199 付款訂單
      When 系統收到綠界付款成功回呼 (RtnCode=1) 但資料庫更新拋出異常
      Then 交易紀錄 status 應標記為 "paid_but_not_activated"
      And 系統應發送告警通知至管理員 Email
      And 系統應記錄錯誤日誌，包含 user_id、交易編號與錯誤訊息

  Rule: 後置（審計）- 所有權限變更應記錄審計日誌

    Example: 升級操作記錄審計日誌
      When 系統處理完 "free@example.com" 的升級至 PRO_199
      Then 系統應記錄審計日誌：
        | 欄位           | 值                                 |
        | action         | subscription_upgrade               |
        | user_id        | 1                                  |
        | previous_plan  | FREE                               |
        | new_plan       | PRO_199                            |
        | trigger        | ecpay_callback                     |
        | transaction_id | (對應的 merchant_trade_no)          |

  # ========== EDU 學生方案權限 ==========

  Rule: 後置（狀態）- 機構管理員匯入學生後學生帳號自動設定為 EDU 方案

    Example: CSV 匯入學生後帳號自動指派 EDU 方案
      Given 使用者 "free@example.com" 被機構管理員透過 CSV 匯入至機構 1
      Then 使用者 "free@example.com" 的訂閱方案應更新為 "EDU"
      And 使用者 "free@example.com" 的角色應更新為 "student"
      And 使用者 "free@example.com" 的每日 AI 對話限額應為 5
      And 使用者 "free@example.com" 不可上傳資源
      And 使用者 "free@example.com" 不可自主出題

  Rule: 後置（狀態）- EDU 學生退出機構後自動降級為 FREE

    Example: 學生被移除出機構後降為 FREE
      Given 使用者 "free@example.com" 目前為機構 1 的 EDU 學生
      When 機構管理員將使用者 "free@example.com" 從機構 1 移除
      Then 使用者 "free@example.com" 的訂閱方案應自動降級為 "FREE"
      And 使用者 "free@example.com" 的角色應更新為 "user"

    Example: 機構退訂 ULTRA 後所有 EDU 學生降為 FREE
      Given 機構 1 的管理員訂閱方案為 "ULTRA_1599"
      And 機構 1 有 2 名 EDU 學生
      When 機構 1 的管理員取消 ULTRA 訂閱且到期日已過
      Then 機構 1 所有 EDU 學生的訂閱方案應自動降級為 "FREE"
