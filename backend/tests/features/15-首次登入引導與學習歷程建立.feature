@backend
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

  Rule: 後置（狀態）- Step 1 顯示歡迎畫面並收集基本個人資訊

    Example: 進入引導頁時顯示歡迎動畫與個人資訊表單
      Given 使用者 "newbie@example.com" 進入首次登入引導頁
      Then 畫面應顯示歡迎動畫
      And 畫面應顯示以下輸入欄位：
        | 欄位         | 類型       | 是否必填 | 預設值                         |
        | 顯示名稱     | 文字輸入   | 否       | Email 前綴 "newbie"             |
        | 年齡         | 數字選擇   | 否       | 空                             |
        | 最高學歷     | 下拉選單   | 否       | 空                             |
        | 職業 / 領域  | 文字輸入   | 否       | 空                             |
      And 年齡選擇範圍應為 15 至 70 歲
      And 最高學歷選項應包含：
        | 選項         |
        | 國中         |
        | 高中 / 高職  |
        | 專科         |
        | 大學         |
        | 碩士         |
        | 博士         |
        | 其他         |
      And 畫面應顯示提示文字「填寫個人資訊有助於 AI 教練提供更適合您的學習建議」
      And 使用者可填寫資訊或直接跳過進入下一步

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

  Rule: 後置（狀態）- 完成 Onboarding 後可在帳號設定頁編輯個人資料與學習偏好

    Example: 使用者在帳號設定頁可查看並編輯 Onboarding 填寫的個人資訊
      Given 使用者 "alice@example.com" 已完成 Onboarding
      When 使用者進入帳號設定頁的「個人資料」分頁
      Then 畫面應顯示以下可編輯欄位：
        | 欄位             | 類型       | 說明                                 |
        | 姓名             | 文字輸入   | 即 Onboarding 的「顯示名稱」           |
        | 年齡             | 下拉選單   | 選填，範圍 15–70 歲                   |
        | 最高學歷         | 下拉選單   | 選填，選項同 Onboarding Step 1        |
        | 職業 / 領域      | 文字輸入   | 選填                                 |
        | 每日學習時間     | 按鈕選擇   | 15 分鐘 / 30 分鐘 / 1 小時 / 2 小時   |
        | 偏好學習方式     | 卡片選擇   | 大量刷題 / 觀念優先 / 混合模式         |
      And 各欄位應預填使用者目前的設定值

    Example: 使用者修改個人資料與學習偏好後儲存成功
      Given 使用者 "alice@example.com" 在帳號設定頁的「個人資料」分頁
      When 使用者修改以下欄位並點擊「儲存變更」：
        | 欄位             | 新值         |
        | 最高學歷         | 碩士         |
        | 職業 / 領域      | 軟體工程師    |
        | 每日學習時間     | 60 分鐘      |
        | 偏好學習方式     | 大量刷題      |
      Then 操作成功
      And 系統應更新使用者的個人資料與學習偏好
      And 畫面應顯示「已儲存」提示

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

  # ========== Step 2：自訂科目 ==========

  Rule: 後置（狀態）- Step 2 支援自訂科目輸入

    Example: 使用者輸入自訂科目名稱新增成功
      Given 使用者 "newbie@example.com" 進入 Step 2 選擇備考科目
      When 使用者在自訂科目輸入欄輸入 "CISSP" 並點擊新增
      Then 已選科目列表應包含 "CISSP"
      And 該科目應標記為「自訂科目」

    Example: 自訂科目名稱與既有科目重複時被拒絕
      Given 使用者 "newbie@example.com" 進入 Step 2 選擇備考科目
      And 使用者已選擇 "AWS SAA"
      When 使用者在自訂科目輸入欄輸入 "AWS SAA" 並點擊新增
      Then 操作失敗
      And 錯誤訊息應為 "此科目已存在，請勿重複新增"

  # ========== Step 2：已選科目考試日期 Badge ==========

  Rule: 後置（回應）- 已選科目卡片應顯示考試日期模式 Badge

    Example: 已選科目卡片設定考試日期後顯示模式 Badge
      Given 使用者 "newbie@example.com" 進入 Step 2 選擇備考科目
      When 使用者選擇以下備考科目並設定：
        | 科目         | 預計考試日期 | 自評程度   |
        | AWS SAA      | 2026-06-15  | 有基礎     |
      Then 已選科目 "AWS SAA" 的卡片應顯示考試日期 Badge "2026-06-15"

  # ========== Step 2：自我評估切換 ==========

  Rule: 後置（狀態）- 已選科目支援自我評估程度切換

    Example: 使用者切換已選科目的自我評估程度
      Given 使用者 "newbie@example.com" 進入 Step 2 選擇備考科目
      And 使用者已選擇 "AWS SAA" 並設定自評程度為 "初學者"
      When 使用者將 "AWS SAA" 的自評程度切換為 "有基礎"
      Then "AWS SAA" 的自評程度應更新為 "有基礎"

    Example: 使用者切換已選科目的自我評估為進階
      Given 使用者 "newbie@example.com" 進入 Step 2 選擇備考科目
      And 使用者已選擇 "AWS SAA" 並設定自評程度為 "有基礎"
      When 使用者將 "AWS SAA" 的自評程度切換為 "進階"
      Then "AWS SAA" 的自評程度應更新為 "進階"

  # ========== Step 3：自訂每日學習時間驗證 ==========

  Rule: 前置（參數）- 自訂每日學習時間必須介於 5 至 480 分鐘

    Example: 自訂每日學習時間低於 5 分鐘被拒絕
      Given 使用者 "newbie@example.com" 進入 Step 3 學習偏好設定
      When 使用者選擇「自訂」並輸入每日學習時間為 3 分鐘
      Then 操作失敗
      And 錯誤訊息應為 "每日學習時間需介於 5 至 480 分鐘"

    Example: 自訂每日學習時間超過 480 分鐘被拒絕
      Given 使用者 "newbie@example.com" 進入 Step 3 學習偏好設定
      When 使用者選擇「自訂」並輸入每日學習時間為 500 分鐘
      Then 操作失敗
      And 錯誤訊息應為 "每日學習時間需介於 5 至 480 分鐘"

    Example: 自訂每日學習時間為有效值設定成功
      Given 使用者 "newbie@example.com" 進入 Step 3 學習偏好設定
      When 使用者選擇「自訂」並輸入每日學習時間為 120 分鐘
      Then 每日學習時間應設定為 120 分鐘

  # ========== Step 4：確認頁編輯返回 ==========

  Rule: 後置（狀態）- Step 4 確認頁可透過編輯按鈕返回各步驟修改

    Example: 確認頁點擊編輯個人資訊返回 Step 1
      Given 使用者 "newbie@example.com" 在 Step 4 確認頁
      When 使用者點擊個人資訊區塊的「編輯」按鈕
      Then 系統應導向至 Step 1 歡迎與基本資訊頁
      And 先前填寫的資料應保留不變

    Example: 確認頁點擊編輯備考科目返回 Step 2
      Given 使用者 "newbie@example.com" 在 Step 4 確認頁
      When 使用者點擊備考科目區塊的「編輯」按鈕
      Then 系統應導向至 Step 2 選擇備考科目頁
      And 先前選擇的科目與設定應保留不變

    Example: 確認頁點擊編輯學習偏好返回 Step 3
      Given 使用者 "newbie@example.com" 在 Step 4 確認頁
      When 使用者點擊學習偏好區塊的「編輯」按鈕
      Then 系統應導向至 Step 3 學習偏好設定頁
      And 先前設定的偏好應保留不變

  # ========== Step 2：類別篩選標籤切換 ==========

  Rule: 後置（狀態）- Step 2 類別篩選標籤可切換並更新科目清單

    Example: 切換類別篩選標籤顯示對應科目
      Given 使用者 "newbie@example.com" 進入 Step 2 選擇備考科目
      And 目前選擇的分類為 "IT"
      When 使用者切換分類標籤至 "金融"
      Then 畫面應顯示該分類下的科目清單，包含 "CFA Level 1"、"FRM"、"證券分析師"
      And 畫面不應顯示 "IT" 分類的科目

    Example: 點擊全部分類標籤顯示所有科目
      Given 使用者 "newbie@example.com" 進入 Step 2 選擇備考科目
      And 目前選擇的分類為 "IT"
      When 使用者切換分類標籤至 "全部"
      Then 畫面應顯示所有分類的科目清單

  # ========== 備考科目 CRUD（引導後管理）==========

  Rule: 命令（新增）- 已完成引導的使用者可新增備考科目

    Example: 新增備考科目到學習歷程
      When 使用者 "alice@example.com" 新增備考科目：
        | 欄位                | 值              |
        | subject_name        | JLPT N1         |
        | exam_date           | 2026-07-01      |
        | self_assessed_level | beginner        |
      Then 操作應成功
      And 使用者 "alice@example.com" 的學習歷程應包含 "JLPT N1"

  Rule: 前置（狀態）- 不可重複新增已在備考的科目

    Example: 重複新增已在備考的科目應回傳衝突錯誤
      Given 使用者 "alice@example.com" 有學習歷程於科目 "AWS SAA"
      When 使用者新增備考科目 "AWS SAA"，設定考試日期為 "2026-08-01"，自評程度為 "intermediate"
      Then 操作失敗
      And 錯誤訊息應為 "已在備考 AWS SAA，無需重複新增"

    Example: 重新新增已封存的科目應自動啟用
      Given 使用者 "alice@example.com" 有已封存的學習歷程於科目 "CFA Level 1"
      When 使用者新增備考科目 "CFA Level 1"，設定考試日期為 "2026-09-01"，自評程度為 "beginner"
      Then 操作應成功
      And 使用者 "alice@example.com" 的學習歷程 "CFA Level 1" 應為活躍狀態

  Rule: 查詢（過濾）- 可選科目清單應排除已備考科目與傘狀父科目

    Example: 可選科目清單不包含已備考的科目
      Given 使用者 "alice@example.com" 有學習歷程於科目 "AWS SAA"
      When 使用者 "alice@example.com" 查詢可選科目清單
      Then 操作應成功
      And 可選科目清單不應包含 "AWS SAA"

    Example: 可選科目清單不包含有子級的傘狀父科目
      Given 系統中有科目 "AI 應用規劃師" 及其子科目 "AI 應用規劃師（初級）"
      When 使用者 "alice@example.com" 查詢可選科目清單
      Then 操作應成功
      And 可選科目清單不應包含 "AI 應用規劃師"
      And 可選科目清單應包含 "AI 應用規劃師（初級）"

  Rule: 命令（移除）- 使用者可移除備考科目（封存而非刪除）

    Example: 移除備考科目後學習歷程被封存
      Given 使用者 "alice@example.com" 有學習歷程於科目 "AWS SAA"
      When 使用者 "alice@example.com" 移除備考科目 "AWS SAA" 並確認
      Then 操作應成功
      And 科目 "AWS SAA" 的學習歷程 is_archived 應為 true
      And 使用者 "alice@example.com" 的活躍學習歷程不應包含 "AWS SAA"

  Rule: 查詢 - 使用者可查詢自己的備考科目清單

    Example: 查詢備考科目清單
      Given 使用者 "alice@example.com" 有學習歷程於科目 "AWS SAA"
      When 使用者 "alice@example.com" 查詢備考科目清單
      Then 操作應成功
      And API 回應應包含科目 "AWS SAA" 及其考試日期和自評程度

  Rule: 查詢 - 可用科目清單應正確區分同一證照的初級/中級

    Example: AI 應用規劃師應分為初級與中級兩個獨立科目
      Given 系統中有科目 "AI 應用規劃師（初級）" 屬於分類 "IT"
      And 系統中有科目 "AI 應用規劃師（中級）" 屬於分類 "IT"
      When 使用者 "alice@example.com" 查詢可選科目清單
      Then 操作應成功
      And "IT" 分類下應包含 "AI 應用規劃師（初級）"
      And "IT" 分類下應包含 "AI 應用規劃師（中級）"
      And "AI 應用規劃師（初級）" 的考古題數量應大於 0
      And "AI 應用規劃師（中級）" 的考古題數量應大於 0

  # ─────────────────────────────────────────────
  # PRD-033：自訂考科必須嚴格隔離到建立者
  # ─────────────────────────────────────────────
  @prd-033 @wip
  Rule: 自訂備考科目 owner_user_id 與 scope 正確設置

    Example: 建立自訂考科時寫入 owner_user_id 並標記 scope=personal
      Given 使用者 "u1@example.com" 已完成引導
      When 使用者透過 SubjectPickerModal 建立自訂考科 "我的化學複習"
      Then 新 subject 的 owner_user_id 應為 u1 的 UUID
      And 新 subject 的 scope 應為 "personal"

    Example: 其他使用者看不到別人的自訂考科
      Given 使用者 "u1@example.com" 已建立自訂考科 "我的化學複習"
      When 使用者 "u2@example.com" 呼叫 GET /api/v1/subjects/available
      Then 回應清單不應包含 "我的化學複習"
      And 回應清單只應包含 scope=platform AND owner_user_id IS NULL 的科目

    Example: 使用者可於帳號設定檢視並刪除自己的自訂考科
      Given 使用者 "u1@example.com" 已建立 2 個自訂考科
      When 呼叫 GET /api/v1/subjects/mine
      Then 應回應 2 筆 subjects（皆為 u1 擁有）
      When 呼叫 DELETE /api/v1/subjects/{subject_id}
      Then 操作成功
