Feature: 資源上傳與隱性版權約定

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | free@example.com   | FREE     |
      | 2        | pro@example.com    | PRO      |
      | 3        | proplus@example.com| PRO_PLUS |
      | 4        | ultra@example.com  | ULTRA    |

  # ========== 前置條件 ==========

  Rule: 前置（參數）- 上傳檔案類型必須在允許清單內

    Scenario Outline: 上傳不支援的檔案類型失敗
      When 使用者 "pro@example.com" 上傳檔案 "document.<副檔名>"
      Then 操作失敗
      And 錯誤訊息應為 "不支援的檔案格式，請上傳 PDF、Markdown 或通用圖片檔案"

      Examples:
        | 副檔名 |
        | docx   |
        | mp4    |

  Rule: 前置（隱性防護）- 點擊上傳按鈕即代表締結免責與無機密資訊同意契約

    Example: 使用者直接上傳檔案並由後端自動寫入同意紀錄 (免打勾)
      When 使用者 "free@example.com" 點擊上傳按鈕上傳檔案 "document.pdf"
      Then 操作成功
      And 系統日誌應自動對該資源附加 "隱性同意防護條款" 欄位標記為 true
      And 上傳按鈕下方必須有小字「上傳代表您已同意我們的版權及免責約定」

  Rule: 前置（參數）- 講義檔案大小不得超過訂閱方案的限制長度

    Example: FREE 方案上傳超過 10MB 的檔案失敗
      When 使用者 "free@example.com" 上傳大小為 12MB 的 PDF 檔案
      Then 操作失敗
      And 錯誤訊息應為 "檔案大小超過 FREE 方案限制（10MB）"

    Example: PRO 方案與 PRO_PLUS 方案支援最高 100MB 的重度檔案上傳
      When 使用者 "pro@example.com" 上傳大小為 95MB 的超級講義 PDF 檔案
      Then 操作成功
      When 使用者 "proplus@example.com" 上傳大小為 95MB 的 PDF 檔案
      Then 操作成功

    Example: ULTRA 方案支援零限制的無上限傳輸
      When 使用者 "ultra@example.com" 上傳大小為 300MB 的教科書圖檔打包 PDF
      Then 操作成功

  Rule: 前置（模型呼叫守門員）- 解題影像檔案 (Vision OCR) 只有 PRO_PLUS 才能觸發多模態辨識

    Example: PRO 用戶上傳數學手寫圖片失敗並提示升級
      When 使用者 "pro@example.com" 嘗試上傳大小為 3MB 的影像檔案 "工數手寫筆記.png"
      Then 操作失敗
      And 提示訊息應為 "手寫微積分與工程圖片辨識 (Vision OCR) 需要多模態算力，請升級至 PRO_PLUS 方案"

    Example: PRO PLUS 上傳微積分圖片成功並啟動 Vision 神經網路
      When 使用者 "proplus@example.com" 上傳帶有方程式的影像檔案 "手寫推導.png"
      Then 操作成功
      And 新建立的資源狀態應為 "PENDING"
      And 預定使用的解析引擎自動切換為 "Vision OCR (KaTeX Support)"

  Rule: 前置（無限槓桿）- YouTube URL 各方案皆可支援，最高放寬為無時長限制

    Example: PRO 用戶提交 10 小時 bootcamp 的 YouTube URL 成功出題
      When 使用者 "pro@example.com" 提交 YouTube URL "https://www.youtube.com/watch?v=10hour_course"
      Then 操作成功
      And 系統應建立狀態為 "PENDING" 的解析任務
      And 交由高速、低耗能的 Gemini Flash 處理影片逐字稿，化解伺服器壓力
