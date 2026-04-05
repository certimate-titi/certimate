Feature: 身分驗證

  # 訂閱方案 API enum 值：FREE | PRO_199 | ULTRA_399
  # 角色 API enum 值：USER | ADMIN

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                | 驗證方式 | 訂閱方案    | 角色  | 狀態   |
      | 1        | alice@example.com    | email    | FREE        | USER  | 已啟用 |
      | 2        | bob@example.com      | email    | PRO_199     | USER  | 已啟用 |
      | 3        | carol@example.com    | google   | ULTRA_399   | USER  | 已啟用 |
      | 4        | pending@example.com  | email    | FREE        | USER  | 待驗證 |
      | 5        | admin@example.com    | email    | FREE        | ADMIN | 已啟用 |

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

  Rule: 後置（狀態）- Email 驗證流程確認帳號啟用

    Example: 使用者點擊驗證連結後帳號應從待驗證變為已啟用
      Given 使用者 "pending@example.com" 帳號狀態為 "待驗證"
      When 使用者以有效驗證 token 確認 Email
      Then 操作成功
      And 該帳號狀態應更新為 "已啟用"

    Example: 使用過期或無效的驗證 token 時驗證失敗
      When 使用者以無效驗證 token 確認 Email
      Then 操作失敗
      And 錯誤訊息應為 "驗證連結無效或已過期"

    Example: 已啟用的帳號再次點擊驗證連結不應報錯
      Given 使用者 "alice@example.com" 帳號狀態為 "已啟用"
      When 使用者以有效驗證 token 確認 Email
      Then 操作成功
      And 該帳號狀態仍為 "已啟用"

  Rule: 後置（狀態）- 待驗證用戶可重新發送驗證信

    Example: 待驗證用戶請求重寄驗證信
      When 使用者以 Email "pending@example.com" 請求重寄驗證信
      Then 操作成功
      And 系統應發送帳號驗證信至 "pending@example.com"

    Example: 以不存在的 Email 請求重寄驗證信仍回傳成功
      When 使用者以 Email "nobody@example.com" 請求重寄驗證信
      Then 操作成功

  Rule: 後置（狀態）- Google SSO 登入可自動啟用待驗證帳號

    @manual
    Example: 待驗證用戶以相同 Email 透過 Google SSO 登入自動啟用帳號
      Given 使用者 "pending@example.com" 帳號狀態為 "待驗證"
      When 使用者透過 Google SSO 登入且 Email 為 "pending@example.com"
      Then 操作成功
      And 該帳號狀態應更新為 "已啟用"
      And 回應應包含有效的 JWT 存取憑證

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

    @manual
    Example: 首次以 Google 帳號登入時系統應自動建立新帳號
      When 使用者透過 Google SSO 登入且 Email 為 "new-google@example.com"
      Then 操作成功
      And 系統應建立新帳號，訂閱方案為 "FREE"，狀態為 "已啟用"
      And 使用者註冊方式應註記為 "Google SSO"
      And 回應應包含有效的 JWT 存取憑證

    @manual
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

  Rule: 後置（回應）- 登入後導覽列依 role 與 subscription_tier 顯示對應功能入口

    # DB: users.subscription_tier = 'ULTRA_1599' → 顯示「教育管理」連結 (/edu-console)
    # DB: users.role = 'ADMIN' → 顯示「平台管理」連結 (/super-admin/dashboard)

    Example: ULTRA_1599 用戶登入後導覽列顯示「教育管理」入口
      Given 使用者 "carol@example.com" 訂閱方案為 "ULTRA_1599"
      When 使用者 "carol@example.com" 成功登入系統
      Then 登入後的回應應包含 "subscription_tier": "ULTRA_1599"
      And 前端導覽列應顯示「教育管理」連結，路徑為 "/edu-console"
      And 前端導覽列不應顯示「平台管理」連結

    Example: ADMIN 角色用戶登入後導覽列顯示「平台管理」入口
      Given 使用者 "admin@example.com" 角色為 "ADMIN"
      When 使用者 "admin@example.com" 成功登入系統
      Then 登入後的回應應包含 "role": "ADMIN"
      And 前端導覽列應顯示「平台管理」連結，路徑為 "/super-admin/dashboard"
      And 前端導覽列不應顯示「教育後台」連結

    Example: FREE / PRO_199 一般用戶登入後導覽列不顯示管理入口
      Given 使用者 "alice@example.com" 訂閱方案為 "FREE" 且角色為 "USER"
      When 使用者 "alice@example.com" 成功登入系統
      Then 前端導覽列不應顯示「教育後台」連結
      And 前端導覽列不應顯示「後台管理」連結

  Rule: 前置（狀態）- 未登入使用者不得存取受保護頁面

    Scenario Outline: 未登入使用者存取受保護頁面時應導向登入頁
      Given 使用者尚未登入（無有效 JWT）
      When 使用者嘗試直接存取 "<頁面路徑>"
      Then 系統應自動導向至 "/login"

      Examples:
        | 頁面路徑                    |
        | /dashboard                  |
        | /knowledge                  |
        | /exam/setup                 |
        | /exam/workspace             |
        | /exam/results               |
        | /review                     |
        | /account                    |
        | /feedback                   |
        | /edu-console                |
        | /super-admin/dashboard      |
        | /super-admin/users          |
        | /super-admin/settings       |

    Example: 非管理員存取平台管理頁面時應導向儀表板
      Given 使用者 "alice@example.com" 角色為 "USER" 且已登入
      When 使用者嘗試直接存取 "/super-admin/dashboard"
      Then 系統應自動導向至 "/dashboard"

  Rule: 後置（狀態）- 刪除帳號時應同步清除所有快取與存儲資料 (Right to be Forgotten)

    Example: 使用者請求刪除帳號後系統徹底清空資料
      When 使用者 "alice@example.com" 執行 "刪除帳號" 操作
      Then 操作成功
      And 系統應從主資料庫中移除該使用者的所有個人資料與測驗記錄
      And 系統應同步清除 Redis 中所有與該使用者 ID 關聯的快取資料
      And 使用者上傳至雲端存儲 (GCS) 的實體檔案應被標記刪除或移除
      And 該使用者的所有 JWT 存取憑證應立即失效 (Revoked)

  # ========== UI 互動行為 ==========

  @ignore
  Rule: 前置（UI）- 登入頁「記住我」勾選框應保留登入狀態

    Example: 勾選「記住我」後成功登入，關閉瀏覽器後重新開啟仍保持登入狀態
      When 使用者在登入頁面勾選「記住我」
      And 使用者以 Email "alice@example.com" 和密碼 "Password1!" 進行登入
      Then 操作成功
      And 系統應將登入狀態持久化至本地儲存
      And 使用者關閉瀏覽器後重新開啟應仍為登入狀態

  @ignore
  Rule: 前置（UI）- 登入頁密碼欄位可切換顯示/隱藏

    Example: 點擊密碼可見性切換按鈕後密碼以明文顯示
      Given 使用者在登入頁面的密碼欄位輸入 "Password1!"
      When 使用者點擊密碼欄位的顯示/隱藏切換按鈕
      Then 密碼欄位應從遮蔽模式切換為明文顯示模式

    Example: 再次點擊密碼可見性切換按鈕後密碼恢復遮蔽
      Given 使用者在登入頁面的密碼欄位輸入 "Password1!"
      And 密碼欄位目前為明文顯示模式
      When 使用者點擊密碼欄位的顯示/隱藏切換按鈕
      Then 密碼欄位應從明文顯示模式切換為遮蔽模式

  @ignore
  Rule: 前置（UI）- 註冊頁密碼欄位可切換顯示/隱藏

    Example: 註冊頁點擊密碼可見性切換按鈕後密碼以明文顯示
      Given 使用者在註冊頁面的密碼欄位輸入 "CertiMate#2024"
      When 使用者點擊密碼欄位的顯示/隱藏切換按鈕
      Then 密碼欄位應從遮蔽模式切換為明文顯示模式

  @ignore
  Rule: 前置（UI）- 註冊頁密碼強度指示條依密碼強度顯示對應等級

    Scenario Outline: 密碼強度指示條依輸入的密碼顯示對應等級
      When 使用者在註冊頁面輸入密碼 "<密碼>"
      Then 密碼強度指示條應顯示 "<等級>"

      Examples:
        | 密碼           | 等級 |
        | abc            | 弱   |
        | password1      | 中   |
        | CertiMate#2024 | 強   |

  @ignore
  Rule: 前置（UI）- 註冊頁服務條款彈窗可開啟與關閉

    Example: 點擊「服務條款」連結開啟服務條款彈窗
      When 使用者在註冊頁面點擊「服務條款」連結
      Then 系統應顯示服務條款彈窗
      And 彈窗內容應包含服務條款全文

    Example: 關閉服務條款彈窗後回到註冊頁面
      Given 使用者已開啟服務條款彈窗
      When 使用者點擊彈窗的關閉按鈕
      Then 服務條款彈窗應關閉
      And 使用者應回到註冊頁面

  @ignore
  Rule: 前置（UI）- 註冊頁隱私權政策彈窗可開啟與關閉

    Example: 點擊「隱私權政策」連結開啟隱私權政策彈窗
      When 使用者在註冊頁面點擊「隱私權政策」連結
      Then 系統應顯示隱私權政策彈窗
      And 彈窗內容應包含隱私權政策全文

    Example: 關閉隱私權政策彈窗後回到註冊頁面
      Given 使用者已開啟隱私權政策彈窗
      When 使用者點擊彈窗的關閉按鈕
      Then 隱私權政策彈窗應關閉
      And 使用者應回到註冊頁面

  @ignore
  Rule: 前置（參數）- 忘記密碼頁面 Email 為空時不可送出

    Example: 忘記密碼頁面未輸入 Email 時送出按鈕應為停用狀態
      When 使用者在忘記密碼頁面未輸入任何 Email
      Then 送出按鈕應為停用狀態，無法點擊

    Example: 忘記密碼頁面清空已輸入的 Email 後送出按鈕恢復停用
      Given 使用者在忘記密碼頁面已輸入 "alice@example.com"
      When 使用者清空 Email 欄位
      Then 送出按鈕應為停用狀態，無法點擊

  @ignore
  Rule: 後置（UI）- 忘記密碼成功送出後顯示確認資訊

    Example: 忘記密碼成功送出後頁面顯示寄送確認訊息與輸入的 Email
      When 使用者以 Email "alice@example.com" 申請密碼重設
      Then 操作成功
      And 頁面應顯示密碼重設信已寄出的確認訊息
      And 確認訊息中應包含使用者輸入的 Email "alice@example.com"
      And 頁面應提供返回登入頁面的連結

  @ignore
  Rule: 後置（UI）- 驗證信寄出頁面重寄按鈕有 60 秒冷卻倒數

    Example: 驗證信寄出後重寄按鈕進入 60 秒冷卻倒數
      Given 使用者已完成註冊並進入驗證信寄出頁面
      When 使用者點擊「重新寄送驗證信」按鈕
      Then 操作成功
      And 重寄按鈕應進入 60 秒冷卻倒數狀態
      And 倒數期間按鈕應顯示剩餘秒數且無法點擊

    Example: 冷卻倒數結束後重寄按鈕恢復可點擊
      Given 使用者已點擊「重新寄送驗證信」且冷卻倒數已結束
      Then 重寄按鈕應恢復為可點擊狀態

  @ignore
  Rule: 後置（狀態）- 登入頁支援 Google SSO 一鍵登入流程

    Example: 使用者點擊 Google 登入按鈕後導向 Google OAuth 授權頁面
      When 使用者在登入頁面點擊「以 Google 帳號登入」按鈕
      Then 系統應導向 Google OAuth 授權頁面

    Example: Google OAuth 授權成功後系統自動完成登入並導向儀表板
      Given 使用者 "carol@example.com" 已有 Google SSO 帳號且狀態為 "已啟用"
      When 使用者完成 Google OAuth 授權且 Email 為 "carol@example.com"
      Then 操作成功
      And 回應應包含有效的 JWT 存取憑證
      And 系統應導向至 "個人儀表板首頁"
