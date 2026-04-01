@query
Feature: 個人儀表板與成就系統

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 | Onboarding |
      | 1        | alice@example.com  | FREE     | true       |
    And 使用者 "alice@example.com" 備考以下科目：
      | 科目     | 考試日期   |
      | AWS SAA  | 2026-06-15 |
      | TOEIC    | 2026-09-01 |

  # ========== 前置（參數）- 儀表板查詢必須有至少一個備考科目 ==========

  Rule: 前置（參數）- 儀表板查詢必須有至少一個備考科目

    Example: 無備考科目的用戶查看儀表板顯示引導
      Given 使用者 "alice@example.com" 尚未設定任何備考科目
      When 使用者 "alice@example.com" 查看儀表板
      Then 操作成功
      And 頁面應顯示「請至少新增一個備考科目」引導提示

  # ========== 科目切換器 ==========

  Rule: 後置（回應）- 儀表板應顯示科目切換器與核心學習組件

    Example: 備考多科時顯示科目切換器
      When 使用者 "alice@example.com" 查看儀表板
      Then 操作成功
      And 科目切換器應包含：
        | 科目    |
        | AWS SAA |
        | TOEIC   |
      And 頁面應顯示「+ 新增備考科目」入口
      And 預設顯示 "AWS SAA" 的學習數據

    Example: 切換科目後儀表板數據更新
      Given 使用者 "alice@example.com" 目前在儀表板檢視 "AWS SAA"
      When 使用者 "alice@example.com" 切換至 "TOEIC"
      Then 操作成功
      And 回應中的考試倒數應對應 "TOEIC" 的考試日期 2026-09-01
      And 回應中的雷達圖應對應 "TOEIC" 的能力分布

  # ========== 儀表板組件 ==========

  Rule: 後置（回應）- 儀表板應包含考試倒數、雷達圖、快速上傳區與待辦提醒

    Example: 查看儀表板取得完整組件資料
      When 使用者 "alice@example.com" 查看儀表板，科目為 "AWS SAA"
      Then 操作成功
      And 回應應包含以下組件：
        | 組件              | 說明                         |
        | exam_countdown    | 距考試日期剩餘天數           |
        | radar_chart       | 各知識節點的能力分布         |
        | quick_upload      | 快速上傳資源入口             |
        | todo_reminders    | 待複習錯題與未完成考卷       |

  # ========== 個人資料 ==========

  Rule: 後置（狀態）- 編輯個人資料應更新顯示名稱與 AI 教練參考資訊

    Example: 更新個人資料成功
      When 使用者 "alice@example.com" 更新個人資料：
        | 欄位         | 值           |
        | display_name | 愛麗絲       |
        | age          | 28           |
        | education    | 資訊工程碩士 |
        | career       | 軟體開發     |
      Then 操作成功
      And 使用者 "alice@example.com" 的顯示名稱應為 "愛麗絲"

  # ========== 以下為複雜/事件驅動功能，標記 @ignore ==========

  @ignore
  Rule: 後置（狀態）- 每日登入並學習應累積連勝天數

    @ignore
    Example: 連續第 3 天登入並完成測驗後連勝更新
      Given 使用者 "alice@example.com" 目前連勝為 2 天
      When 使用者 "alice@example.com" 今日登入並完成一次測驗
      Then 使用者 "alice@example.com" 的連勝應為 3 天

  @ignore
  Rule: 後置（狀態）- 每日首次登入應自動產生 1-3 個微任務

    @ignore
    Example: 登入後收到每日微任務
      When 使用者 "alice@example.com" 今日首次登入
      Then 系統應產生 1 至 3 個每日微任務

  @ignore
  Rule: 後置（狀態）- 達成特定里程碑時應頒發成就徽章

    @ignore
    Example: 首次上傳資源獲得播種者徽章
      When 使用者 "alice@example.com" 首次成功上傳一份資源
      Then 使用者 "alice@example.com" 應獲得成就徽章：
        | 欄位   | 值           |
        | key    | first_upload |
        | name   | 播種者       |

  @ignore
  Rule: 後置（狀態）- 上傳頭像後應全站同步更新

    @ignore
    Example: 更新頭像成功
      When 使用者 "alice@example.com" 上傳新頭像
      Then 操作成功
      And 回應應包含新頭像的 URL

  # ========== 檔案拖放上傳 ==========

  @ignore
  Rule: 後置（狀態）- 儀表板快速上傳區支援拖放上傳 PDF/MD/TXT 檔案

    @ignore
    Example: 檔案拖放上傳 PDF/MD/TXT 成功
      When 使用者 "alice@example.com" 在儀表板拖放上傳以下檔案：
        | 檔名               | 格式 | 大小    |
        | aws-notes.pdf      | PDF  | 2.5 MB  |
      Then 操作成功
      And 回應應包含上傳資源的 ID
      And 上傳狀態應為 "completed"

    @ignore
    Example: 檔案拖放上傳不支援格式失敗
      When 使用者 "alice@example.com" 在儀表板拖放上傳以下檔案：
        | 檔名             | 格式 | 大小    |
        | photo.exe        | EXE  | 1.0 MB  |
      Then 操作失敗，錯誤為「不支援的檔案格式，僅接受 PDF、MD、TXT」

  # ========== YouTube URL 解析 ==========

  @ignore
  Rule: 後置（狀態）- 儀表板快速上傳區支援 YouTube URL 解析提交

    @ignore
    Example: YouTube URL 解析提交成功
      When 使用者 "alice@example.com" 在儀表板提交 YouTube URL "https://www.youtube.com/watch?v=abc123"
      Then 操作成功
      And 回應應包含上傳資源的 ID
      And 資源類型應為 "youtube"

    @ignore
    Example: YouTube URL 解析提交無效 URL 失敗
      When 使用者 "alice@example.com" 在儀表板提交 YouTube URL "https://not-a-valid-url.com/xyz"
      Then 操作失敗，錯誤為「請輸入有效的 YouTube 影片網址」

  # ========== 圖片 Vision OCR 權限 ==========

  @ignore
  Rule: 前置（權限）- 上傳圖片 Vision OCR 功能需要 PRO_PLUS 以上方案

    @ignore
    Example: 上傳圖片 Vision OCR 非 PRO+ 顯示鎖定
      Given 使用者 "alice@example.com" 的訂閱方案為 "FREE"
      When 使用者 "alice@example.com" 嘗試上傳圖片進行 Vision OCR
      Then 操作失敗，錯誤為「Vision OCR 功能需升級至 PRO+ 方案」
      And 回應應包含升級方案的連結

  # ========== 上傳進度與重試 ==========

  @ignore
  Rule: 後置（回應）- 上傳過程應顯示進度指示器與正確狀態

    @ignore
    Example: 上傳進度指示器顯示正確狀態
      When 使用者 "alice@example.com" 在儀表板拖放上傳以下檔案：
        | 檔名               | 格式 | 大小    |
        | study-guide.pdf    | PDF  | 5.0 MB  |
      Then 操作成功
      And 回應應包含上傳進度狀態：
        | 欄位           | 說明                     |
        | progress       | 上傳百分比（0-100）      |
        | status         | uploading / completed    |

  @ignore
  Rule: 後置（狀態）- 上傳失敗後應提供重試功能

    @ignore
    Example: 上傳失敗後重試功能
      Given 使用者 "alice@example.com" 有一筆上傳失敗的資源，ID 為 "res-fail-001"
      When 使用者 "alice@example.com" 重試上傳資源 "res-fail-001"
      Then 操作成功
      And 上傳狀態應為 "completed"

  # ========== 雷達圖 ==========

  @ignore
  Rule: 後置（回應）- 雷達圖應顯示各領域的強度資料

    @ignore
    Example: 雷達圖顯示領域強度資料
      Given 使用者 "alice@example.com" 在 "AWS SAA" 科目有以下能力分布：
        | 領域               | 強度 |
        | 運算               | 80   |
        | 儲存               | 65   |
        | 網路               | 70   |
        | 資料庫             | 55   |
        | 安全性             | 90   |
      When 使用者 "alice@example.com" 查看儀表板，科目為 "AWS SAA"
      Then 操作成功
      And 回應中的雷達圖資料應包含：
        | 領域               | 強度 |
        | 運算               | 80   |
        | 儲存               | 65   |
        | 網路               | 70   |
        | 資料庫             | 55   |
        | 安全性             | 90   |

  # ========== 艾賓浩斯複習月曆 ==========

  @ignore
  Rule: 後置（回應）- 艾賓浩斯複習月曆應顯示正確的複習排程點

    @ignore
    Example: 艾賓浩斯複習月曆顯示正確複習點
      Given 使用者 "alice@example.com" 在 "AWS SAA" 科目有以下複習排程：
        | 日期       | 複習項目數 |
        | 2026-04-01 | 5          |
        | 2026-04-03 | 3          |
        | 2026-04-07 | 8          |
      When 使用者 "alice@example.com" 查看 "AWS SAA" 的複習月曆，月份為 "2026-04"
      Then 操作成功
      And 回應中的月曆複習點應包含：
        | 日期       | 複習項目數 |
        | 2026-04-01 | 5          |
        | 2026-04-03 | 3          |
        | 2026-04-07 | 8          |

  # ========== 新增科目 Modal ==========

  @ignore
  Rule: 後置（狀態）- 從儀表板新增備考科目

    @ignore
    Example: 新增科目 Modal 成功新增科目
      When 使用者 "alice@example.com" 從儀表板新增備考科目：
        | 科目     | 考試日期   |
        | CKA      | 2026-12-01 |
      Then 操作成功
      And 科目切換器應包含：
        | 科目    |
        | AWS SAA |
        | TOEIC   |
        | CKA     |

  # ========== 任務模式 Badge ==========

  @ignore
  Rule: 後置（回應）- 任務模式 Badge 點擊應顯示 tooltip 說明

    @ignore
    Example: 任務模式 Badge 點擊顯示 tooltip
      Given 使用者 "alice@example.com" 有一個類型為 "quiz" 的任務「完成一份 15 題測驗」，狀態為 "pending"
      When 使用者 "alice@example.com" 查看每日任務列表
      Then 操作成功
      And 每個任務應包含 badge 資訊：
        | 欄位         | 說明                       |
        | quest_type   | 任務類型標籤               |
        | tooltip      | 任務類型的詳細說明文字     |

  # ========== 帳戶頁面 - 大頭貼 ==========

  @ignore
  Rule: 後置（狀態）- 帳戶頁面更換大頭貼上傳

    @ignore
    Example: 帳戶頁面更換大頭貼上傳成功
      When 使用者 "alice@example.com" 在帳戶頁面上傳新大頭貼：
        | 檔名            | 格式 | 大小    |
        | avatar.jpg      | JPG  | 500 KB  |
      Then 操作成功
      And 回應應包含新頭像的 URL

  # ========== 帳戶頁面 - 訂閱管理 ==========

  @ignore
  Rule: 後置（狀態）- 帳戶頁面訂閱升級與取消

    @ignore
    Example: 帳戶頁面訂閱升級 Pro 成功
      When 使用者 "alice@example.com" 在帳戶頁面升級訂閱方案至 "PRO_199"
      Then 操作成功
      And 使用者 "alice@example.com" 的訂閱方案應為 "PRO_199"

    @ignore
    Example: 帳戶頁面取消訂閱成功
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email             | 訂閱方案  | Onboarding |
        | 3        | pro@example.com   | PRO_199   | true       |
      When 使用者 "pro@example.com" 在帳戶頁面取消訂閱
      Then 操作成功
      And 使用者 "pro@example.com" 的訂閱方案應於計費週期結束後降為 "FREE"

  # ========== 帳戶頁面 - 偏好設定 ==========

  @ignore
  Rule: 後置（狀態）- 帳戶頁面通知偏好與深色模式切換

    @ignore
    Example: 通知偏好設定切換
      When 使用者 "alice@example.com" 更新通知偏好設定：
        | 設定項目         | 值    |
        | email_notify     | false |
        | push_notify      | true  |
      Then 操作成功
      And 使用者 "alice@example.com" 的通知偏好應為：
        | 設定項目         | 值    |
        | email_notify     | false |
        | push_notify      | true  |

    @ignore
    Example: 深色模式切換
      When 使用者 "alice@example.com" 切換深色模式為 "enabled"
      Then 操作成功
      And 使用者 "alice@example.com" 的深色模式設定應為 "enabled"

  # ========== 帳戶頁面 - 刪除帳號 ==========

  @ignore
  Rule: 前置（參數）- 刪除帳號需輸入 DELETE 確認文字

    @ignore
    Example: 刪除帳號需輸入 DELETE 確認
      When 使用者 "alice@example.com" 提交刪除帳號請求，確認文字為 "DELETE"
      Then 操作成功
      And 使用者 "alice@example.com" 的帳號狀態應為 "deleted"

    @ignore
    Example: 刪除帳號確認文字錯誤被拒絕
      When 使用者 "alice@example.com" 提交刪除帳號請求，確認文字為 "delete"
      Then 操作失敗，錯誤為「請輸入大寫 DELETE 以確認刪除帳號」

  # ========== 帳戶頁面 - 科目管理 ==========

  @ignore
  Rule: 後置（狀態）- 帳戶頁面科目編輯與移除

    @ignore
    Example: 科目編輯導航至 onboarding
      When 使用者 "alice@example.com" 在帳戶頁面點擊編輯科目 "AWS SAA"
      Then 操作成功
      And 系統應導向至 Onboarding 科目編輯頁，帶入 "AWS SAA" 的現有設定

    @ignore
    Example: 科目移除成功
      When 使用者 "alice@example.com" 在帳戶頁面移除科目 "TOEIC"
      Then 操作成功
      And 使用者 "alice@example.com" 的備考科目應不包含 "TOEIC"
