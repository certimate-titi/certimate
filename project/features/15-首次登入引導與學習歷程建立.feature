Feature: 首次登入引導與學習歷程建立 (Onboarding)

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 | 已完成 Onboarding |
      | 1        | alice@example.com  | FREE     | 是                |
      | 2        | newbie@example.com | FREE     | 否                |
    And 系統中有以下證照科目分類：
      | 分類   | 科目範例                          |
      | IT     | AWS SAA、Azure AZ-900、CCNA       |
      | 金融   | CFA Level 1、FRM、證券分析師        |
      | 語言   | TOEIC、JLPT N1、IELTS             |
      | 醫療   | 護理師、藥師、醫檢師               |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 僅未完成 Onboarding 的使用者會被導向引導頁

    Example: 未完成 Onboarding 的新用戶登入後自動導向引導頁
      Given 使用者 "newbie@example.com" 尚未完成 Onboarding
      When 使用者 "newbie@example.com" 成功登入系統
      Then 系統應導向至 "首次登入引導頁"

    Example: 已完成 Onboarding 的使用者登入後直接導向儀表板
      Given 使用者 "alice@example.com" 已完成 Onboarding
      When 使用者 "alice@example.com" 成功登入系統
      Then 系統應導向至 "個人儀表板首頁"

  Rule: 前置（參數）- 至少須選擇一個備考科目才能完成引導

    Example: 未選擇任何科目時無法完成 Onboarding
      Given 使用者 "newbie@example.com" 正在進行 Onboarding 流程
      When 使用者未選擇任何備考科目並嘗試進入下一步
      Then 操作失敗
      And 錯誤訊息應為 "請至少選擇一個備考科目"

  # ========== Step 1：歡迎與基本資訊 ==========

  Rule: 後置（狀態）- Step 1 顯示歡迎畫面並可填寫顯示名稱

    Example: 進入引導頁時顯示歡迎動畫與名稱填寫
      Given 使用者 "newbie@example.com" 進入首次登入引導頁
      Then 畫面應顯示歡迎動畫
      And 畫面應顯示「顯示名稱」輸入欄位，預設值為 Email 前綴 "newbie"
      And 使用者可修改顯示名稱或直接跳過進入下一步

  # ========== Step 2：選擇備考科目 ==========

  Rule: 後置（狀態）- Step 2 支援瀏覽分類與搜尋科目

    Example: 使用者可透過分類瀏覽找到備考科目
      Given 使用者 "newbie@example.com" 進入 Step 2 選擇備考科目
      When 使用者選擇分類 "IT"
      Then 畫面應顯示該分類下的科目清單，包含 "AWS SAA"、"Azure AZ-900"、"CCNA"

    Example: 使用者可透過關鍵字搜尋找到備考科目
      Given 使用者 "newbie@example.com" 進入 Step 2 選擇備考科目
      When 使用者在搜尋欄輸入 "AWS"
      Then 搜尋結果應包含 "AWS SAA"

  Rule: 後置（狀態）- Step 2 支援同時選擇多個備考科目並個別設定

    Example: 使用者選擇多個備考科目並分別設定考試日期與程度
      Given 使用者 "newbie@example.com" 進入 Step 2 選擇備考科目
      When 使用者選擇以下備考科目並設定：
        | 科目         | 預計考試日期 | 自評程度   |
        | AWS SAA      | 2026-06-15  | 有基礎     |
        | CFA Level 1  | 2026-08-20  | 初學       |
      Then 已選科目列表應顯示 2 個科目及其設定
      And 每個科目旁應顯示可移除的按鈕

    Example: 使用者可移除已選擇的備考科目
      Given 使用者 "newbie@example.com" 已選擇 "AWS SAA" 和 "CFA Level 1"
      When 使用者移除 "CFA Level 1"
      Then 已選科目列表應僅顯示 "AWS SAA"

  # ========== Step 3：學習偏好設定 ==========

  Rule: 後置（狀態）- Step 3 設定每日學習時間與偏好方式

    Example: 使用者設定學習偏好
      Given 使用者 "newbie@example.com" 進入 Step 3 學習偏好設定
      When 使用者設定以下偏好：
        | 欄位             | 值           |
        | 每日學習時間     | 30 分鐘      |
        | 偏好學習方式     | 觀念理解優先  |
      Then 系統應暫存使用者的學習偏好設定

    Example: 使用者可選擇自訂每日學習時間
      Given 使用者 "newbie@example.com" 進入 Step 3 學習偏好設定
      When 使用者選擇「自訂」並輸入每日學習時間為 45 分鐘
      Then 每日學習時間應設定為 45 分鐘

  # ========== Step 4：確認與啟動 ==========

  Rule: 後置（狀態）- Step 4 摘要預覽並確認啟動學習計畫

    Example: 確認頁正確顯示所有設定摘要
      Given 使用者 "newbie@example.com" 已完成 Step 1 至 Step 3 的設定：
        | 顯示名稱 | 備考科目               | 每日學習時間 | 偏好學習方式   |
        | 小新     | AWS SAA, CFA Level 1   | 30 分鐘     | 觀念理解優先    |
      When 使用者進入 Step 4 確認頁
      Then 畫面應顯示完整的設定摘要
      And 各科目的考試日期與自評程度均應正確顯示
      And 畫面應顯示「開始我的學習旅程」按鈕

    Example: 點擊確認後系統初始化學習計畫並導向儀表板
      Given 使用者 "newbie@example.com" 在 Step 4 確認頁
      When 使用者點擊「開始我的學習旅程」
      Then 操作成功
      And 系統應為每個備考科目各建立一份獨立的學習歷程
      And 使用者的 Onboarding 狀態應標記為「已完成」
      And 系統應導向至 "個人儀表板首頁"

  # ========== 後續管理 ==========

  Rule: 後置（狀態）- 完成 Onboarding 後可隨時新增或管理備考科目

    Example: 使用者在儀表板新增備考科目
      Given 使用者 "alice@example.com" 已完成 Onboarding 且目前有 1 個備考科目
      When 使用者在個人儀表板點擊「+ 新增備考科目」
      Then 系統應開啟科目選擇介面
      And 使用者可選擇新科目並設定考試日期與自評程度

    Example: 新增科目後系統獨立建立學習歷程
      Given 使用者 "alice@example.com" 目前備考 "AWS SAA"
      When 使用者新增備考科目 "TOEIC"，設定考試日期為 "2026-09-01"，自評程度為 "有基礎"
      Then 操作成功
      And 系統應建立 "TOEIC" 的獨立學習歷程
      And 儀表板科目切換器應新增 "TOEIC" 選項
      And 原有 "AWS SAA" 的學習歷程不受影響

    Example: 使用者可移除不再備考的科目
      Given 使用者 "alice@example.com" 目前備考 "AWS SAA" 和 "TOEIC"
      When 使用者在會員中心移除備考科目 "TOEIC"
      Then 系統應提示確認 "移除後該科目的學習紀錄將被封存，確定要移除嗎？"
      When 使用者確認移除
      Then 操作成功
      And "TOEIC" 的學習歷程應被封存（非刪除）
      And 儀表板科目切換器不再顯示 "TOEIC"
