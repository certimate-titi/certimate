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

  Rule: 前置（狀態）- 註冊時必須同意服務條款與隱私權宣告

    Example: 使用者未勾選同意條款註冊失敗
      When 使用者以 Email "new@example.com" 和密碼 "ValidPass1!" 進行註冊，但未勾選同意「服務條款與隱私權宣告」
      Then 操作失敗
      And 錯誤訊息應為 "請閱讀並同意服務條款與隱私權政策"

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

  Rule: 後置（狀態）- 支援第三方 OAuth 登入 (Google SSO)

    Example: 首次以 Google 帳號登入時系統應自動建立新帳號
      When 使用者透過 Google SSO 登入且 Email 為 "new-google@example.com"
      Then 操作成功
      And 系統應建立新帳號，訂閱方案為 "FREE"，狀態為 "已啟用"
      And 使用者註冊方式應註記為 "Google SSO"
      And 回應應包含有效的 JWT 存取憑證

    Example: 已註冊過 Email 密碼的使用者，若與 Google SSO 綁定同一 Email，應成功登入並關聯身分
      Given 使用者 "alice@example.com" 原本為 Email/密碼註冊方式
      When 使用者透過 Google SSO 登入且 Email 為 "alice@example.com"
      Then 操作成功
      And 登入成功不會報錯
      And 該帳號的註冊方式應允許或更新關聯 "Google SSO"
      And 回應應包含有效的 JWT 存取憑證

  Rule: 後置（狀態）- 首次登入應導向 Onboarding 引導流程

    Example: 新用戶首次登入後系統自動導向 Onboarding 頁面
      Given 使用者 "newuser@example.com" 已完成註冊驗證
      And 該使用者尚未建立任何學習歷程
      When 使用者以 Email "newuser@example.com" 和密碼 "CertiMate#2024" 進行登入
      Then 操作成功
      And 回應應包含有效的 JWT 存取憑證
      And 系統應導向至 "首次登入引導頁"

    Example: 已完成 Onboarding 的使用者登入後直接導向儀表板
      Given 使用者 "alice@example.com" 已建立至少一個備考科目的學習歷程
      When 使用者以 Email "alice@example.com" 和密碼 "Password1!" 進行登入
      Then 操作成功
      And 系統應導向至 "個人儀表板首頁"

  Rule: 後置（狀態）- 刪除帳號時應同步清除所有快取與存儲資料 (Right to be Forgotten)

    Example: 使用者請求刪除帳號後系統徹底清空資料
      When 使用者 "alice@example.com" 執行 "刪除帳號" 操作
      Then 操作成功
      And 系統應從主資料庫中移除該使用者的所有個人資料與測驗記錄
      And 系統應同步清除 Redis 中所有與該使用者 ID 關聯的快取資料
      And 使用者上傳至雲端存儲 (GCS) 的實體檔案應被標記刪除或移除
      And 該使用者的所有 JWT 存取憑證應立即失效 (Revoked)
