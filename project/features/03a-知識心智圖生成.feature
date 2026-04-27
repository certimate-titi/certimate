Feature: 知識心智圖生成

  資源上傳處理成功後，系統自動從原文萃取知識節點樹。

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | free@example.com   | FREE     |
      | 2        | pro@example.com     | PRO_199      |
      | 3        | proplus@example.com | PRO_PLUS_399 |
    And 系統中預設存在 "PMP" 與 "AWS SAA" 兩個學科庫

  # ========== 自動生成流程 ==========

  Rule: 前置（觸發）- 資源處理成功後自動觸發心智圖生成

    Example: PDF 資源解析完成後系統自動生成知識節點樹
      Given 使用者 "pro@example.com" 已上傳 PDF 資源 "AWS_SAA_教材.pdf" 且狀態為 "PROCESSING"
      When 系統完成資源解析
      Then 資源狀態應更新為 "COMPLETED"
      And 系統應自動為該資源建立知識節點樹
      And 儀表板應顯示 Toast 通知「解析完成！心智圖已生成，立即查看」

    Example: YouTube 影片逐字稿解析後自動生成知識節點樹
      Given 使用者 "pro@example.com" 已提交 YouTube URL 且狀態為 "PROCESSING"
      When 系統完成影片逐字稿解析
      Then 資源狀態應更新為 "COMPLETED"
      And 系統應自動為該影片建立知識節點樹（含時間軸標記）

  Rule: 後置（結構）- 生成的知識節點樹應具備層級結構與溯源定位

    Example: 節點樹包含章節層級與原文溯源
      Given 系統已完成 "AWS_SAA_教材.pdf" 的心智圖生成
      Then 知識節點樹應包含至少兩層結構（主題 → 子概念）
      And 每個葉節點應關聯原文溯源位置（PDF 頁碼或 YouTube 時間戳）

  Rule: 後置（失敗處理）- 心智圖生成失敗時資源狀態應反映錯誤

    Example: 原文內容過少導致無法萃取有意義的知識節點
      Given 使用者 "free@example.com" 上傳了僅含 2 行文字的 PDF
      When 系統嘗試生成心智圖
      Then 資源狀態應更新為 "COMPLETED_NO_MAP"
      And 提示訊息應為「內容不足以生成心智圖，但您仍可使用此資源出題」
