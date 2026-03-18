Feature: 身分驗證

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                | 驗證方式 | 訂閱方案 | 狀態   |
      | 1        | alice@example.com    | email    | FREE     | 已啟用 |
      | 2        | bob@example.com      | email    | PRO      | 已啟用 |
      | 3        | carol@example.com    | google   | ULTRA    | 已啟用 |
      | 4        | pending@example.com  | email    | FREE     | 待驗證 |

  # ========== 前置條件 ==========

  Rule: 前置（參數）- 電子郵件格式必須合法

    Scenario Outline: 以不合法格式的 Email 註冊失敗
      When 使用者以 Email "<email>" 和密碼 "ValidPass1!" 進行註冊
      Then 操作失敗
      And 錯誤訊息應為 "電子郵件格式無效"

      Examples:
        | email            |
        | notanemail       |
        | missing@         |
        | @nodomain.com    |
        | double@@test.com |

  Rule: 前置（參數）- 密碼強度必須達到最低要求

    Scenario Outline: 以強度不足的密碼註冊失敗
      When 使用者以 Email "newuser@example.com" 和密碼 "<密碼>" 進行註冊
      Then 操作失敗
      And 錯誤訊息應為 "密碼強度不足"

      Examples:
        | 密碼      |
        | abc       |
        | password  |
        | PASSWORD1 |

    Example: 密碼強度達標時密碼強度指示條顯示「強」
      When 使用者輸入密碼 "CertiMate#2024"
      Then 密碼強度指示條應顯示 "強"

  Rule: 前置（狀態）- 已存在的 Email 不可重複註冊

    Example: 使用已註冊的 Email 再次註冊失敗
      When 使用者以 Email "alice@example.com" 和密碼 "NewPass1!" 進行註冊
      Then 操作失敗
      And 錯誤訊息應為 "此電子郵件已被註冊"

  Rule: 前置（狀態）- 登入時帳號必須存在且為已啟用狀態

    Example: 以不存在的 Email 登入失敗
      When 使用者以 Email "nobody@example.com" 和密碼 "Password1!" 進行登入
      Then 操作失敗
      And 錯誤訊息應為 "帳號或密碼錯誤"

    Example: 以待驗證帳號登入失敗
      When 使用者以 Email "pending@example.com" 和密碼 "Pending1!" 進行登入
      Then 操作失敗
      And 錯誤訊息應為 "帳號尚未驗證，請查收啟用信件"

  Rule: 前置（參數）- 登入密碼必須與帳號相符

    Example: 密碼錯誤時登入失敗
      When 使用者以 Email "alice@example.com" 和密碼 "WrongPass!" 進行登入
      Then 操作失敗
      And 錯誤訊息應為 "帳號或密碼錯誤"

  # ========== 後置條件 ==========

  Rule: 後置（狀態）- 成功註冊後應建立 FREE 方案帳號並發送驗證信

    Example: 以合法 Email 和強密碼成功完成註冊
      When 使用者以 Email "newuser@example.com" 和密碼 "CertiMate#2024" 進行註冊
      Then 操作成功
      And 系統應建立新帳號，訂閱方案為 "FREE"，狀態為 "待驗證"
      And 系統應發送帳號驗證信至 "newuser@example.com"

  Rule: 後置（回應）- 成功登入後應回傳 JWT 存取憑證與使用者資訊

    Example: 以正確帳密成功登入
      When 使用者以 Email "alice@example.com" 和密碼 "Password1!" 進行登入
      Then 操作成功
      And 回應應包含有效的 JWT 存取憑證
      And 回應中的使用者資訊應包含：
        | 欄位     | 值                |
        | email    | alice@example.com |
        | 訂閱方案 | FREE              |

  Rule: 後置（狀態）- 忘記密碼流程應發送重設連結且連結有效期為 1 小時

    Example: 以已存在的 Email 申請密碼重設
      When 使用者以 Email "alice@example.com" 申請密碼重設
      Then 操作成功
      And 系統應發送密碼重設信至 "alice@example.com"
      And 重設連結應在 1 小時後失效

    Example: 以不存在的 Email 申請密碼重設仍回傳成功以防止帳號列舉攻擊
      When 使用者以 Email "ghost@example.com" 申請密碼重設
      Then 操作成功
      And 系統不應洩漏該帳號是否存在的資訊
