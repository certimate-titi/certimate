@frontend @command
Feature: 綠界金流串接 (ECPay Integration)

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                  | 訂閱方案 | 訂閱狀態 |
      | 1        | free@example.com       | FREE     | 無       |
      | 2        | pro@example.com        | PRO_199  | active   |
    And 系統中有以下綠界金流設定：
      | 設定          | 值                     |
      | MerchantID    | 3002607                |
      | HashKey       | pwFHCqoQZGmho4w6        |
      | HashIV        | EkRm7iFT261dpevs        |
      | 環境          | Stage (測試)            |
    And 目前時間為 "2026-03-26 10:00:00"

  # ========== 前置條件 ==========

  Rule: 前置（認證）- 未登入用戶無法建立付款訂單

    Example: 未登入用戶嘗試建立付款訂單失敗
      When 未認證用戶發送建立付款訂單請求，目標方案為 "PRO_199"
      Then 操作失敗，錯誤為「未認證，請先登入」
      And HTTP 狀態碼應為 401

  Rule: 前置（參數）- 建立付款訂單必須提供合法目標方案

    Example: 提供無效方案名稱時建立訂單失敗
      When 使用者 "free@example.com" 建立付款訂單，目標方案為 "INVALID_PLAN"
      Then 操作失敗，錯誤為「無效的訂閱方案」

    Example: 已訂閱相同方案時建立訂單失敗
      When 使用者 "pro@example.com" 建立付款訂單，目標方案為 "PRO_199"
      Then 操作失敗，錯誤為「您已訂閱此方案，無須重複付款」

  # ========== 建立付款訂單 ==========

  Rule: 後置（回應）- 建立訂單成功後回傳綠界所需的表單參數

    Example: FREE 用戶建立 PRO_199 付款訂單成功
      When 使用者 "free@example.com" 建立付款訂單，目標方案為 "PRO_199"
      Then 操作成功
      And 回應應包含綠界表單參數：
        | 欄位               | 值                                       |
        | MerchantID         | 3002607                                  |
        | MerchantTradeNo    | (系統產生的唯一交易編號，長度 <= 20)      |
        | MerchantTradeDate  | 2026/03/26 10:00:00                      |
        | TotalAmount        | 199                                      |
        | TradeDesc          | CertiMate PRO_199 訂閱                   |
        | ItemName           | CertiMate PRO_199 月訂閱方案             |
        | PaymentType        | aio                                      |
        | ChoosePayment      | ALL                                      |
        | EncryptType        | 1                                        |
      And 回應應包含有效的 CheckMacValue
      And 回應應包含 ReturnURL 指向後端回呼端點
      And 回應應包含 OrderResultURL 指向前端付款結果頁

    Example: 建立訂單時系統應同步建立 pending 狀態的交易紀錄
      When 使用者 "free@example.com" 建立付款訂單，目標方案為 "PRO_199"
      Then 操作成功
      And 資料庫中應新增一筆交易紀錄：
        | 欄位               | 值                    |
        | user_id            | 1                     |
        | target_plan        | PRO_199               |
        | amount             | 199                   |
        | status             | pending               |
        | payment_provider   | ecpay                 |

  # ========== CheckMacValue 驗證 ==========

  Rule: 後置（安全）- CheckMacValue 計算應符合綠界 SHA256 規範

    Example: CheckMacValue 計算結果與綠界官方範例一致
      Given 以下綠界交易參數：
        | 欄位               | 值                    |
        | MerchantID         | 3002607               |
        | MerchantTradeNo    | TEST20260326100000    |
        | MerchantTradeDate  | 2026/03/26 10:00:00   |
        | TotalAmount        | 199                   |
        | TradeDesc          | Test                  |
        | ItemName           | TestItem              |
        | PaymentType        | aio                   |
        | ChoosePayment      | ALL                   |
        | EncryptType        | 1                     |
        | ReturnURL          | https://example.com/callback |
      When 系統以 HashKey "pwFHCqoQZGmho4w6" 和 HashIV "EkRm7iFT261dpevs" 計算 CheckMacValue
      Then 計算流程應為：
        """
        1. 將參數依照 key 名稱升冪排序
        2. 前綴 HashKey=，後綴 &HashIV=
        3. URL Encode（小寫）
        4. SHA256 後轉大寫
        """
      And 結果應為有效的 64 字元大寫十六進位字串

  # ========== 綠界回呼處理 (ReturnURL) ==========

  Rule: 後置（安全）- 回呼端點必須驗證 CheckMacValue 防止偽造

    Example: CheckMacValue 驗證失敗時拒絕處理
      When 綠界發送回呼至 ReturnURL，但 CheckMacValue 為無效值 "FAKECHECKSUM"
      Then 操作失敗
      And 回應應為 "0|CheckMacValue verification failed"
      And 交易紀錄狀態不應變更

  Rule: 後置（狀態）- 付款成功回呼應更新交易紀錄與使用者訂閱

    Example: 收到綠界付款成功通知後更新使用者訂閱
      Given 資料庫中有 pending 交易紀錄：
        | merchant_trade_no  | user_id | target_plan | amount | status  |
        | CRT20260326100001  | 1       | PRO_199     | 199    | pending |
      When 綠界發送回呼至 ReturnURL：
        | 欄位               | 值                   |
        | MerchantTradeNo    | CRT20260326100001    |
        | RtnCode            | 1                    |
        | TradeNo            | 2026032610001234     |
        | TradeAmt            | 199                  |
        | PaymentType        | Credit_CreditCard    |
        | CheckMacValue      | (有效的 CheckMacValue) |
      Then 回應應為 "1|OK"
      And 交易紀錄 "CRT20260326100001" 應更新為：
        | 欄位               | 值                   |
        | status             | success              |
        | trade_no           | 2026032610001234     |
        | payment_type       | Credit_CreditCard    |
        | rtn_code           | 1                    |
      And 使用者 1 的訂閱方案應更新為 "PRO_199"
      And 使用者 1 的訂閱狀態應更新為 "active"
      And 使用者 1 的下次扣款日應設為 "2026-04-26"

    Example: 收到綠界付款失敗通知後僅更新交易紀錄
      Given 資料庫中有 pending 交易紀錄：
        | merchant_trade_no  | user_id | target_plan | amount | status  |
        | CRT20260326100002  | 1       | PRO_199     | 199    | pending |
      When 綠界發送回呼至 ReturnURL：
        | 欄位               | 值                   |
        | MerchantTradeNo    | CRT20260326100002    |
        | RtnCode            | 10100058             |
        | CheckMacValue      | (有效的 CheckMacValue) |
      Then 回應應為 "1|OK"
      And 交易紀錄 "CRT20260326100002" 的 status 應為 "failed"
      And 使用者 1 的訂閱方案應維持 "FREE"

  Rule: 後置（冪等）- 重複收到相同交易回呼不應重複處理

    Example: 同一筆交易的重複回呼應忽略
      Given 交易紀錄 "CRT20260326100001" 的 status 已為 "success"
      When 綠界再次發送相同的回呼至 ReturnURL
      Then 回應應為 "1|OK"
      And 使用者 1 的訂閱紀錄不應被重複修改
